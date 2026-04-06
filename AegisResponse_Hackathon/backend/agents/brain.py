"""
Steps 37-39: Pluggable LLM Brain Abstraction
The brain is the reasoning engine — completely provider-agnostic.
Swap between OpenAI, Gemini, Mistral, local LLMs, or a mock with ONE config change.

Includes:
  - LLMBrain abstract interface
  - MockBrain for hackathon/testing (no API keys needed)
  - HTTPBrain for any OpenAI-compatible API
  - Task planning via structured prompts
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("ahos.agents.brain")


# ─────────────────────────────────────────────
# Brain Response Model
# ─────────────────────────────────────────────
class BrainResponse(BaseModel):
    """Standardized response from any LLM brain."""
    content: str = ""
    structured_data: Optional[dict] = None  # Parsed JSON if applicable
    model: str = "unknown"
    provider: str = "unknown"
    usage: dict = Field(default_factory=dict)  # token counts
    latency_ms: float = 0.0
    raw_response: Optional[dict] = None


# ─────────────────────────────────────────────
# Step 38: Task Graph Schema
# ─────────────────────────────────────────────
class TaskNode(BaseModel):
    """A single node in a task graph produced by the brain."""
    task_id: str
    agent: str  # target agent: "security", "operations", "finance"
    action: str
    description: str
    parameters: dict = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    priority: int = Field(default=5, ge=1, le=10)
    requires_approval: bool = False


class TaskPlan(BaseModel):
    """Step 38-39: A complete task graph produced by the brain."""
    plan_id: str
    intent: str
    reasoning: str
    tasks: list[TaskNode]
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────
# Brain Interface (Abstract)
# ─────────────────────────────────────────────
class LLMBrain(ABC):
    """
    Abstract LLM brain interface. All implementations must provide:
      - think(): free-form reasoning
      - parse_intent(): extract structured intent from natural language
      - plan_tasks(): decompose intent into a task graph
    """

    @abstractmethod
    async def think(self, prompt: str, system_prompt: str = "", context: dict = None) -> BrainResponse:
        """General-purpose reasoning call."""
        ...

    @abstractmethod
    async def parse_intent(self, user_message: str, hotel_context: dict = None) -> dict:
        """Parse user/agent message into a structured intent."""
        ...

    @abstractmethod
    async def plan_tasks(self, intent: dict, available_agents: list[str], hotel_context: dict = None) -> TaskPlan:
        """Step 39: Decompose an intent into an executable task graph."""
        ...

    @abstractmethod
    def get_info(self) -> dict:
        """Return provider info."""
        ...


# ─────────────────────────────────────────────
# MockBrain — No API keys needed
# ─────────────────────────────────────────────
class MockBrain(LLMBrain):
    """
    Simulated LLM brain for development and hackathon demos.
    Uses rule-based logic to simulate intent parsing and task planning.
    No API keys or network calls needed.
    """

    INTENT_PATTERNS = {
        "fire": {"intent": "fire_emergency", "domain": "security", "priority": 10, "approval": False},
        "smoke": {"intent": "fire_emergency", "domain": "security", "priority": 10, "approval": False},
        "unlock": {"intent": "door_unlock", "domain": "security", "priority": 8, "approval": True},
        "door": {"intent": "door_unlock", "domain": "security", "priority": 8, "approval": True},
        "security": {"intent": "security_alert", "domain": "security", "priority": 9, "approval": False},
        "breach": {"intent": "security_breach", "domain": "security", "priority": 10, "approval": False},
        "guest": {"intent": "guest_service", "domain": "operations", "priority": 5, "approval": False},
        "booking": {"intent": "manage_booking", "domain": "operations", "priority": 5, "approval": False},
        "checkout": {"intent": "guest_checkout", "domain": "operations", "priority": 6, "approval": False},
        "checkin": {"intent": "guest_checkin", "domain": "operations", "priority": 6, "approval": False},
        "maintenance": {"intent": "maintenance_request", "domain": "operations", "priority": 4, "approval": False},
        "housekeeping": {"intent": "housekeeping_request", "domain": "operations", "priority": 3, "approval": False},
        "billing": {"intent": "billing_inquiry", "domain": "finance", "priority": 4, "approval": False},
        "refund": {"intent": "process_refund", "domain": "finance", "priority": 6, "approval": True},
        "fraud": {"intent": "fraud_detection", "domain": "finance", "priority": 9, "approval": False},
        "notify": {"intent": "send_notification", "domain": "operations", "priority": 5, "approval": False},
        "vip": {"intent": "vip_service", "domain": "operations", "priority": 7, "approval": False},
        "emergency": {"intent": "general_emergency", "domain": "security", "priority": 10, "approval": False},
    }

    TASK_TEMPLATES = {
        "fire_emergency": [
            TaskNode(task_id="t1", agent="security", action="trigger_fire_alarm", description="Trigger fire alarms on affected floor", parameters={"protocol": "fire"}, priority=10),
            TaskNode(task_id="t2", agent="security", action="unlock_floor", description="Emergency unlock all doors on affected floor", parameters={"mode": "emergency"}, priority=10, depends_on=["t1"]),
            TaskNode(task_id="t3", agent="operations", action="notify_guests", description="Send emergency evacuation notifications", parameters={"type": "evacuation"}, priority=9, depends_on=["t1"]),
            TaskNode(task_id="t4", agent="operations", action="notify_staff", description="Alert all staff and emergency contacts", parameters={"type": "emergency_staff"}, priority=9, depends_on=["t1"]),
            TaskNode(task_id="t5", agent="finance", action="log_incident", description="Log fire incident for insurance", parameters={"category": "fire"}, priority=3, depends_on=["t2"]),
        ],
        "door_unlock": [
            TaskNode(task_id="t1", agent="security", action="verify_authorization", description="Verify unlock authorization", priority=8),
            TaskNode(task_id="t2", agent="security", action="unlock_door", description="Execute door unlock command", priority=8, requires_approval=True, depends_on=["t1"]),
            TaskNode(task_id="t3", agent="finance", action="log_access", description="Log access event for audit", priority=2, depends_on=["t2"]),
        ],
        "security_breach": [
            TaskNode(task_id="t1", agent="security", action="lockdown_area", description="Initiate lockdown of affected area", priority=10),
            TaskNode(task_id="t2", agent="security", action="activate_cameras", description="Activate all security cameras", priority=9, depends_on=["t1"]),
            TaskNode(task_id="t3", agent="operations", action="notify_security_team", description="Alert security personnel", priority=9, depends_on=["t1"]),
            TaskNode(task_id="t4", agent="finance", action="log_incident", description="Log security incident", priority=3, depends_on=["t1"]),
        ],
        "guest_checkin": [
            TaskNode(task_id="t1", agent="operations", action="verify_reservation", description="Verify guest reservation", priority=6),
            TaskNode(task_id="t2", agent="operations", action="assign_room", description="Assign and prepare room", priority=6, depends_on=["t1"]),
            TaskNode(task_id="t3", agent="security", action="issue_keycard", description="Generate keycard access", priority=5, depends_on=["t2"]),
            TaskNode(task_id="t4", agent="operations", action="welcome_notification", description="Send welcome message to guest", priority=3, depends_on=["t2"]),
        ],
        "vip_service": [
            TaskNode(task_id="t1", agent="operations", action="check_vip_preferences", description="Load VIP guest preferences", priority=7),
            TaskNode(task_id="t2", agent="operations", action="prepare_room", description="Prepare room per VIP preferences", priority=7, depends_on=["t1"]),
            TaskNode(task_id="t3", agent="operations", action="arrange_amenities", description="Arrange special amenities", priority=6, depends_on=["t1"]),
            TaskNode(task_id="t4", agent="operations", action="notify_staff", description="Brief staff on VIP arrival", priority=5, depends_on=["t1"]),
        ],
        "process_refund": [
            TaskNode(task_id="t1", agent="finance", action="verify_booking", description="Verify original booking and payment", priority=6),
            TaskNode(task_id="t2", agent="finance", action="calculate_refund", description="Calculate refund amount", priority=6, depends_on=["t1"]),
            TaskNode(task_id="t3", agent="finance", action="process_refund", description="Process refund to payment method", priority=7, requires_approval=True, depends_on=["t2"]),
            TaskNode(task_id="t4", agent="operations", action="notify_guest", description="Notify guest of refund status", priority=4, depends_on=["t3"]),
        ],
    }

    async def think(self, prompt: str, system_prompt: str = "", context: dict = None) -> BrainResponse:
        import time
        start = time.time()
        # Simple rule-based reasoning
        response_text = f"[MockBrain] Analyzed: '{prompt[:80]}...'\n"
        if context:
            response_text += f"Context: hotel={context.get('hotel_id', 'unknown')}\n"
        response_text += "Assessment: Task identified and ready for execution."

        return BrainResponse(
            content=response_text,
            model="mock-brain-v1",
            provider="mock",
            usage={"prompt_tokens": len(prompt.split()), "completion_tokens": 20},
            latency_ms=round((time.time() - start) * 1000, 2),
        )

    async def parse_intent(self, user_message: str, hotel_context: dict = None) -> dict:
        msg_lower = user_message.lower()
        matched_intent = None
        highest_priority = 0

        for keyword, intent_data in self.INTENT_PATTERNS.items():
            if keyword in msg_lower and intent_data["priority"] > highest_priority:
                matched_intent = intent_data
                highest_priority = intent_data["priority"]

        if not matched_intent:
            matched_intent = {"intent": "general_inquiry", "domain": "operations", "priority": 3, "approval": False}

        return {
            "intent": matched_intent["intent"],
            "domain": matched_intent["domain"],
            "priority": matched_intent["priority"],
            "requires_approval": matched_intent["approval"],
            "original_message": user_message,
            "hotel_id": (hotel_context or {}).get("hotel_id", "HQ"),
            "confidence": 0.85 if matched_intent["intent"] != "general_inquiry" else 0.5,
        }

    async def plan_tasks(self, intent: dict, available_agents: list[str], hotel_context: dict = None) -> TaskPlan:
        intent_type = intent.get("intent", "general_inquiry")
        hotel_id = intent.get("hotel_id", "HQ")

        # Get matching task template or create a generic one
        if intent_type in self.TASK_TEMPLATES:
            tasks = [t.model_copy() for t in self.TASK_TEMPLATES[intent_type]]
        else:
            tasks = [
                TaskNode(
                    task_id="t1",
                    agent=intent.get("domain", "operations"),
                    action="handle_request",
                    description=f"Handle {intent_type} request",
                    parameters={"original_message": intent.get("original_message", "")},
                    priority=intent.get("priority", 5),
                ),
            ]

        # Inject hotel context into all tasks
        for task in tasks:
            task.parameters["hotel_id"] = hotel_id

        reasoning = (
            f"Intent '{intent_type}' parsed from input. "
            f"Decomposed into {len(tasks)} tasks across "
            f"{len(set(t.agent for t in tasks))} domain(s). "
            f"Execution order respects dependency graph."
        )

        return TaskPlan(
            plan_id=f"plan-{intent_type}-{uuid.uuid4().hex[:6]}",
            intent=intent_type,
            reasoning=reasoning,
            tasks=tasks,
            confidence=intent.get("confidence", 0.85),
        )

    def get_info(self) -> dict:
        return {
            "provider": "mock",
            "model": "mock-brain-v1",
            "description": "Rule-based mock brain for development. No API keys needed.",
            "supported_intents": list(self.INTENT_PATTERNS.keys()),
            "task_templates": list(self.TASK_TEMPLATES.keys()),
        }


# ─────────────────────────────────────────────
# HTTPBrain — Any OpenAI-compatible API
# ─────────────────────────────────────────────
class HTTPBrain(LLMBrain):
    """
    Generic HTTP brain for any OpenAI-compatible API:
      - OpenAI (GPT-4o, etc.)
      - Google Gemini (via OpenAI compat)
      - Mistral
      - Ollama (local)
      - Any vLLM / LiteLLM endpoint

    Set via env:
      LLM_API_BASE=https://api.openai.com/v1  (or any compat endpoint)
      LLM_API_KEY=sk-...
      LLM_MODEL=gpt-4o-mini
    """

    def __init__(
        self,
        api_base: str = None,
        api_key: str = None,
        model: str = None,
        provider_name: str = "openai-compatible",
    ):
        self.api_base = (api_base or os.getenv("LLM_API_BASE", "")).rstrip("/")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.provider_name = provider_name

    @property
    def is_configured(self) -> bool:
        return bool(self.api_base and self.api_key)

    async def _call_api(self, messages: list[dict], temperature: float = 0.3, max_tokens: int = 1024) -> BrainResponse:
        import httpx, time
        start = time.time()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.api_base}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return BrainResponse(
            content=content,
            model=self.model,
            provider=self.provider_name,
            usage=usage,
            latency_ms=round((time.time() - start) * 1000, 2),
            raw_response=data,
        )

    async def think(self, prompt: str, system_prompt: str = "", context: dict = None) -> BrainResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            messages.append({"role": "system", "content": f"Context: {json.dumps(context)}"})
        messages.append({"role": "user", "content": prompt})
        return await self._call_api(messages)

    async def parse_intent(self, user_message: str, hotel_context: dict = None) -> dict:
        system_prompt = (
            "You are an AI intent parser for a hotel management system. "
            "Parse the user message into a structured JSON with fields: "
            "intent, domain (security/operations/finance), priority (1-10), "
            "requires_approval (bool), confidence (0-1). "
            "Respond ONLY with valid JSON, no markdown."
        )
        context_str = f"\nHotel context: {json.dumps(hotel_context)}" if hotel_context else ""
        resp = await self.think(user_message + context_str, system_prompt)
        try:
            return json.loads(resp.content)
        except json.JSONDecodeError:
            return {"intent": "general_inquiry", "domain": "operations", "priority": 3, "confidence": 0.3}

    async def plan_tasks(self, intent: dict, available_agents: list[str], hotel_context: dict = None) -> TaskPlan:
        import uuid
        system_prompt = (
            "You are a task planner for a hotel management AI system. "
            f"Available agents: {available_agents}. "
            "Decompose the intent into a list of tasks. "
            "Respond ONLY with valid JSON matching this schema: "
            '{"tasks": [{"task_id": "t1", "agent": "...", "action": "...", '
            '"description": "...", "depends_on": [], "priority": 5, "requires_approval": false}],'
            '"reasoning": "...", "confidence": 0.9}'
        )
        resp = await self.think(f"Plan tasks for intent: {json.dumps(intent)}", system_prompt, hotel_context)
        try:
            data = json.loads(resp.content)
            tasks = [TaskNode(**t) for t in data.get("tasks", [])]
            return TaskPlan(
                plan_id=f"plan-{uuid.uuid4().hex[:6]}",
                intent=intent.get("intent", "unknown"),
                reasoning=data.get("reasoning", ""),
                tasks=tasks,
                confidence=data.get("confidence", 0.7),
            )
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse task plan from LLM: {e}")
            return TaskPlan(
                plan_id=f"plan-fallback-{uuid.uuid4().hex[:6]}",
                intent=intent.get("intent", "unknown"),
                reasoning=f"LLM plan parsing failed: {e}",
                tasks=[],
                confidence=0.1,
                warnings=[f"Plan generation failed: {e}"],
            )

    def get_info(self) -> dict:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "api_base": self.api_base[:30] + "..." if self.api_base else "not set",
            "configured": self.is_configured,
        }


# ─────────────────────────────────────────────
# Brain Factory
# ─────────────────────────────────────────────
def create_brain(provider: str = None) -> LLMBrain:
    """
    Factory: create the appropriate brain based on config.
    Set LLM_PROVIDER env var to: 'mock', 'openai', 'gemini', 'ollama', etc.
    Defaults to MockBrain if no provider is configured.
    """
    provider = provider or os.getenv("LLM_PROVIDER", "mock")

    if provider == "mock":
        logger.info("Brain: Using MockBrain (no API keys needed)")
        return MockBrain()

    if provider in ("openai", "gemini", "mistral", "ollama", "custom"):
        api_base = os.getenv("LLM_API_BASE", "")
        if not api_base:
            defaults = {
                "openai": "https://api.openai.com/v1",
                "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
                "mistral": "https://api.mistral.ai/v1",
                "ollama": "http://localhost:11434/v1",
            }
            api_base = defaults.get(provider, "")
            os.environ["LLM_API_BASE"] = api_base

        brain = HTTPBrain(api_base=api_base, provider_name=provider)
        if brain.is_configured:
            logger.info(f"Brain: Using HTTPBrain ({provider}, model={brain.model})")
            return brain
        else:
            logger.warning(f"Brain: {provider} not fully configured, falling back to MockBrain")
            return MockBrain()

    logger.warning(f"Brain: Unknown provider '{provider}', using MockBrain")
    return MockBrain()


# Default brain singleton
import uuid
default_brain = create_brain()
