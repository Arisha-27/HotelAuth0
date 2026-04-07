"""
RBAC — Role-Based Access Control with scope enforcement.
Maps agent roles to permitted scopes and provides FastAPI dependencies
for scope-gated endpoint access.
"""

from enum import Enum
from typing import Callable
from fastapi import Depends, HTTPException, status

from backend.auth.jwt_validator import validate_jwt
from backend.logging_config import get_logger

logger = get_logger("auth.rbac")


# ── Scopes ──────────────────────────────────────────────────
class Scope(str, Enum):
    """All OAuth2 scopes defined in the Lunaris API."""
    UNLOCK_DOORS = "unlock:doors"
    NOTIFY_GUESTS = "notify:guests"
    MANAGE_BOOKINGS = "manage:bookings"
    READ_FINANCE = "read:finance"


# ── Roles ───────────────────────────────────────────────────
class AgentRole(str, Enum):
    """Hierarchical agent roles in the Lunaris system."""
    EXECUTIVE = "executive_agent"
    SECURITY = "security_agent"
    OPERATIONS = "operations_agent"
    FINANCE = "finance_agent"
    ADMIN = "admin"


# ── Role → Scope Mapping ───────────────────────────────────
ROLE_SCOPES: dict[AgentRole, set[Scope]] = {
    AgentRole.ADMIN: {
        Scope.UNLOCK_DOORS,
        Scope.NOTIFY_GUESTS,
        Scope.MANAGE_BOOKINGS,
        Scope.READ_FINANCE,
    },
    AgentRole.EXECUTIVE: {
        Scope.UNLOCK_DOORS,
        Scope.NOTIFY_GUESTS,
        Scope.MANAGE_BOOKINGS,
        Scope.READ_FINANCE,
    },
    AgentRole.SECURITY: {
        Scope.UNLOCK_DOORS,
        Scope.NOTIFY_GUESTS,
    },
    AgentRole.OPERATIONS: {
        Scope.NOTIFY_GUESTS,
        Scope.MANAGE_BOOKINGS,
    },
    AgentRole.FINANCE: {
        Scope.READ_FINANCE,
    },
}


def get_role_scopes(role: AgentRole) -> set[Scope]:
    """Return the set of scopes permitted for a given role."""
    return ROLE_SCOPES.get(role, set())


def require_scope(required_scope: Scope) -> Callable:
    """
    FastAPI dependency factory: returns a dependency that validates
    the JWT payload contains the required scope.

    Usage:
        @router.post("/security/unlock")
        async def unlock(payload: dict = Depends(require_scope(Scope.UNLOCK_DOORS))):
            ...
    """

    async def _scope_validator(payload: dict = Depends(validate_jwt)) -> dict:
        token_scopes = payload.get("scope", "")
        if isinstance(token_scopes, str):
            token_scopes = token_scopes.split()

        if required_scope.value not in token_scopes:
            logger.warning(
                f"Scope denied: required={required_scope.value}, "
                f"token_scopes={token_scopes}, sub={payload.get('sub', 'unknown')}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scope. Required: {required_scope.value}",
            )

        logger.info(
            f"Scope granted: {required_scope.value}",
            extra={"extra_data": {"sub": payload.get("sub"), "scope": required_scope.value}},
        )
        return payload

    return _scope_validator


def require_role(required_role: AgentRole) -> Callable:
    """
    FastAPI dependency factory: validates the JWT payload has a role
    with sufficient permissions.

    The role is expected in the JWT custom claim 'https://lunaris/role'.
    """

    async def _role_validator(payload: dict = Depends(validate_jwt)) -> dict:
        # Extract role from custom namespace claim or permissions
        token_role = payload.get("https://lunaris/role", "")
        token_scopes = payload.get("scope", "")
        if isinstance(token_scopes, str):
            token_scopes = set(token_scopes.split())
        else:
            token_scopes = set(token_scopes)

        # Check if token role matches or has required scopes
        try:
            role = AgentRole(token_role)
        except ValueError:
            role = None

        if role == required_role or role == AgentRole.ADMIN:
            return payload

        # Fallback: check if token has all scopes for the required role
        required_scopes = {s.value for s in get_role_scopes(required_role)}
        if required_scopes.issubset(token_scopes):
            return payload

        logger.warning(
            f"Role denied: required={required_role.value}, token_role={token_role}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient role. Required: {required_role.value}",
        )

    return _role_validator
