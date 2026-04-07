"""
Centralized configuration for the Lunaris Hospitality OS backend.
Loads all settings from environment variables with validation.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the LunarisResponse_Hackathon root (parent of backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # ── Auth0 ──────────────────────────────────────────────
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "")
    AUTH0_CLIENT_ID: str = os.getenv("AUTH0_CLIENT_ID", "")
    AUTH0_CLIENT_SECRET: str = os.getenv("AUTH0_CLIENT_SECRET", "")
    AUTH0_AUDIENCE: str = os.getenv("AUTH0_AUDIENCE", "https://api.lunarisresponse.com")
    AUTH0_ISSUER: str = f"https://{AUTH0_DOMAIN}/"
    AUTH0_JWKS_URL: str = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    AUTH0_ALGORITHMS: list = ["RS256"]

    # ── App ────────────────────────────────────────────────
    APP_NAME: str = "Lunaris Hospitality OS"
    APP_VERSION: str = "5.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # ── Rate Limiting ──────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # ── Logging ────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/lunaris.log")
    AUDIT_LOG_FILE: str = os.getenv("AUDIT_LOG_FILE", "logs/audit.log")

    # ── Task Queue ─────────────────────────────────────────
    TASK_QUEUE_WORKERS: int = int(os.getenv("TASK_QUEUE_WORKERS", "3"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "1.0"))

    # ── Phase 5: Gmail API ─────────────────────────────────
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REFRESH_TOKEN: str = os.getenv("GOOGLE_REFRESH_TOKEN", "")
    GMAIL_SENDER_EMAIL: str = os.getenv("GMAIL_SENDER_EMAIL", "lunaris-os@lunaris-hospitality.com")

    # ── Phase 5: Notion API ────────────────────────────────
    NOTION_API_KEY: str = os.getenv("NOTION_API_KEY", "")
    NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")

    # ── Phase 5: Twilio SMS ────────────────────────────────
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "+15551234567")

    # ── Phase 5: Claude / Anthropic ────────────────────────
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    def validate(self) -> list[str]:
        """Return list of missing required configuration keys."""
        errors = []
        if not self.AUTH0_DOMAIN:
            errors.append("AUTH0_DOMAIN is required")
        if not self.AUTH0_CLIENT_ID:
            errors.append("AUTH0_CLIENT_ID is required")
        if not self.AUTH0_CLIENT_SECRET:
            errors.append("AUTH0_CLIENT_SECRET is required")
        return errors


settings = Settings()
