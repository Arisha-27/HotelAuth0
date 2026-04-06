"""
JWT Validator — Auth0 public key verification using JWKS.
Fetches RSA public keys from Auth0 and validates JWT signatures.
"""

import time
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import jwt, JWTError, ExpiredSignatureError

from backend.config import settings
from backend.logging_config import get_logger

logger = get_logger("auth.jwt")
security_scheme = HTTPBearer(auto_error=True)

# ── JWKS Cache ──────────────────────────────────────────────
_jwks_cache: dict = {}
_jwks_cache_ttl: int = 3600  # 1 hour
_jwks_cache_timestamp: float = 0.0


async def _fetch_jwks() -> dict:
    """Fetch JSON Web Key Set from Auth0 with caching."""
    global _jwks_cache, _jwks_cache_timestamp

    now = time.time()
    if _jwks_cache and (now - _jwks_cache_timestamp) < _jwks_cache_ttl:
        return _jwks_cache

    logger.info("Fetching JWKS from Auth0", extra={
        "extra_data": {"url": settings.AUTH0_JWKS_URL}
    })

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.AUTH0_JWKS_URL)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_timestamp = now
            logger.info("JWKS cache refreshed", extra={
                "extra_data": {"keys_count": len(_jwks_cache.get("keys", []))}
            })
            return _jwks_cache
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        if _jwks_cache:
            logger.warning("Using stale JWKS cache")
            return _jwks_cache
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch Auth0 public keys",
        )


def _get_rsa_key(jwks: dict, token: str) -> Optional[dict]:
    """Extract the RSA public key matching the token's kid header."""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        return None

    kid = unverified_header.get("kid")
    if not kid:
        return None

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
    return None


async def validate_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """
    FastAPI dependency: validate the JWT bearer token against Auth0 JWKS.
    Returns the decoded token payload on success.
    """
    token = credentials.credentials

    # Fetch JWKS and find matching key
    jwks = await _fetch_jwks()
    rsa_key = _get_rsa_key(jwks, token)

    if not rsa_key:
        logger.warning("No matching RSA key found for token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: no matching signing key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=settings.AUTH0_ALGORITHMS,
            audience=settings.AUTH0_AUDIENCE,
            issuer=settings.AUTH0_ISSUER,
        )
        logger.info("JWT validated successfully", extra={
            "extra_data": {
                "sub": payload.get("sub", "unknown"),
                "scopes": payload.get("scope", ""),
            }
        })
        return payload

    except ExpiredSignatureError:
        logger.warning("JWT has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def invalidate_jwks_cache() -> None:
    """Force JWKS cache to refresh on next request."""
    global _jwks_cache_timestamp
    _jwks_cache_timestamp = 0.0
    logger.info("JWKS cache invalidated")
