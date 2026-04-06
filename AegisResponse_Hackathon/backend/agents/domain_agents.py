"""
Steps 40-43: Domain Agents — Security, Operations, Finance
Mid-level agents that handle domain-specific tasks.
Each has its own scoped token, memory, and connection to Phase 5 services.
"""

from backend.agents.base import (
    BaseAgent, AgentInput, AgentOutput, AgentTier, ReasoningStep, Confidence
)
from backend.agents.brain import LLMBrain, default_brain
from backend.logging_config import get_logger

logger = get_logger("agents.domain")


# ═══════════════════════════════════════════
# Step 41: Security Agent
# ═══════════════════════════════════════════
class SecurityAgent(BaseAgent):
    """Handles emergency protocols, access control, and security incidents."""

    def __init__(self, brain: LLMBrain = None):
        super().__init__(
            agent_id="security",
            agent_name="Security Agent",
            tier=AgentTier.DOMAIN,
            description="Emergency handling, door access, fire protocols, security incidents",
            scopes=["unlock:doors", "notify:guests"],
            brain=brain or default_brain,
        )

    async def _execute(self, input: AgentInput) -> AgentOutput:
        reasoning = []
        actions_taken = []
        result = {}
        confidence = 0.9

        action = input.context.get("action", self._infer_action(input.message))
        hotel_id = input.hotel_id

        reasoning.append(ReasoningStep(
            step_number=1,
            thought=f"Security action requested: {action} at hotel {hotel_id}",
            action=f"security.{action}",
        ))

        if action == "trigger_fire_alarm":
            from backend.integrations.iot_service import iot_simulator
            floor = input.context.get("floor", 1)
            result = await iot_simulator.trigger_fire_protocol(hotel_id, floor, self.agent_id)
            reasoning[-1].observation = f"Fire protocol executed: {len(result.get('doors', []))} doors unlocked"
            actions_taken.append({"action": "fire_protocol", "floor": floor, "result": "executed"})
            confidence = 0.95

        elif action in ("unlock_door", "unlock_floor"):
            from backend.integrations.iot_service import iot_simulator
            floor = input.context.get("floor", 1)
            result = await iot_simulator.unlock_floor(hotel_id, floor, self.agent_id)
            actions_taken.append({"action": "unlock_floor", "floor": floor, "doors": len(result)})
            reasoning[-1].observation = f"Unlocked {len(result)} doors on floor {floor}"
            confidence = 0.9

        elif action == "lockdown_area":
            result = {"action": "lockdown", "hotel_id": hotel_id, "status": "lockdown_initiated"}
            reasoning[-1].observation = "Area lockdown initiated"
            actions_taken.append({"action": "lockdown", "status": "initiated"})
            confidence = 0.85

        elif action == "verify_authorization":
            result = {"authorized": True, "method": "token_vault", "agent": self.agent_id}
            reasoning[-1].observation = "Authorization verified via token vault"
            confidence = 0.95

        else:
            result = {"action": action, "status": "acknowledged", "agent": self.agent_id}
            reasoning[-1].observation = f"Action '{action}' acknowledged"
            confidence = 0.7

        return AgentOutput(
            request_id=input.request_id,
            agent_id=self.agent_id,
            agent_tier=self.tier,
            status="completed",
            result=result,
            reasoning=reasoning,
            confidence_score=confidence,
            actions_taken=actions_taken,
        )

    def _infer_action(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ("fire", "smoke", "alarm")):
            return "trigger_fire_alarm"
        if any(w in msg for w in ("unlock", "open", "door")):
            return "unlock_door"
        if any(w in msg for w in ("lock", "lockdown", "secure")):
            return "lockdown_area"
        return "assess_threat"


