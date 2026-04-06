"""
Operations Core APIs
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone

from backend.auth.rbac import require_scope, Scope
from backend.logging_config import get_logger

logger = get_logger("routes.operations")
router = APIRouter(prefix="/ops", tags=["Operations"])


class NotificationRequest(BaseModel):
    type: str  # "email", "sms", "in_app"
    recipients: List[str]
    subject: str
    message: str
    priority: str = "normal"  # "low", "normal", "high", "urgent"


class NotificationResponse(BaseModel):
    status: str
    dispatched_count: int
    timestamp: str


@router.post("/notify", response_model=NotificationResponse)
async def send_notification(
    req: NotificationRequest,
    payload: dict = Depends(require_scope(Scope.NOTIFY_GUESTS)),
) -> NotificationResponse:
    """Send notifications to guests or staff. Requires notify:guests scope."""
    agent_sub = payload.get("sub", "unknown_agent")

    logger.info(
        f"Notification requested by {agent_sub}",
        extra={
            "extra_data": {
                "type": req.type,
                "recipients_count": len(req.recipients),
                "priority": req.priority,
            }
        },
    )

    # In a real system, we'd queue these or send via Twilio/SendGrid
    
    return NotificationResponse(
        status="queued",
        dispatched_count=len(req.recipients),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
