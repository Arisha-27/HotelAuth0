"""
Step 58: Twilio SMS Integration for Critical Alerts
Sends SMS alerts for emergencies, approval requests, and guest notifications.
Supports real Twilio API and mock fallback.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger("ahos.integrations.twilio")


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class SMSRequest(BaseModel):
    """Schema for sending an SMS alert."""
    to: str = Field(..., description="Recipient phone number (E.164 format: +1234567890)")
    message: str = Field(..., description="SMS message body (max 1600 chars)")
    priority: str = Field(default="normal", description="Priority: low, normal, high, critical")
    hotel_id: str = Field(default="HQ", description="Originating hotel ID")
    alert_type: str = Field(default="general", description="Alert type for routing")
    requires_response: bool = Field(default=False, description="If true, awaits approval reply")


class SMSResult(BaseModel):
    """Result of sending an SMS."""
    success: bool
    sid: Optional[str] = None
    timestamp: str
    provider: str  # "twilio" or "mock"
    status: str = "queued"
    details: dict = Field(default_factory=dict)


class ApprovalSMS(BaseModel):
    """An approval request sent via SMS."""
    to: str
    action_description: str
    action_id: str
    hotel_id: str = "HQ"
    timeout_minutes: int = Field(default=5, ge=1, le=60)


# ─────────────────────────────────────────────
# SMS Formatting
# ─────────────────────────────────────────────
PRIORITY_PREFIX = {
    "low": "ℹ️",
    "normal": "📢",
    "high": "⚠️",
    "critical": "🚨🚨🚨",
}


def _format_alert_sms(req: SMSRequest) -> str:
    """Format an alert SMS with priority prefix and metadata."""
    prefix = PRIORITY_PREFIX.get(req.priority, "📢")
    lines = [
        f"{prefix} AEGIS HOSPITALITY OS",
        f"Hotel: {req.hotel_id}",
        f"Priority: {req.priority.upper()}",
        "",
        req.message,
        "",
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
    ]
    return "\n".join(lines)


def _format_approval_sms(req: ApprovalSMS) -> str:
    """Format an approval request SMS."""
    return (
        f"🔐 AEGIS APPROVAL REQUIRED\n"
        f"Hotel: {req.hotel_id}\n\n"
        f"Action: {req.action_description}\n"
        f"ID: {req.action_id}\n\n"
        f"Reply YES to approve, NO to deny.\n"
        f"Expires in {req.timeout_minutes} min."
    )


# ─────────────────────────────────────────────
# Twilio Service
# ─────────────────────────────────────────────
class TwilioService:
    """
    Twilio SMS integration for AHOS alerts and approval workflows.
    Falls back to mock in development.
    """

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "+15551234567")
        self._sent_log: list[dict] = []
        self._pending_approvals: dict[str, dict] = {}

    @property
    def is_configured(self) -> bool:
        return all([self.account_sid, self.auth_token])

    async def send_alert(self, request: SMSRequest) -> SMSResult:
        """Send an SMS alert."""
        if self.is_configured:
            return await self._send_via_twilio(request)
        return await self._send_mock(request)

    async def send_approval_request(self, request: ApprovalSMS) -> SMSResult:
        """Send an approval request via SMS and track it."""
        sms_req = SMSRequest(
            to=request.to,
            message=_format_approval_sms(request),
            priority="critical",
            hotel_id=request.hotel_id,
            alert_type="approval",
            requires_response=True,
        )
        result = await self.send_alert(sms_req)

        if result.success:
            self._pending_approvals[request.action_id] = {
                "action_id": request.action_id,
                "description": request.action_description,
                "hotel_id": request.hotel_id,
                "to": request.to,
                "sent_at": result.timestamp,
                "timeout_minutes": request.timeout_minutes,
                "status": "pending",
                "sms_sid": result.sid,
            }

        return result

    def process_approval_response(self, action_id: str, approved: bool) -> dict:
        """Process an approval response (called by webhook handler)."""
        if action_id not in self._pending_approvals:
            return {"error": "Unknown action_id", "action_id": action_id}

        approval = self._pending_approvals[action_id]
        approval["status"] = "approved" if approved else "denied"
        approval["responded_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Approval {'GRANTED' if approved else 'DENIED'} for action {action_id}")
        return approval

    async def _send_via_twilio(self, request: SMSRequest) -> SMSResult:
        """Send via real Twilio API."""
        try:
            formatted_msg = _format_alert_sms(request)
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    auth=(self.account_sid, self.auth_token),
                    data={
                        "From": self.from_number,
                        "To": request.to,
                        "Body": formatted_msg,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            result = SMSResult(
                success=True,
                sid=data.get("sid"),
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="twilio",
                status=data.get("status", "queued"),
                details={"to": request.to, "from": self.from_number},
            )
            self._sent_log.append(result.model_dump())
            logger.info(f"SMS sent via Twilio: {result.sid}")
            return result

        except Exception as e:
            logger.error(f"Twilio send failed: {e}")
            return SMSResult(
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="twilio",
                status="failed",
                details={"error": str(e)},
            )

    async def _send_mock(self, request: SMSRequest) -> SMSResult:
        """Mock SMS sending for development."""
        import uuid

        sid = f"SM{uuid.uuid4().hex[:30]}"
        formatted_msg = _format_alert_sms(request)

        logger.info(
            f"\n{'='*50}\n"
            f"📱 MOCK SMS SENT\n"
            f"{'='*50}\n"
            f"  To:       {request.to}\n"
            f"  From:     {self.from_number}\n"
            f"  Priority: {request.priority}\n"
            f"  Hotel:    {request.hotel_id}\n"
            f"  SID:      {sid}\n"
            f"{'─'*50}\n"
            f"{formatted_msg}\n"
            f"{'='*50}"
        )

        result = SMSResult(
            success=True,
            sid=sid,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider="mock",
            status="delivered",
            details={"to": request.to, "from": self.from_number, "body_preview": request.message[:80]},
        )
        self._sent_log.append(result.model_dump())
        return result

    def get_sent_log(self) -> list[dict]:
        return self._sent_log.copy()

    def get_pending_approvals(self) -> dict:
        return {k: v for k, v in self._pending_approvals.items() if v["status"] == "pending"}


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────
twilio_service = TwilioService()
