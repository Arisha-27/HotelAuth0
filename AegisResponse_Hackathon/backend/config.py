"""
Centralized configuration for the Aegis Hospitality OS backend.
Loads all settings from environment variables with validation.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the AegisResponse_Hackathon root (parent of backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # ── Auth0 ──────────────────────────────────────────────
    AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "")
    AUTH0_CLIENT_ID: str = os.getenv("AUTH0_CLIENT_ID", "")
    AUTH0_CLIENT_SECRET: str = os.getenv("AUTH0_CLIENT_SECRET", "")
    AUTH0_AUDIENCE: str = os.getenv("AUTH0_AUDIENCE", "https://api.aegisresponse.com")
    AUTH0_ISSUER: str = f"https://{AUTH0_DOMAIN}/"
    AUTH0_JWKS_URL: str = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    AUTH0_ALGORITHMS: list = ["RS256"]

    # ── App ────────────────────────────────────────────────
    APP_NAME: str = "Aegis Hospitality OS"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # ── Rate Limiting ──────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # ── Logging ────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/ahos.log")
    AUDIT_LOG_FILE: str = os.getenv("AUDIT_LOG_FILE", "logs/audit.log")

    # ── Task Queue ─────────────────────────────────────────
    TASK_QUEUE_WORKERS: int = int(os.getenv("TASK_QUEUE_WORKERS", "3"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "1.0"))

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
