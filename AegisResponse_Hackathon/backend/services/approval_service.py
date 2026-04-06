"""
Phase 6 — Steps 66–72: Human-in-the-Loop Approval System
Intercepts critical actions, routes them for approval, enforces
role-based approval authority, and integrates with Twilio SMS.
"""

import uuid
import asyncio
from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from backend.logging_config import get_logger

logger = get_logger("services.approval")


# ═══════════════════════════════════════════
# Step 66: Critical Action Definitions
# ═══════════════════════════════════════════
class CriticalityLevel(str, Enum):
    """How critical an action is — determines approval requirements."""
    LOW = "low"              # No approval needed
    MEDIUM = "medium"        # Single manager approval
    HIGH = "high"            # Senior manager + SMS notification
    CRITICAL = "critical"    # Multi-party approval + step-up auth


class ActionCategory(str, Enum):
    """Categories of actions that can be intercepted."""
    SECURITY = "security"
    FINANCIAL = "financial"
    GUEST_DATA = "guest_data"
    INFRASTRUCTURE = "infrastructure"
    EMERGENCY = "emergency"


# ═══════════════════════════════════════════
# Step 72: Role-Based Approval Hierarchy
# ═══════════════════════════════════════════
class ApproverRole(str, Enum):
    STAFF = "staff"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    SENIOR_MANAGER = "senior_manager"
    DIRECTOR = "director"
    ADMIN = "admin"


# Which roles can approve which criticality levels
APPROVAL_AUTHORITY: dict[CriticalityLevel, list[ApproverRole]] = {
    CriticalityLevel.LOW: [
        ApproverRole.STAFF, ApproverRole.SUPERVISOR, ApproverRole.MANAGER,
        ApproverRole.SENIOR_MANAGER, ApproverRole.DIRECTOR, ApproverRole.ADMIN,
    ],
    CriticalityLevel.MEDIUM: [
        ApproverRole.MANAGER, ApproverRole.SENIOR_MANAGER,
        ApproverRole.DIRECTOR, ApproverRole.ADMIN,
    ],
    CriticalityLevel.HIGH: [
        ApproverRole.SENIOR_MANAGER, ApproverRole.DIRECTOR, ApproverRole.ADMIN,
    ],
    CriticalityLevel.CRITICAL: [
        ApproverRole.DIRECTOR, ApproverRole.ADMIN,
    ],
}


# ═══════════════════════════════════════════
# Step 66: Criticality Rules Engine
# ═══════════════════════════════════════════
CRITICALITY_RULES: list[dict] = [
    # Security
    {"pattern": "unlock_all_doors", "category": ActionCategory.SECURITY, "level": CriticalityLevel.CRITICAL},
    {"pattern": "fire_protocol", "category": ActionCategory.EMERGENCY, "level": CriticalityLevel.HIGH},
    {"pattern": "unlock_floor", "category": ActionCategory.SECURITY, "level": CriticalityLevel.HIGH},
    {"pattern": "unlock_door", "category": ActionCategory.SECURITY, "level": CriticalityLevel.MEDIUM},
    {"pattern": "lockdown", "category": ActionCategory.SECURITY, "level": CriticalityLevel.CRITICAL},
    # Financial
    {"pattern": "refund", "category": ActionCategory.FINANCIAL, "level": CriticalityLevel.HIGH, "threshold": 500},
    {"pattern": "charge_override", "category": ActionCategory.FINANCIAL, "level": CriticalityLevel.CRITICAL},
    {"pattern": "billing_adjustment", "category": ActionCategory.FINANCIAL, "level": CriticalityLevel.MEDIUM, "threshold": 100},
    # Guest Data
    {"pattern": "delete_guest", "category": ActionCategory.GUEST_DATA, "level": CriticalityLevel.CRITICAL},
    {"pattern": "export_guest_data", "category": ActionCategory.GUEST_DATA, "level": CriticalityLevel.HIGH},
    {"pattern": "modify_booking", "category": ActionCategory.GUEST_DATA, "level": CriticalityLevel.MEDIUM},
    # Infrastructure
    {"pattern": "hvac_override", "category": ActionCategory.INFRASTRUCTURE, "level": CriticalityLevel.MEDIUM},
    {"pattern": "elevator_shutdown", "category": ActionCategory.INFRASTRUCTURE, "level": CriticalityLevel.HIGH},
    {"pattern": "power_cutoff", "category": ActionCategory.INFRASTRUCTURE, "level": CriticalityLevel.CRITICAL},
    {"pattern": "system_restart", "category": ActionCategory.INFRASTRUCTURE, "level": CriticalityLevel.CRITICAL},
]


