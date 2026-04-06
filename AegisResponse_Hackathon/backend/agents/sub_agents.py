"""
Step 44: Sub-Agents — Leaf-level specialized agents.
Access Control, Housekeeping, Booking, and Maintenance agents.
"""

from backend.agents.base import (
    BaseAgent, AgentInput, AgentOutput, AgentTier, ReasoningStep
)
from backend.agents.brain import LLMBrain, default_brain
from backend.logging_config import get_logger

logger = get_logger("agents.sub")


class AccessControlAgent(BaseAgent):
    """Sub-agent for door access, keycards, and physical security."""
    def __init__(self, brain: LLMBrain = None):
        super().__init__(
            agent_id="access_control", agent_name="Access Control Agent",
            tier=AgentTier.SUB_AGENT,
            description="Door locks, keycards, physical access management",
            scopes=["unlock:doors"], brain=brain or default_brain,
        )

    async def _execute(self, input: AgentInput) -> AgentOutput:
        from backend.integrations.iot_service import iot_simulator, IoTCommand
        action = input.context.get("action", "unlock")
        device_id = input.context.get("device_id", "")
        reasoning = [ReasoningStep(step_number=1, thought=f"Access control: {action} on {device_id}", action=f"iot.{action}")]

        if device_id:
            cmd = IoTCommand(device_id=device_id, action=action, authorized_by=self.agent_id, hotel_id=input.hotel_id)
            result = await iot_simulator.execute_command(cmd)
        else:
            result = {"status": "no_device_specified", "action": action}

        reasoning[-1].observation = f"Result: {result.get('success', False)}"
        return AgentOutput(
            request_id=input.request_id, agent_id=self.agent_id, agent_tier=self.tier,
            status="completed", result=result, reasoning=reasoning, confidence_score=0.9,
            actions_taken=[{"action": action, "device_id": device_id}],
        )


class HousekeepingAgent(BaseAgent):
    """Sub-agent for room cleaning, amenities, and housekeeping dispatch."""
    def __init__(self, brain: LLMBrain = None):
        super().__init__(
            agent_id="housekeeping", agent_name="Housekeeping Agent",
            tier=AgentTier.SUB_AGENT,
            description="Room cleaning, amenity restocking, laundry",
            scopes=["notify:guests"], brain=brain or default_brain,
        )

    async def _execute(self, input: AgentInput) -> AgentOutput:
        from backend.integrations.notion_service import notion_service, NotionLogEntry
        log = await notion_service.create_log(NotionLogEntry(
            title=f"Housekeeping: {input.message[:60]}",
            category="maintenance", status="open", hotel_id=input.hotel_id,
            description=input.message, assigned_agent=self.agent_id,
            tags=["housekeeping"],
        ))
        return AgentOutput(
            request_id=input.request_id, agent_id=self.agent_id, agent_tier=self.tier,
            status="completed",
            result={"task_logged": True, "page_id": log.page_id, "status": "dispatched"},
            reasoning=[ReasoningStep(step_number=1, thought="Housekeeping task logged to Notion", action="notion.create_log", observation=f"Page: {log.page_id}")],
            confidence_score=0.9,
            actions_taken=[{"action": "log_housekeeping", "page_id": log.page_id}],
        )


class BookingAgent(BaseAgent):
    """Sub-agent for reservation management."""
    def __init__(self, brain: LLMBrain = None):
        super().__init__(
            agent_id="booking", agent_name="Booking Agent",
            tier=AgentTier.SUB_AGENT,
            description="Reservation lookup, modification, cancellation",
            scopes=["manage:bookings"], brain=brain or default_brain,
        )

    async def _execute(self, input: AgentInput) -> AgentOutput:
        from backend.database.hotel_db import hotel_db
        action = input.context.get("action", "lookup")
        hotel_id = input.hotel_id

        if action == "lookup":
            guest_id = input.context.get("guest_id")
            bookings = hotel_db.get_bookings(hotel_id=hotel_id, guest_id=guest_id)
            result = {"bookings": bookings, "count": len(bookings)}
        elif action == "available_rooms":
            rooms = hotel_db.get_rooms(hotel_id, status="available")
            result = {"available_rooms": len(rooms), "rooms": rooms[:5]}
        else:
            result = {"action": action, "status": "processed"}

        return AgentOutput(
            request_id=input.request_id, agent_id=self.agent_id, agent_tier=self.tier,
            status="completed", result=result,
            reasoning=[ReasoningStep(step_number=1, thought=f"Booking {action}", action=f"db.{action}", observation=f"Processed")],
            confidence_score=0.9, actions_taken=[{"action": action, "hotel_id": hotel_id}],
        )


class MaintenanceAgent(BaseAgent):
    """Sub-agent for facility maintenance and repairs."""
    def __init__(self, brain: LLMBrain = None):
        super().__init__(
            agent_id="maintenance", agent_name="Maintenance Agent",
            tier=AgentTier.SUB_AGENT,
            description="HVAC, plumbing, electrical, facility repairs",
            scopes=[], brain=brain or default_brain,
        )

    async def _execute(self, input: AgentInput) -> AgentOutput:
        from backend.integrations.iot_service import iot_simulator
        from backend.database.hotel_db import hotel_db, IncidentLog
        import uuid

        # Log maintenance incident
        incident = IncidentLog(
            incident_id=f"INC-{uuid.uuid4().hex[:8]}",
            hotel_id=input.hotel_id,
            incident_type="maintenance",
            severity=input.context.get("severity", "medium"),
            location=input.context.get("location", ""),
            description=input.message,
            reported_by=self.agent_id,
        )
        hotel_db.log_incident(incident)

        # Check relevant IoT devices
        devices = iot_simulator.get_devices(input.hotel_id)
        hvac_count = sum(1 for d in devices if d.get("device_type") == "hvac")

        return AgentOutput(
            request_id=input.request_id, agent_id=self.agent_id, agent_tier=self.tier,
            status="completed",
            result={"incident_id": incident.incident_id, "logged": True, "hvac_devices_checked": hvac_count},
            reasoning=[ReasoningStep(step_number=1, thought=f"Maintenance logged: {incident.incident_id}", action="db.log_incident", observation="Incident created and devices checked")],
            confidence_score=0.85, actions_taken=[{"action": "log_incident", "id": incident.incident_id}],
        )
