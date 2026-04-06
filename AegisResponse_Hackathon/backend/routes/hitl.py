"""
Phase 6 — API Routes: Human-in-the-Loop + Security
Steps 66–75 exposed as REST endpoints.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

from backend.services.approval_service import (
    approval_service, CriticalActionCheck, ApprovalDecision, ApproverRole,
)
from backend.services.consent_log import consent_log
from backend.services.security_engine import (
    anomaly_detector, attack_simulator, AttackScenario,
)
from backend.integrations.twilio_service import twilio_service, ApprovalSMS
from backend.logging_config import get_logger

logger = get_logger("routes.hitl")

router = APIRouter(prefix="/api/v1/hitl", tags=["Human-in-the-Loop"])


# ═══════════════════════════════════════════
# Steps 66–67: Action Interception + Approvals
# ═══════════════════════════════════════════

@router.post("/intercept")
async def intercept_action(check: CriticalActionCheck):
    """
    Step 66: Check if an action requires human approval.
    Evaluates the action against the criticality rules engine
    and creates an approval request if needed.
    """
    result = approval_service.check_action(check)

    # If intercepted, log to consent log
    if result.intercepted:
        consent_log.log(
            action_type="interception",
            action_description=f"Action '{check.action_type}' intercepted — criticality: {result.criticality}",
            actor=check.agent_id,
            category=result.category.value if result.category else "",
            criticality=result.criticality.value if result.criticality else "",
            approval_id=result.approval_id or "",
            hotel_id=check.hotel_id,
        )

        # Step 68: Send SMS for HIGH/CRITICAL actions
        if result.criticality in ("high", "critical") and result.approval_id:
            try:
                sms_result = await twilio_service.send_approval_request(ApprovalSMS(
                    to="+15551234567",  # Default manager number
                    action_description=check.description,
                    action_id=result.approval_id,
                    hotel_id=check.hotel_id,
                    timeout_minutes=5 if result.criticality == "critical" else 10,
                ))
                # Mark SMS sent on the approval request
                req = approval_service._pending.get(result.approval_id)
                if req:
                    req.sms_sent = sms_result.success
            except Exception as e:
                logger.error(f"Failed to send approval SMS: {e}")

    return result.model_dump()


@router.get("/approvals/pending")
async def get_pending_approvals(hotel_id: str = Query(None)):
    """Get all pending approval requests."""
    return {"pending": approval_service.get_pending(hotel_id), "count": len(approval_service.get_pending(hotel_id))}


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str):
    """Get details of a specific approval request."""
    data = approval_service.get_approval(approval_id)
    if not data:
        return {"error": "Not found", "approval_id": approval_id}
    return data


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(approval_id: str, decision: ApprovalDecision):
    """
    Step 70: Process an approval or denial decision.
    Validates role authority and step-up auth if required.
    """
    decision.approval_id = approval_id
    result = approval_service.process_decision(decision)

    # Log the decision to consent log
    if result.get("success"):
        req_data = approval_service.get_approval(approval_id)
        if req_data:
            consent_log.log_approval(req_data)

    return result


@router.post("/approvals/{approval_id}/escalate")
async def escalate_approval(approval_id: str, reason: str = "Manual escalation"):
    """Escalate a pending approval to higher authority."""
    return approval_service.escalate(approval_id, reason)


@router.get("/approvals/history")
async def get_approval_history(
    limit: int = Query(50, ge=1, le=200),
    status: str = Query(None),
):
    """Get approval decision history."""
    return {"history": approval_service.get_history(limit, status)}


@router.get("/approvals/stats")
async def get_approval_stats():
    """Get approval system statistics."""
    return approval_service.get_stats()


# ═══════════════════════════════════════════
# Step 69: Webhook Listener (SMS Replies)
# ═══════════════════════════════════════════

class WebhookPayload(BaseModel):
    """Incoming webhook from Twilio / external service."""
    From: str = ""
    Body: str = ""
    action_id: str = ""

@router.post("/webhook/sms")
async def sms_webhook(payload: WebhookPayload):
    """
    Step 69: Receive SMS approval responses via webhook.
    Parses YES/NO replies and processes the approval decision.
    """
    body = payload.Body.strip().upper()
    action_id = payload.action_id

    # Try to find action_id from pending approvals if not provided
    if not action_id:
        pending = twilio_service.get_pending_approvals()
        for aid, data in pending.items():
            if data.get("to") == payload.From:
                action_id = aid
                break

    if not action_id:
        return {"error": "No matching pending approval found"}

    approved = body in ("YES", "Y", "APPROVE", "OK", "1")
    denied = body in ("NO", "N", "DENY", "REJECT", "0")

    if not approved and not denied:
        return {"error": "Unrecognized response. Reply YES or NO."}

    # Process via Twilio service
    twilio_result = twilio_service.process_approval_response(action_id, approved)

    # Also process via approval service
    decision = ApprovalDecision(
        approval_id=action_id,
        approved=approved,
        approver=payload.From or "sms_responder",
        approver_role=ApproverRole.MANAGER,
        reason=f"SMS {'approval' if approved else 'denial'}: {body}",
    )
    approval_result = approval_service.process_decision(decision)

    consent_log.log(
        action_type="sms_approval" if approved else "sms_denial",
        action_description=f"SMS response '{body}' for action {action_id}",
        actor=payload.From or "sms_responder",
        actor_role="manager",
        approval_id=action_id,
    )

    return {"twilio": twilio_result, "approval": approval_result}


# ═══════════════════════════════════════════
# Step 71: Step-Up Authentication
# ═══════════════════════════════════════════

class StepUpVerification(BaseModel):
    otp: str

@router.post("/step-up/{approval_id}/verify")
async def verify_step_up(approval_id: str, verification: StepUpVerification):
    """Verify step-up authentication OTP for CRITICAL actions."""
    otp_valid = approval_service._verify_step_up(approval_id, verification.otp)
    if otp_valid:
        consent_log.log(
            action_type="step_up_verified",
            action_description=f"Step-up authentication verified for {approval_id}",
            actor="otp_system",
            approval_id=approval_id,
        )
        return {"verified": True, "approval_id": approval_id, "message": "Step-up authentication successful. You may now approve the action."}
    return {"verified": False, "message": "Invalid OTP"}

@router.get("/step-up/{approval_id}/otp")
async def get_step_up_otp(approval_id: str):
    """Get the OTP for testing (development only)."""
    otp = approval_service.get_step_up_otp(approval_id)
    if otp:
        return {"approval_id": approval_id, "otp": otp, "warning": "DEV ONLY — remove in production"}
    return {"error": "No OTP found for this approval"}


# ═══════════════════════════════════════════
# Step 73: Consent Logs
# ═══════════════════════════════════════════

@router.get("/consent/log")
async def get_consent_log(
    limit: int = Query(50, ge=1, le=500),
    action_type: str = Query(None),
    actor: str = Query(None),
    hotel_id: str = Query(None),
):
    """Get consent/audit log entries."""
    return {"entries": consent_log.get_entries(limit, action_type, actor, hotel_id)}


@router.get("/consent/verify")
async def verify_consent_integrity():
    """Verify the integrity of the consent log chain (tamper detection)."""
    return consent_log.verify_integrity()


@router.get("/consent/stats")
async def get_consent_stats():
    """Get consent log statistics."""
    return consent_log.get_stats()


# ═══════════════════════════════════════════
# Step 74: Anomaly Detection
# ═══════════════════════════════════════════

@router.get("/anomalies")
async def get_anomaly_alerts(
    limit: int = Query(50, ge=1, le=200),
    threat_level: str = Query(None),
    acknowledged: bool = Query(None),
):
    """Get anomaly detection alerts."""
    return {
        "alerts": anomaly_detector.get_alerts(limit, threat_level, acknowledged),
        "stats": anomaly_detector.get_stats(),
    }


@router.post("/anomalies/{alert_id}/acknowledge")
async def acknowledge_anomaly(alert_id: str, acknowledged_by: str = "admin"):
    """Acknowledge an anomaly alert."""
    result = anomaly_detector.acknowledge_alert(alert_id, acknowledged_by)
    if result.get("success"):
        consent_log.log(
            action_type="anomaly_acknowledged",
            action_description=f"Anomaly alert {alert_id} acknowledged",
            actor=acknowledged_by,
        )
    return result


@router.post("/anomalies/simulate-request")
async def simulate_anomaly_request(
    source: str = "test_source",
    scope: str = "",
    hotel_id: str = "hotel-grandview",
):
    """Simulate a request through the anomaly detector for testing."""
    alert = anomaly_detector.record_request(source, scope, hotel_id)
    return {
        "anomaly_detected": alert is not None,
        "alert": alert.model_dump() if alert else None,
    }


# ═══════════════════════════════════════════
# Step 75: Attack Simulation
# ═══════════════════════════════════════════

@router.post("/attack-sim/run")
async def run_attack_simulation(
    scenario: AttackScenario,
    hotel_id: str = "hotel-grandview",
):
    """
    Step 75: Run an attack simulation scenario.
    Available scenarios: brute_force, privilege_escalation,
    data_exfiltration, rapid_fire_requests, off_hours_access,
    social_engineering, token_replay, agent_manipulation
    """
    result = await attack_simulator.run_scenario(scenario, hotel_id)

    consent_log.log(
        action_type="attack_simulation",
        action_description=f"Attack simulation: {scenario.value} — {'PASS' if result.success else 'FAIL'}",
        actor="security_team",
        category="security",
        hotel_id=hotel_id,
        metadata={"simulation_id": result.simulation_id, "success": result.success},
    )

    return result.model_dump()


@router.post("/attack-sim/run-all")
async def run_all_simulations(hotel_id: str = "hotel-grandview"):
    """Run ALL attack simulation scenarios and produce a full security report."""
    results = []
    for scenario in AttackScenario:
        result = await attack_simulator.run_scenario(scenario, hotel_id)
        results.append(result.model_dump())

    summary = attack_simulator.get_summary()

    consent_log.log(
        action_type="full_security_audit",
        action_description=f"Full attack simulation suite — {summary['pass_rate']} pass rate",
        actor="security_team",
        category="security",
        hotel_id=hotel_id,
    )

    return {
        "summary": summary,
        "results": results,
    }


@router.get("/attack-sim/results")
async def get_simulation_results(limit: int = Query(20)):
    """Get past attack simulation results."""
    return {"results": attack_simulator.get_results(limit), "summary": attack_simulator.get_summary()}


# ═══════════════════════════════════════════
# Phase 6 Dashboard Summary
# ═══════════════════════════════════════════

@router.get("/dashboard")
async def hitl_dashboard():
    """Get a full Phase 6 HITL + Security dashboard summary."""
    return {
        "approvals": approval_service.get_stats(),
        "consent_log": consent_log.get_stats(),
        "anomaly_detection": anomaly_detector.get_stats(),
        "attack_simulations": attack_simulator.get_summary(),
        "pending_approvals": approval_service.get_pending(),
        "recent_anomalies": anomaly_detector.get_alerts(limit=5),
    }
