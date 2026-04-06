"""
Health and metrics API endpoints.
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
    """Basic health check endpoint."""
    uptime_seconds = time.time() - START_TIME
    return {
        "status": "healthy",
        "uptime": f"{uptime_seconds:.2f}s",
        "version": "3.0.0",
        "timestamp": time.time(),
    }


@router.get("/metrics", response_model=Dict[str, Any])
async def metrics() -> Dict[str, Any]:
    """System metrics and token vault status."""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "system": {
            "uptime_seconds": time.time() - START_TIME,
            "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
            "cpu_percent": psutil.cpu_percent(),
        },
        "auth": {
            "token_vault": get_cached_tokens_info()
        }
    }
