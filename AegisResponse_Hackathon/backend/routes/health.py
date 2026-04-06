"""
Health and metrics API endpoints.
Combines Phase 3 system metrics with Phase 5 integration health.
"""

import time
import psutil
from fastapi import APIRouter
from typing import Dict, Any

from backend.auth.token_vault import get_cached_tokens_info

router = APIRouter()
START_TIME = time.time()


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check including all Phase 3 + Phase 5 services."""
    uptime_seconds = time.time() - START_TIME

    # Phase 5 service health
    from backend.integrations.gmail_service import gmail_service
    from backend.integrations.notion_service import notion_service
    from backend.integrations.twilio_service import twilio_service
    from backend.integrations.iot_service import iot_simulator
    from backend.database.hotel_db import hotel_db
    from backend.gateway.cache import cache

    return {
        "status": "healthy",
        "uptime": f"{uptime_seconds:.2f}s",
        "version": "5.0.0",
        "phase": "Phase 3+5 — Core + External Integrations",
        "timestamp": time.time(),
        "services": {
            "database": {"status": "up", "hotels": len(hotel_db.get_hotels())},
            "iot_simulator": {"status": "up", "devices": len(iot_simulator.devices)},
            "gmail": {"configured": gmail_service.is_configured, "mode": "live" if gmail_service.is_configured else "mock"},
            "notion": {"configured": notion_service.is_configured, "mode": "live" if notion_service.is_configured else "mock"},
            "twilio": {"configured": twilio_service.is_configured, "mode": "live" if twilio_service.is_configured else "mock"},
            "cache": cache.get_stats(),
        },
    }


@router.get("/metrics", response_model=Dict[str, Any])
async def metrics() -> Dict[str, Any]:
    """System metrics, token vault status, and Phase 5 monitoring data."""
    process = psutil.Process()
    memory_info = process.memory_info()

    from backend.monitoring.usage_tracker import usage_tracker
    from backend.monitoring.cost_monitor import cost_monitor
    from backend.gateway.cache import cache

    return {
        "system": {
            "uptime_seconds": time.time() - START_TIME,
            "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
            "cpu_percent": psutil.cpu_percent(),
        },
        "auth": {
            "token_vault": get_cached_tokens_info()
        },
        "integrations": {
            "usage": usage_tracker.get_summary(),
            "costs": cost_monitor.get_summary(),
            "cache": cache.get_stats(),
        },
    }
