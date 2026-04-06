"""
Step 65: Cost Monitoring Module
Tracks estimated costs for API calls, agent invocations, and external services.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("ahos.monitoring.cost")

# Cost per call estimates (USD)
SERVICE_COSTS = {
    "gmail": {"send_alert": 0.0001},
    "notion": {"create_log": 0.0002, "query_logs": 0.0001},
    "twilio": {"send_alert": 0.0075, "send_approval": 0.0075},
    "iot": {"execute_command": 0.0, "unlock_floor": 0.0, "fire_protocol": 0.0},
    "claude": {"intent_parse": 0.003, "task_plan": 0.008, "reasoning": 0.005},
    "auth0": {"get_token": 0.0, "validate_token": 0.0},
    "database": {"read": 0.0, "write": 0.0001},
}

BUDGET_ALERTS = {
    "warning": 50.0,   # $50 warning
    "critical": 100.0,  # $100 critical
    "limit": 200.0,     # $200 hard limit
}

class CostEntry(BaseModel):
    service: str
    operation: str
    cost_usd: float
    hotel_id: str = "HQ"
    caller: str = "system"
    timestamp: str = ""

class CostMonitor:
    """Tracks and monitors costs across all services."""
    def __init__(self):
        self._entries: list[dict] = []
        self._totals: dict[str, float] = {}
        self._budget_alerts_fired: set[str] = set()

    def record_cost(self, service: str, operation: str, hotel_id: str = "HQ", caller: str = "system", multiplier: float = 1.0):
        cost = SERVICE_COSTS.get(service, {}).get(operation, 0.0) * multiplier
        entry = CostEntry(service=service, operation=operation, cost_usd=cost, hotel_id=hotel_id, caller=caller, timestamp=datetime.now(timezone.utc).isoformat())
        self._entries.append(entry.model_dump())
        self._totals[service] = self._totals.get(service, 0.0) + cost
        self._totals["grand_total"] = self._totals.get("grand_total", 0.0) + cost
        self._check_budget()
        if len(self._entries) > 5000:
            self._entries = self._entries[-2500:]

    def _check_budget(self):
        total = self._totals.get("grand_total", 0.0)
        for level, threshold in BUDGET_ALERTS.items():
            if total >= threshold and level not in self._budget_alerts_fired:
                self._budget_alerts_fired.add(level)
                logger.warning(f"💰 BUDGET ALERT [{level.upper()}]: Total cost ${total:.2f} exceeds ${threshold:.2f}")

    def get_summary(self) -> dict:
        gt = self._totals.get("grand_total", 0.0)
        by_svc = {k: round(v, 4) for k, v in self._totals.items() if k != "grand_total"}
        return {
            "grand_total_usd": round(gt, 4),
            "by_service": by_svc,
            "budget_status": "limit_reached" if gt >= BUDGET_ALERTS["limit"] else "critical" if gt >= BUDGET_ALERTS["critical"] else "warning" if gt >= BUDGET_ALERTS["warning"] else "normal",
            "budget_remaining_usd": round(max(0, BUDGET_ALERTS["limit"] - gt), 2),
            "total_entries": len(self._entries),
        }

    def get_hotel_costs(self, hotel_id: str) -> dict:
        entries = [e for e in self._entries if e["hotel_id"] == hotel_id]
        total = sum(e["cost_usd"] for e in entries)
        by_svc = {}
        for e in entries:
            by_svc[e["service"]] = by_svc.get(e["service"], 0.0) + e["cost_usd"]
        return {"hotel_id": hotel_id, "total_usd": round(total, 4), "by_service": {k: round(v, 4) for k, v in by_svc.items()}, "entry_count": len(entries)}

    def get_recent(self, limit: int = 50) -> list[dict]:
        return self._entries[-limit:]

cost_monitor = CostMonitor()
