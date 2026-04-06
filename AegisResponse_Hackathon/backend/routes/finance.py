"""
Finance Core APIs
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from backend.auth.rbac import require_scope, Scope
from backend.logging_config import get_logger

logger = get_logger("routes.finance")
router = APIRouter(prefix="/finance", tags=["Finance"])


class TransactionLogRequest(BaseModel):
    transaction_type: str  # "refund", "charge", "adjustment"
    amount: float
    currency: str = "USD"
    description: str
    booking_id: Optional[str] = None


class TransactionLogResponse(BaseModel):
    status: str
    transaction_id: str
    timestamp: str


@router.post("/log", response_model=TransactionLogResponse)
async def log_transaction(
    req: TransactionLogRequest,
    payload: dict = Depends(require_scope(Scope.READ_FINANCE)),
) -> TransactionLogResponse:
    """Log a financial transaction. Requires read:finance scope."""
    agent_sub = payload.get("sub", "unknown_agent")

    logger.info(
        f"Transaction logged by {agent_sub}",
        extra={
            "extra_data": {
                "type": req.transaction_type,
                "amount": req.amount,
                "currency": req.currency,
                "booking_id": req.booking_id,
            }
        },
    )

    # In a real system, write to finance DB ledger
    
    return TransactionLogResponse(
        status="logged",
        transaction_id=f"txn_{int(datetime.now().timestamp())}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
