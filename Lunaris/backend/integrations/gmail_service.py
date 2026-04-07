"""
Step 56: Gmail API Integration for Alert Notifications
Uses Google Gmail API to send critical hotel alerts (fire, security breach, VIP arrival, etc.)
Supports both real Gmail API and a mock fallback for development.
"""

import os
import json
import base64
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger("lunaris.integrations.gmail")


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class EmailAlert(BaseModel):
    """Schema for sending an alert email."""
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body (HTML supported)")
    priority: str = Field(default="normal", description="Priority: low, normal, high, critical")
    hotel_id: str = Field(default="HQ", description="Originating hotel ID")
    alert_type: str = Field(default="general", description="Alert type: fire, security, ops, vip, general")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class EmailResult(BaseModel):
    """Result of sending an email."""
    success: bool
    message_id: Optional[str] = None
    timestamp: str
    provider: str  # "gmail_api" or "mock"
    details: dict = Field(default_factory=dict)


# ─────────────────────────────────────────────
# Alert Templates
# ─────────────────────────────────────────────
ALERT_TEMPLATES = {
    "fire": {
        "subject_prefix": "🔥 [CRITICAL FIRE ALERT]",
        "color": "#FF4136",
        "icon": "🔥",
    },
    "security": {
        "subject_prefix": "🚨 [SECURITY ALERT]",
        "color": "#FF851B",
        "icon": "🚨",
    },
    "ops": {
        "subject_prefix": "⚙️ [OPERATIONS]",
        "color": "#0074D9",
        "icon": "⚙️",
    },
    "vip": {
        "subject_prefix": "⭐ [VIP NOTIFICATION]",
        "color": "#B10DC9",
        "icon": "⭐",
    },
    "general": {
        "subject_prefix": "📢 [AEGIS ALERT]",
        "color": "#2ECC40",
        "icon": "📢",
    },
}


def _build_html_body(alert: EmailAlert) -> str:
    """Build a beautifully formatted HTML email body."""
    template = ALERT_TEMPLATES.get(alert.alert_type, ALERT_TEMPLATES["general"])
    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #eee; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: #16213e; border-radius: 12px; overflow: hidden; border: 1px solid {template['color']}40;">
            <div style="background: {template['color']}; padding: 20px; text-align: center;">
                <h1 style="margin: 0; color: white; font-size: 24px;">
                    {template['icon']} Lunaris Hospitality OS
                </h1>
                <p style="margin: 5px 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">
                    Automated Alert System
                </p>
            </div>
            <div style="padding: 24px;">
                <h2 style="color: {template['color']}; margin-top: 0;">
                    {alert.subject}
                </h2>
                <div style="background: #0f3460; border-radius: 8px; padding: 16px; margin: 16px 0;">
                    {alert.body}
                </div>
                <table style="width: 100%; font-size: 13px; color: #aaa; margin-top: 16px;">
                    <tr>
                        <td><strong>Hotel:</strong> {alert.hotel_id}</td>
                        <td><strong>Priority:</strong> {alert.priority.upper()}</td>
                    </tr>
                    <tr>
                        <td><strong>Type:</strong> {alert.alert_type}</td>
                        <td><strong>Time:</strong> {datetime.now(timezone.utc).isoformat()}</td>
                    </tr>
                </table>
            </div>
            <div style="background: #0a0a23; padding: 12px; text-align: center; font-size: 11px; color: #555;">
                Lunaris Hospitality OS &bull; Secured by Auth0 Token Vault &bull; AI-Powered Operations
            </div>
        </div>
    </body>
    </html>
    """


# ─────────────────────────────────────────────
# Gmail API Client
# ─────────────────────────────────────────────
class GmailService:
    """
    Gmail integration for Lunaris alerts.
    Falls back to mock mode if credentials are not configured.
    """

    def __init__(self):
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
        self.sender_email = os.getenv("GMAIL_SENDER_EMAIL", "lunaris-os@lunaris-hospitality.com")
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._sent_log: list[dict] = []

    @property
    def is_configured(self) -> bool:
        return all([self.google_client_id, self.google_client_secret, self.google_refresh_token])

    async def _refresh_access_token(self) -> str:
        """Refresh OAuth2 access token using the refresh token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "refresh_token": self.google_refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            return self._access_token

    async def send_alert(self, alert: EmailAlert) -> EmailResult:
        """Send an alert email. Uses Gmail API if configured, otherwise falls back to mock."""
        if self.is_configured:
            return await self._send_via_gmail_api(alert)
        else:
            return await self._send_mock(alert)

    async def _send_via_gmail_api(self, alert: EmailAlert) -> EmailResult:
        """Send via real Gmail API."""
        try:
            token = await self._refresh_access_token()

            msg = MIMEMultipart("alternative")
            template = ALERT_TEMPLATES.get(alert.alert_type, ALERT_TEMPLATES["general"])
            msg["Subject"] = f"{template['subject_prefix']} {alert.subject}"
            msg["From"] = self.sender_email
            msg["To"] = alert.to
            msg["X-Priority"] = "1" if alert.priority == "critical" else "3"

            html_body = _build_html_body(alert)
            msg.attach(MIMEText(html_body, "html"))

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"raw": raw},
                )
                resp.raise_for_status()
                data = resp.json()

            result = EmailResult(
                success=True,
                message_id=data.get("id"),
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="gmail_api",
                details={"thread_id": data.get("threadId")},
            )
            self._sent_log.append(result.model_dump())
            logger.info(f"Email sent via Gmail API: {result.message_id}")
            return result

        except Exception as e:
            logger.error(f"Gmail API send failed: {e}")
            return EmailResult(
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="gmail_api",
                details={"error": str(e)},
            )

    async def _send_mock(self, alert: EmailAlert) -> EmailResult:
        """Mock email sending for development/hackathon demo."""
        import uuid

        mock_id = f"mock-{uuid.uuid4().hex[:12]}"
        template = ALERT_TEMPLATES.get(alert.alert_type, ALERT_TEMPLATES["general"])

        logger.info(
            f"\n{'='*60}\n"
            f"📧 MOCK EMAIL SENT\n"
            f"{'='*60}\n"
            f"  To:       {alert.to}\n"
            f"  Subject:  {template['subject_prefix']} {alert.subject}\n"
            f"  Priority: {alert.priority}\n"
            f"  Hotel:    {alert.hotel_id}\n"
            f"  Type:     {alert.alert_type}\n"
            f"  ID:       {mock_id}\n"
            f"{'='*60}"
        )

        result = EmailResult(
            success=True,
            message_id=mock_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider="mock",
            details={
                "to": alert.to,
                "subject": f"{template['subject_prefix']} {alert.subject}",
                "alert_type": alert.alert_type,
                "hotel_id": alert.hotel_id,
            },
        )
        self._sent_log.append(result.model_dump())
        return result

    def get_sent_log(self) -> list[dict]:
        """Return log of all sent emails for this session."""
        return self._sent_log.copy()


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────
gmail_service = GmailService()
