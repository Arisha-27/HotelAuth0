"""
Rate Limiting Middleware — Sliding window rate limiter.
Prevents abuse by limiting requests per client IP within a time window.
"""

import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger("middleware.ratelimit")


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter.
    Tracks request timestamps per client IP and enforces limits.
    """

    # Paths exempt from rate limiting
    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    def __init__(self, app, max_requests: int = None, window_seconds: int = None):
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS
        # client_ip -> list of request timestamps
        self._request_log: dict[str, list[float]] = defaultdict(list)

    def _cleanup_old_entries(self, client_ip: str, now: float) -> None:
        """Remove timestamps outside the current window."""
        cutoff = now - self.window_seconds
        self._request_log[client_ip] = [
            ts for ts in self._request_log[client_ip] if ts > cutoff
        ]

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean up old entries
        self._cleanup_old_entries(client_ip, now)

        # Check rate limit
        request_count = len(self._request_log[client_ip])

        if request_count >= self.max_requests:
            # Calculate retry-after
            oldest_in_window = self._request_log[client_ip][0]
            retry_after = int(self.window_seconds - (now - oldest_in_window)) + 1

            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={
                    "extra_data": {
                        "client_ip": client_ip,
                        "request_count": request_count,
                        "limit": self.max_requests,
                        "window": self.window_seconds,
                    }
                },
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Record this request
        self._request_log[client_ip].append(now)

        # Add rate limit info to response headers
        response = await call_next(request)
        remaining = self.max_requests - len(self._request_log[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = f"{self.window_seconds}s"

        return response
