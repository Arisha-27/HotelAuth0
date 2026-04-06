"""
Audit Logging Middleware — Records every request/response with full context.
Writes structured JSON audit entries for compliance and security monitoring.
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from backend.config import settings
from backend.logging_config import get_logger, correlation_id_var, generate_correlation_id

logger = get_logger("middleware.audit")

# Dedicated audit file logger
_audit_logger: logging.Logger | None = None


def _get_audit_logger() -> logging.Logger:
    """Get or create the dedicated audit file logger."""
    global _audit_logger
    if _audit_logger is None:
        audit_path = Path(settings.AUDIT_LOG_FILE)
        audit_path.parent.mkdir(parents=True, exist_ok=True)

        _audit_logger = logging.getLogger("ahos.audit_file")
        _audit_logger.setLevel(logging.INFO)
        _audit_logger.propagate = False

        handler = logging.FileHandler(str(audit_path), mode="a", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        _audit_logger.addHandler(handler)

    return _audit_logger


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs every HTTP request/response as a structured
    audit trail entry with timing, identity, and outcome details.
    """

    # Paths to exclude from audit logging (noisy internal endpoints)
    EXCLUDE_PATHS = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip noisy endpoints
        if request.url.path in self.EXCLUDE_PATHS:
            return await call_next(request)

        # Generate and set correlation ID for this request
        corr_id = generate_correlation_id()
        correlation_id_var.set(corr_id)

        # Capture request details
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else None
        user_agent = request.headers.get("user-agent", "unknown")

        # Extract identity from Authorization header (if present)
        auth_header = request.headers.get("authorization", "")
        identity = "anonymous"
        if auth_header.startswith("Bearer "):
            # Just mark as "authenticated" — full identity comes from JWT payload
            identity = "bearer_token"

        # Process request
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            # Inject correlation ID into response headers
            response.headers["X-Correlation-ID"] = corr_id
            return response
        except Exception as e:
            logger.error(f"Unhandled exception during request: {e}", exc_info=True)
            raise
        finally:
            duration_ms = round((time.time() - start_time) * 1000, 2)

            # Build audit entry
            audit_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "correlation_id": corr_id,
                "method": method,
                "path": path,
                "query": query,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "identity": identity,
                "user_agent": user_agent,
            }

            # Log to structured logger
            logger.info(
                f"{method} {path} → {status_code} ({duration_ms}ms)",
                extra={"extra_data": audit_entry},
            )

            # Write to dedicated audit log file
            _get_audit_logger().info(json.dumps(audit_entry, default=str))
