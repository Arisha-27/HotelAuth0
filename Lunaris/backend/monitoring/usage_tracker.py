"""
Step 64: API Usage Tracking
Tracks all API calls with detailed metrics for each service, endpoint, and hotel.
"""
import time, logging
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict
from pydantic import BaseModel, Field

logger = logging.getLogger("lunaris.monitoring.usage")

class APIUsageRecord(BaseModel):
    service: str
    operation: str
    hotel_id: str = "HQ"
    caller: str = "system"
    status_code: int = 200
    latency_ms: float = 0.0
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    timestamp: str = ""
    metadata: dict = Field(default_factory=dict)

class UsageTracker:
    """Tracks API usage metrics per service, operation, hotel, and time window."""
    def __init__(self):
        self._records: list[dict] = []
        self._counters: dict[str, int] = defaultdict(int)
        self._rate_windows: dict[str, list[float]] = defaultdict(list)
        self.rate_limit_per_minute: int = 100

    def record(self, rec: APIUsageRecord):
        rec.timestamp = rec.timestamp or datetime.now(timezone.utc).isoformat()
        self._records.append(rec.model_dump())
        self._counters[f"{rec.service}:{rec.operation}"] += 1
        self._counters[f"hotel:{rec.hotel_id}"] += 1
        self._counters["total"] += 1
        key = f"rate:{rec.service}"
        now = time.time()
        self._rate_windows[key].append(now)
        self._rate_windows[key] = [t for t in self._rate_windows[key] if now - t < 60]
        if len(self._records) > 5000:
            self._records = self._records[-2500:]

    def check_rate_limit(self, service: str) -> dict:
        key = f"rate:{service}"
        now = time.time()
        self._rate_windows[key] = [t for t in self._rate_windows[key] if now - t < 60]
        current = len(self._rate_windows[key])
        return {"service": service, "requests_last_minute": current, "limit": self.rate_limit_per_minute, "allowed": current < self.rate_limit_per_minute}

    def get_summary(self) -> dict:
        total = self._counters.get("total", 0)
        by_service = {}
        for k, v in self._counters.items():
            if ":" in k and not k.startswith("hotel:") and not k.startswith("rate:"):
                svc = k.split(":")[0]
                by_service.setdefault(svc, {"total": 0, "operations": {}})
                by_service[svc]["total"] += v
                by_service[svc]["operations"][k.split(":")[1]] = v
        by_hotel = {k.split(":")[1]: v for k, v in self._counters.items() if k.startswith("hotel:")}
        errors = sum(1 for r in self._records if r.get("status_code", 200) >= 400)
        return {"total_requests": total, "error_count": errors, "error_rate": round(errors / total * 100, 2) if total else 0, "by_service": by_service, "by_hotel": by_hotel}

    def get_recent(self, service: str = None, hotel_id: str = None, limit: int = 50) -> list[dict]:
        recs = self._records.copy()
        if service:
            recs = [r for r in recs if r["service"] == service]
        if hotel_id:
            recs = [r for r in recs if r["hotel_id"] == hotel_id]
        return recs[-limit:]

usage_tracker = UsageTracker()
