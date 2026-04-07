"""
Security Core APIs
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from backend.auth.rbac import require_scope, Scope
from backend.logging_config import get_logger

logger = get_logger("routes.security")
router = APIRouter(prefix="/security", tags=["Security"])


class UnlockRequest(BaseModel):
    target: str  # e.g., "floor_3", "room_101", "main_entrance"
    reason: str
    emergency_override: bool = False


class UnlockResponse(BaseModel):
    status: str
    target: str
    timestamp: str
    action_id: str


@router.post("/unlock", response_model=UnlockResponse)
async def unlock_doors(
    req: UnlockRequest,
    payload: dict = Depends(require_scope(Scope.UNLOCK_DOORS)),
) -> UnlockResponse:
    """Unlock specified doors. Requires unlock:doors scope."""
    agent_sub = payload.get("sub", "unknown_agent")
    
    logger.info(
        f"Unlock requested for {req.target} by {agent_sub}",
        extra={
            "extra_data": {
                "target": req.target,
                "reason": req.reason,
                "emergency": req.emergency_override,
                "agent": agent_sub,
            }
        },
    )

    # In a real system, we'd interact with IoT controllers here
    
    return UnlockResponse(
        status="success",
        target=req.target,
        timestamp=datetime.now(timezone.utc).isoformat(),
        action_id=f"act_sec_{int(datetime.now().timestamp())}",
    )