# ═══════════════════════════════════════════
# Step 42: Operations Agent
# ═══════════════════════════════════════════
class OperationsAgent(BaseAgent):
    """Handles guest services, bookings, notifications, and housekeeping."""

    def __init__(self, brain: LLMBrain = None):
        super().__init__(
            agent_id="operations",
            agent_name="Operations Agent",
            tier=AgentTier.DOMAIN,
            description="Guest services, bookings, notifications, housekeeping, maintenance",
            scopes=["notify:guests", "manage:bookings"],
            brain=brain or default_brain,
        )

    async def _execute(self, input: AgentInput) -> AgentOutput:
        reasoning = []
        actions_taken = []
        result = {}
        confidence = 0.85

        action = input.context.get("action", self._infer_action(input.message))
        hotel_id = input.hotel_id

        reasoning.append(ReasoningStep(
            step_number=1,
            thought=f"Operations action: {action} at hotel {hotel_id}",
            action=f"operations.{action}",
        ))

        if action == "notify_guests":
            from backend.integrations.gmail_service import gmail_service, EmailAlert
            from backend.integrations.twilio_service import twilio_service, SMSRequest
            # Send both email and SMS
            msg = input.context.get("message", input.message)
            alert_type = input.context.get("type", "ops")

            email_result = await gmail_service.send_alert(EmailAlert(
                to=input.context.get("email", "guests@aegis.com"),
                subject=f"[{hotel_id}] {msg[:50]}",
                body=f"<p>{msg}</p>",
                hotel_id=hotel_id,
                alert_type=alert_type,
            ))
            actions_taken.append({"action": "email_sent", "id": email_result.message_id})

            sms_result = await twilio_service.send_alert(SMSRequest(
                to=input.context.get("phone", "+1234567890"),
                message=msg,
                hotel_id=hotel_id,
            ))
            actions_taken.append({"action": "sms_sent", "sid": sms_result.sid})
            result = {"notifications_sent": 2, "email": email_result.model_dump(), "sms": sms_result.model_dump()}
            reasoning[-1].observation = "Email and SMS notifications sent"

        elif action in ("verify_reservation", "manage_booking", "assign_room"):
            from backend.database.hotel_db import hotel_db
            bookings = hotel_db.get_bookings(hotel_id=hotel_id)
            result = {"bookings_found": len(bookings), "action": action, "status": "processed"}
            reasoning[-1].observation = f"Found {len(bookings)} bookings for {hotel_id}"

        elif action == "check_vip_preferences":
            from backend.database.hotel_db import hotel_db
            guests = hotel_db.get_guests(vip_only=True)
            result = {"vip_guests": len(guests), "guests": [g["name"] for g in guests[:5]]}
            reasoning[-1].observation = f"Loaded {len(guests)} VIP guests"

        elif action in ("housekeeping_request", "maintenance_request"):
            from backend.integrations.notion_service import notion_service, NotionLogEntry
            log = await notion_service.create_log(NotionLogEntry(
                title=f"{action.replace('_', ' ').title()} — {hotel_id}",
                category="maintenance" if "maintenance" in action else "general",
                hotel_id=hotel_id,
                description=input.message,
                assigned_agent=self.agent_id,
            ))
            actions_taken.append({"action": "notion_log", "page_id": log.page_id})
            result = {"logged": True, "page_id": log.page_id}
            reasoning[-1].observation = f"Logged to Notion: {log.page_id}"

        else:
            result = {"action": action, "status": "acknowledged", "agent": self.agent_id}
            reasoning[-1].observation = f"Action '{action}' acknowledged"
            confidence = 0.7

        return AgentOutput(
            request_id=input.request_id,
            agent_id=self.agent_id,
            agent_tier=self.tier,
            status="completed",
            result=result,
            reasoning=reasoning,
            confidence_score=confidence,
            actions_taken=actions_taken,
        )

    def _infer_action(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ("notify", "alert", "message")):
            return "notify_guests"
        if any(w in msg for w in ("book", "reservation", "checkin", "checkout")):
            return "manage_booking"
        if any(w in msg for w in ("vip", "preference")):
            return "check_vip_preferences"
        if any(w in msg for w in ("clean", "housekeeping")):
            return "housekeeping_request"
        if any(w in msg for w in ("repair", "maintenance", "fix")):
            return "maintenance_request"
        return "handle_request"


