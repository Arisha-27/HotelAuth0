"""
Step 62: API Gateway Abstraction Layer
Unified interface for all external service calls with retry, circuit breaking, and fallback.
"""
import asyncio, logging, time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("ahos.gateway")

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, name: str, threshold: int = 5, timeout: float = 30.0):
        self.name = name
        self.threshold = threshold
        self.timeout = timeout
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_fail: Optional[float] = None

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN and self.last_fail and (time.time() - self.last_fail) > self.timeout:
            self.state = CircuitState.HALF_OPEN
            return True
        return self.state == CircuitState.HALF_OPEN

    def record_success(self):
        self.state = CircuitState.CLOSED
        self.failures = 0

    def record_failure(self):
        self.failures += 1
        self.last_fail = time.time()
        if self.failures >= self.threshold:
            self.state = CircuitState.OPEN

class GatewayRequest(BaseModel):
    service: str
    operation: str
    payload: dict = Field(default_factory=dict)
    hotel_id: str = "HQ"
    priority: str = "normal"
    timeout: float = 30.0
    max_retries: int = 3
    caller: str = "system"

class GatewayResponse(BaseModel):
    success: bool
    service: str
    operation: str
    data: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0
    retries_used: int = 0
    circuit_state: str = "closed"
    timestamp: str = ""

class APIGateway:
    def __init__(self):
        self._services: dict[str, dict[str, Callable]] = {}
        self._cbs: dict[str, CircuitBreaker] = {}
        self._log: list[dict] = []
        self._stats: dict[str, dict] = {}

    def register_service(self, name: str, ops: dict[str, Callable]):
        self._services[name] = ops
        self._cbs[name] = CircuitBreaker(name)
        self._stats[name] = {"total": 0, "ok": 0, "fail": 0, "avg_ms": 0.0, "total_ms": 0.0}

    async def execute(self, req: GatewayRequest) -> GatewayResponse:
        start = time.time()
        if req.service not in self._services:
            return GatewayResponse(success=False, service=req.service, operation=req.operation, error=f"Unknown service: {req.service}", timestamp=datetime.now(timezone.utc).isoformat())
        ops = self._services[req.service]
        if req.operation not in ops:
            return GatewayResponse(success=False, service=req.service, operation=req.operation, error=f"Unknown op: {req.operation}", timestamp=datetime.now(timezone.utc).isoformat())
        cb = self._cbs[req.service]
        if not cb.can_execute():
            return GatewayResponse(success=False, service=req.service, operation=req.operation, error="Circuit OPEN", circuit_state=cb.state, timestamp=datetime.now(timezone.utc).isoformat())

        handler = ops[req.operation]
        last_err = None
        retries = 0
        for attempt in range(req.max_retries + 1):
            try:
                result = await asyncio.wait_for(handler(**req.payload), timeout=req.timeout)
                cb.record_success()
                ms = (time.time() - start) * 1000
                self._update_stats(req.service, True, ms)
                resp = GatewayResponse(success=True, service=req.service, operation=req.operation, data=result.model_dump() if hasattr(result, 'model_dump') else result, latency_ms=round(ms, 2), retries_used=retries, circuit_state=cb.state, timestamp=datetime.now(timezone.utc).isoformat())
                self._log_req(req, resp)
                return resp
            except Exception as e:
                last_err = str(e)
                retries += 1
                if attempt < req.max_retries:
                    await asyncio.sleep(min(2 ** attempt * 0.5, 10.0))

        cb.record_failure()
        ms = (time.time() - start) * 1000
        self._update_stats(req.service, False, ms)
        resp = GatewayResponse(success=False, service=req.service, operation=req.operation, error=f"All attempts failed: {last_err}", latency_ms=round(ms, 2), retries_used=retries, circuit_state=cb.state, timestamp=datetime.now(timezone.utc).isoformat())
        self._log_req(req, resp)
        return resp

    def _update_stats(self, svc: str, ok: bool, ms: float):
        s = self._stats[svc]
        s["total"] += 1
        s["ok" if ok else "fail"] += 1
        s["total_ms"] += ms
        s["avg_ms"] = round(s["total_ms"] / s["total"], 2)

    def _log_req(self, req, resp):
        self._log.append({"service": req.service, "op": req.operation, "hotel": req.hotel_id, "ok": resp.success, "ms": resp.latency_ms, "ts": resp.timestamp})
        if len(self._log) > 1000:
            self._log = self._log[-500:]

    def get_health(self) -> dict:
        return {n: {"state": self._cbs[n].state, "ops": list(self._services[n].keys()), **self._stats[n]} for n in self._services}

    def get_log(self, svc: str = None, limit: int = 50) -> list[dict]:
        log = [r for r in self._log if not svc or r["service"] == svc]
        return log[-limit:]

    def reset_cb(self, svc: str) -> bool:
        if svc in self._cbs:
            self._cbs[svc].state = CircuitState.CLOSED
            self._cbs[svc].failures = 0
            return True
        return False

api_gateway = APIGateway()