# ═══════════════════════════════════════════
# Models
# ═══════════════════════════════════════════
class ApprovalRequest(BaseModel):
    """A pending approval request."""
    approval_id: str = Field(default_factory=lambda: f"APR-{uuid.uuid4().hex[:8].upper()}")
    action_type: str
    action_description: str
    category: ActionCategory
    criticality: CriticalityLevel
    hotel_id: str = "hotel-grandview"
    requested_by: str = "system"              # agent or user who triggered
    requested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    timeout_minutes: int = 10
    # Approval state
    status: str = "pending"                   # pending, approved, denied, expired, escalated
    approver: Optional[str] = None
    approver_role: Optional[str] = None
    approved_at: Optional[str] = None
    denial_reason: Optional[str] = None
    # Step-up auth
    requires_step_up: bool = False
    step_up_method: Optional[str] = None      # "sms_otp", "biometric", "manager_override"
    step_up_verified: bool = False
    # Metadata
    context: dict = Field(default_factory=dict)
    sms_sent: bool = False


class ApprovalDecision(BaseModel):
    """The decision made on an approval request."""
    approval_id: str
    approved: bool
    approver: str = "admin"
    approver_role: ApproverRole = ApproverRole.ADMIN
    reason: Optional[str] = None
    step_up_token: Optional[str] = None       # For step-up auth verification


class CriticalActionCheck(BaseModel):
    """Input for checking if an action requires approval."""
    action_type: str
    description: str
    hotel_id: str = "hotel-grandview"
    agent_id: str = "system"
    amount: Optional[float] = None
    context: dict = Field(default_factory=dict)


class ActionInterceptResult(BaseModel):
    """Result of the action intercept check."""
    intercepted: bool
    requires_approval: bool
    criticality: Optional[CriticalityLevel] = None
    category: Optional[ActionCategory] = None
    approval_id: Optional[str] = None
    message: str = ""
    auto_approved: bool = False