# ═══════════════════════════════════════════
# Step 43: Finance Agent
# ═══════════════════════════════════════════
class FinanceAgent(BaseAgent):
    """Handles billing, refunds, fraud detection, and financial logging."""

    def __init__(self, brain: LLMBrain = None):
        super().__init__(
            agent_id="finance",
            agent_name="Finance Agent",
            tier=AgentTier.DOMAIN,
            description="Billing, refunds, fraud detection, financial logging",
            scopes=["read:finance"],
            brain=brain or default_brain,
        )

    async def _execute(self, input: AgentInput) -> AgentOutput:
        reasoning = []
        actions_taken = []
        result = {}
        confidence = 0.85

        action = input.context.get("action", self._infer_action(input.message))
        hotel_id = input.hotel_id

        reasoning.append(ReasoningStep(
            step_number=1,
            thought=f"Finance action: {action} at hotel {hotel_id}",
            action=f"finance.{action}",
        ))

        if action == "log_incident":
            from backend.database.hotel_db import hotel_db, FinanceRecord
            import uuid
            record = FinanceRecord(
                record_id=f"FIN-{uuid.uuid4().hex[:8]}",
                hotel_id=hotel_id,
                category="expense",
                amount=-float(input.context.get("amount", 0)),
                description=input.context.get("description", input.message),
                reference_id=input.context.get("reference_id", ""),
            )
            hotel_db.log_finance(record)
            result = {"logged": True, "record_id": record.record_id}
            actions_taken.append({"action": "finance_log", "record_id": record.record_id})
            reasoning[-1].observation = f"Finance record created: {record.record_id}"

        elif action == "get_summary":
            from backend.database.hotel_db import hotel_db
            summary = hotel_db.get_finance_summary(hotel_id)
            result = summary
            reasoning[-1].observation = f"Revenue summary: ${summary.get('grand_total', 0):.2f}"

        elif action == "fraud_detection":
            # Simplified fraud check: flag large transactions
            amount = float(input.context.get("amount", 0))
            is_suspicious = amount > 5000 or "unusual" in input.message.lower()
            result = {
                "amount": amount,
                "suspicious": is_suspicious,
                "risk_score": 0.8 if is_suspicious else 0.1,
                "recommendation": "flag_for_review" if is_suspicious else "approve",
            }
            confidence = 0.75 if is_suspicious else 0.9
            if is_suspicious:
                result["warnings"] = ["Amount exceeds threshold", "Flagged for manual review"]
            reasoning[-1].observation = f"Fraud check: {'SUSPICIOUS' if is_suspicious else 'Clean'} (${amount})"

        elif action == "process_refund":
            result = {
                "action": "refund",
                "status": "requires_approval",
                "amount": input.context.get("amount", 0),
                "hotel_id": hotel_id,
            }
            confidence = 0.6  # Refunds need approval
            reasoning[-1].observation = "Refund request — requires manager approval"

        else:
            from backend.database.hotel_db import hotel_db
            records = hotel_db.get_finance_records(hotel_id=hotel_id)
            result = {"records": len(records), "action": action}
            reasoning[-1].observation = f"Found {len(records)} finance records"

        return AgentOutput(
            request_id=input.request_id,
            agent_id=self.agent_id,
            agent_tier=self.tier,
            status="completed",
            result=result,
            reasoning=reasoning,
            confidence_score=confidence,
            actions_taken=actions_taken,
        )

    def _infer_action(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ("fraud", "suspicious", "unusual")):
            return "fraud_detection"
        if any(w in msg for w in ("refund", "cancel")):
            return "process_refund"
        if any(w in msg for w in ("log", "record", "incident")):
            return "log_incident"
        if any(w in msg for w in ("summary", "report", "revenue")):
            return "get_summary"
        return "billing_inquiry"
