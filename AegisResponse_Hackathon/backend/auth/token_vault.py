"""
Token Vault — Secure token management for Auth0 machine-to-machine flows.
Handles token acquisition, caching, and scope-specific requests.
"""

import time
from typing import Optional
import httpx
from fastapi import HTTPException

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger("auth.vault")

# ── Token Cache ─────────────────────────────────────────────
_token_cache: dict[str, dict] = {}  # scope_key -> {token, expires_at}


async def get_agent_token(scopes: Optional[list[str]] = None) -> str:
    """
    Request a scoped access token from Auth0 via client credentials grant.
    Tokens are cached until expiry.

    Args:
        scopes: Optional list of scopes to request (e.g., ['unlock:doors'])

    Returns:
        Bearer access token string
    """
    scope_key = " ".join(sorted(scopes)) if scopes else "__default__"

    # Check cache
    cached = _token_cache.get(scope_key)
    if cached and cached["expires_at"] > time.time():
        logger.info("Using cached token", extra={
            "extra_data": {"scope_key": scope_key, "ttl": int(cached["expires_at"] - time.time())}
        })
        return cached["token"]

    # Request new token
    url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
    payload = {
        "client_id": settings.AUTH0_CLIENT_ID,
        "client_secret": settings.AUTH0_CLIENT_SECRET,
        "audience": settings.AUTH0_AUDIENCE,
        "grant_type": "client_credentials",
    }

    if scopes:
        payload["scope"] = " ".join(scopes)

    logger.info("Requesting new token from Auth0", extra={
        "extra_data": {"scope_key": scope_key}
    })

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)

            if response.status_code != 200:
                error_detail = response.json().get("error_description", response.text)
                logger.error(f"Auth0 token request failed: {error_detail}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Auth0 denied the token request: {error_detail}",
                )

            data = response.json()
            token = data["access_token"]
            expires_in = data.get("expires_in", 86400)

            # Cache with 60-second safety margin
            _token_cache[scope_key] = {
                "token": token,
                "expires_at": time.time() + expires_in - 60,
            }

            logger.info("Token acquired and cached", extra={
                "extra_data": {
                    "scope_key": scope_key,
                    "expires_in": expires_in,
                    "token_preview": f"{token[:15]}...",
                }
            })

            return token

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching token: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to contact Auth0",
        )


def clear_token_cache() -> None:
    """Clear all cached tokens."""
    _token_cache.clear()
    logger.info("Token cache cleared")


def get_cached_tokens_info() -> list[dict]:
    """Return metadata about cached tokens (for metrics/monitoring)."""
    now = time.time()
    result = []
    for scope_key, entry in _token_cache.items():
        result.append({
            "scope_key": scope_key,
            "ttl_seconds": max(0, int(entry["expires_at"] - now)),
            "active": entry["expires_at"] > now,
        })
    return result