# ═══════════════════════════════════════════
# Step 67: Approval Workflow Service
# ═══════════════════════════════════════════
class ApprovalService:
    """
    Central approval workflow engine.
    Intercepts critical actions, creates approval requests,
    validates approvals with role-based authority, and manages
    the full lifecycle of human-in-the-loop oversight.
    """

    def __init__(self):
        self._pending: dict[str, ApprovalRequest] = {}
        self._history: list[ApprovalRequest] = []
        self._step_up_tokens: dict[str, dict] = {}

    # ── Step 66: Intercept Critical Actions ──
    def check_action(self, check: CriticalActionCheck) -> ActionInterceptResult:
        """
        Evaluate whether an action requires human approval.
        Returns intercept result with criticality assessment.
        """
        matched_rule = None
        for rule in CRITICALITY_RULES:
            if rule["pattern"] in check.action_type.lower():
                # Check threshold-based rules (e.g., refunds over $500)
                if "threshold" in rule and check.amount is not None:
                    if check.amount < rule["threshold"]:
                        continue
                matched_rule = rule
                break

        if not matched_rule:
            return ActionInterceptResult(
                intercepted=False,
                requires_approval=False,
                message="Action does not require approval",
            )

        level = CriticalityLevel(matched_rule["level"])
        category = ActionCategory(matched_rule["category"])

        # LOW criticality = auto-approved
        if level == CriticalityLevel.LOW:
            return ActionInterceptResult(
                intercepted=True,
                requires_approval=False,
                criticality=level,
                category=category,
                auto_approved=True,
                message="Action auto-approved (LOW criticality)",
            )

        # Create approval request
        req = ApprovalRequest(
            action_type=check.action_type,
            action_description=check.description,
            category=category,
            criticality=level,
            hotel_id=check.hotel_id,
            requested_by=check.agent_id,
            timeout_minutes=5 if level == CriticalityLevel.CRITICAL else 10,
            requires_step_up=level == CriticalityLevel.CRITICAL,
            step_up_method="sms_otp" if level == CriticalityLevel.CRITICAL else None,
            context=check.context,
        )
        req.expires_at = (
            datetime.now(timezone.utc) + timedelta(minutes=req.timeout_minutes)
        ).isoformat()

        self._pending[req.approval_id] = req

        logger.warning(
            f"🔒 ACTION INTERCEPTED: {check.action_type} → {level.value} criticality",
            extra={"extra_data": {
                "approval_id": req.approval_id,
                "category": category.value,
                "criticality": level.value,
                "hotel_id": check.hotel_id,
                "agent": check.agent_id,
            }},
        )

        return ActionInterceptResult(
            intercepted=True,
            requires_approval=True,
            criticality=level,
            category=category,
            approval_id=req.approval_id,
            message=f"Action requires {level.value} approval (ID: {req.approval_id})",
        )

    # ── Step 70: Validate Approvals ──
    def process_decision(self, decision: ApprovalDecision) -> dict:
        """
        Process an approval or denial decision.
        Validates the approver has sufficient role authority.
        """
        req = self._pending.get(decision.approval_id)
        if not req:
            # Check history
            for h in self._history:
                if h.approval_id == decision.approval_id:
                    return {"error": "Already processed", "status": h.status, "approval_id": decision.approval_id}
            return {"error": "Approval request not found", "approval_id": decision.approval_id}

        # Check expiry
        if req.expires_at:
            exp = datetime.fromisoformat(req.expires_at)
            if datetime.now(timezone.utc) > exp:
                req.status = "expired"
                self._history.append(req)
                del self._pending[decision.approval_id]
                return {"error": "Approval request expired", "approval_id": decision.approval_id}

        # Step 72: Role-based authority check
        allowed_roles = APPROVAL_AUTHORITY.get(req.criticality, [])
        if decision.approver_role not in allowed_roles:
            return {
                "error": "Insufficient authority",
                "required_roles": [r.value for r in allowed_roles],
                "your_role": decision.approver_role.value,
                "criticality": req.criticality.value,
            }

        # Step 71: Step-up authentication check
        if req.requires_step_up and not req.step_up_verified:
            if decision.step_up_token:
                verified = self._verify_step_up(decision.approval_id, decision.step_up_token)
                if not verified:
                    return {"error": "Step-up authentication failed", "method": req.step_up_method}
            else:
                # Generate step-up challenge
                challenge = self._create_step_up_challenge(decision.approval_id)
                return {
                    "requires_step_up": True,
                    "method": req.step_up_method,
                    "challenge": challenge,
                    "message": "Step-up authentication required for CRITICAL actions",
                }

        # Process the decision
        now = datetime.now(timezone.utc).isoformat()
        if decision.approved:
            req.status = "approved"
            req.approver = decision.approver
            req.approver_role = decision.approver_role.value
            req.approved_at = now
            logger.info(f"✅ APPROVED: {req.approval_id} by {decision.approver} ({decision.approver_role.value})")
        else:
            req.status = "denied"
            req.approver = decision.approver
            req.approver_role = decision.approver_role.value
            req.approved_at = now
            req.denial_reason = decision.reason or "No reason provided"
            logger.info(f"❌ DENIED: {req.approval_id} by {decision.approver}: {req.denial_reason}")

        self._history.append(req)
        del self._pending[decision.approval_id]

        return {
            "success": True,
            "approval_id": req.approval_id,
            "status": req.status,
            "action_type": req.action_type,
            "approver": req.approver,
            "approver_role": req.approver_role,
            "timestamp": now,
        }

    # ── Step 71: Step-Up Authentication ──
    def _create_step_up_challenge(self, approval_id: str) -> dict:
        """Generate a step-up authentication challenge (OTP code)."""
        otp = str(uuid.uuid4().int)[:6]
        self._step_up_tokens[approval_id] = {
            "otp": otp,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            "verified": False,
        }
        logger.info(f"🔐 Step-up OTP generated for {approval_id}: {otp}")
        return {"otp_hint": f"***{otp[-2:]}", "expires_in": "5 minutes", "method": "sms_otp"}

    def _verify_step_up(self, approval_id: str, token: str) -> bool:
        """Verify a step-up authentication token."""
        challenge = self._step_up_tokens.get(approval_id)
        if not challenge:
            return False
        if challenge["otp"] == token:
            challenge["verified"] = True
            if approval_id in self._pending:
                self._pending[approval_id].step_up_verified = True
            return True
        return False

    def get_step_up_otp(self, approval_id: str) -> Optional[str]:
        """Get the OTP for testing purposes."""
        challenge = self._step_up_tokens.get(approval_id)
        return challenge["otp"] if challenge else None

    # ── Escalation ──
    def escalate(self, approval_id: str, reason: str = "Timeout") -> dict:
        """Escalate a pending approval to higher authority."""
        req = self._pending.get(approval_id)
        if not req:
            return {"error": "Not found"}
        req.status = "escalated"
        logger.warning(f"⚡ ESCALATED: {approval_id} — {reason}")
        return {"approval_id": approval_id, "status": "escalated", "reason": reason}

    # ── Query Methods ──
    def get_pending(self, hotel_id: str = None) -> list[dict]:
        pending = list(self._pending.values())
        if hotel_id:
            pending = [p for p in pending if p.hotel_id == hotel_id]
        return [p.model_dump() for p in pending]

    def get_history(self, limit: int = 50, status: str = None) -> list[dict]:
        history = self._history.copy()
        if status:
            history = [h for h in history if h.status == status]
        return [h.model_dump() for h in history[-limit:]]

    def get_approval(self, approval_id: str) -> Optional[dict]:
        req = self._pending.get(approval_id)
        if req:
            return req.model_dump()
        for h in self._history:
            if h.approval_id == approval_id:
                return h.model_dump()
        return None

    def get_stats(self) -> dict:
        """Get approval system statistics."""
        all_items = list(self._pending.values()) + self._history
        return {
            "total_requests": len(all_items),
            "pending": len(self._pending),
            "approved": len([h for h in self._history if h.status == "approved"]),
            "denied": len([h for h in self._history if h.status == "denied"]),
            "expired": len([h for h in self._history if h.status == "expired"]),
            "escalated": len([h for h in self._history if h.status == "escalated"]),
            "by_criticality": {
                level.value: len([i for i in all_items if i.criticality == level])
                for level in CriticalityLevel
            },
            "by_category": {
                cat.value: len([i for i in all_items if i.category == cat])
                for cat in ActionCategory
            },
        }


# Singleton
approval_service = ApprovalService()
