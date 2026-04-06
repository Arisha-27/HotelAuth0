"""
Step 36: Agent Interfaces — Base classes for the hierarchical agent system.
Defines the input → reasoning → output contract that all agents must follow.
Every agent is LLM-agnostic: the 'brain' is injected, not hardcoded.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.logging_config import get_logger

logger = get_logger("agents.base")


# ─────────────────────────────────────────────
# Agent Enums
# ─────────────────────────────────────────────
class AgentTier(str, Enum):
    """Hierarchy level of an agent."""
    EXECUTIVE = "executive"      # Top-level: intent parsing, task planning
    DOMAIN = "domain"            # Mid-level: security, operations, finance
    SUB_AGENT = "sub_agent"      # Leaf-level: access control, housekeeping, etc.


class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"


class Confidence(str, Enum):
    """Step 52: Agent confidence levels for action decisions."""
    HIGH = "high"          # > 0.8  — proceed autonomously
    MEDIUM = "medium"      # 0.5–0.8  — proceed with logging
    LOW = "low"            # 0.2–0.5  — request human review
    UNCERTAIN = "uncertain"  # < 0.2  — refuse to act


# ─────────────────────────────────────────────
# Agent Input / Output Models
# ─────────────────────────────────────────────
class AgentInput(BaseModel):
    """Standardized input to any agent."""
    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:10]}")
    message: str = Field(..., description="Natural language or structured instruction")
    context: dict = Field(default_factory=dict, description="Contextual data (hotel_id, guest_info, etc.)")
    hotel_id: str = Field(default="HQ")
    priority: str = Field(default="normal")
    source_agent: Optional[str] = Field(default=None, description="Agent that delegated this task")
    requires_approval: bool = Field(default=False)
    metadata: dict = Field(default_factory=dict)


class ReasoningStep(BaseModel):
    """A single step in the agent's chain-of-thought."""
    step_number: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentOutput(BaseModel):
    """Standardized output from any agent."""
    request_id: str
    agent_id: str
    agent_tier: AgentTier
    status: str = "completed"  # completed, failed, delegated, awaiting_approval
    result: Any = None
    reasoning: list[ReasoningStep] = Field(default_factory=list)
    confidence: Confidence = Confidence.HIGH
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    delegated_to: Optional[str] = None
    actions_taken: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    execution_time_ms: float = 0.0


# ─────────────────────────────────────────────
# Step 45: Agent Communication Protocol (JSON-RPC style)
# ─────────────────────────────────────────────
class AgentMessage(BaseModel):
    """Inter-agent communication message (JSON-RPC inspired)."""
    message_id: str = Field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:10]}")
    from_agent: str
    to_agent: str
    method: str  # e.g., "execute_task", "request_info", "report_status"
    params: dict = Field(default_factory=dict)
    reply_to: Optional[str] = None  # message_id of the message this replies to
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────
# Step 48: Agent Memory (short-term context)
# ─────────────────────────────────────────────
class AgentMemory:
    """Short-term memory for an agent — stores recent interactions and context."""

    def __init__(self, max_entries: int = 50):
        self.max_entries = max_entries
        self._entries: list[dict] = []
        self._facts: dict[str, Any] = {}

    def remember(self, key: str, value: Any):
        """Store a fact in memory."""
        self._facts[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        """Recall a stored fact."""
        return self._facts.get(key, default)

    def add_interaction(self, role: str, content: str, metadata: dict = None):
        """Add an interaction to the conversation history."""
        self._entries.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]

    def get_history(self, last_n: int = 10) -> list[dict]:
        """Get recent interaction history."""
        return self._entries[-last_n:]

    def get_context_summary(self) -> dict:
        """Get a summary of current agent context."""
        return {
            "facts": self._facts.copy(),
            "history_length": len(self._entries),
            "recent_topics": [e.get("content", "")[:80] for e in self._entries[-3:]],
        }

    def clear(self):
        self._entries.clear()
        self._facts.clear()


# ─────────────────────────────────────────────
# Step 36: Base Agent Abstract Class
# ─────────────────────────────────────────────
class BaseAgent(ABC):
    """
    Abstract base class for all AHOS agents.
    Implements the input → reasoning → output pipeline.
    The LLM 'brain' is injected via the constructor — no hardcoded provider.
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        tier: AgentTier,
        description: str = "",
        scopes: list[str] = None,
        brain=None,  # LLMBrain instance — injected, not hardcoded
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.tier = tier
        self.description = description
        self.scopes = scopes or []
        self.brain = brain
        self.status = AgentStatus.IDLE
        self.memory = AgentMemory()
        self._execution_trace: list[dict] = []
        self._total_executions = 0
        self._total_errors = 0

        logger.info(f"Agent initialized: {agent_id} ({tier.value}) — brain={'connected' if brain else 'none'}")

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Main processing pipeline: input → reasoning → output.
        Step 55: Full execution tracing built in.
        """
        import time
        start = time.time()
        self.status = AgentStatus.THINKING
        self._total_executions += 1

        trace_entry = {
            "request_id": input.request_id,
            "agent_id": self.agent_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "input_summary": input.message[:100],
        }

        try:
            # Store input in memory
            self.memory.add_interaction("user", input.message, {"request_id": input.request_id})

            # Step 50: Apply system prompt constraints
            self._enforce_system_constraints(input)

            # Step 51: Hallucination guard
            self._apply_hallucination_guards(input)

            # Execute agent-specific logic
            self.status = AgentStatus.EXECUTING
            output = await self._execute(input)

            # Step 52: Compute confidence
            output = self._compute_confidence(output)

            # Check if approval is needed
            if input.requires_approval or output.confidence == Confidence.LOW:
                output.status = "awaiting_approval"
                self.status = AgentStatus.WAITING_APPROVAL

            # Store output in memory
            self.memory.add_interaction(
                "agent",
                str(output.result)[:200] if output.result else "No result",
                {"confidence": output.confidence_score},
            )

            output.execution_time_ms = round((time.time() - start) * 1000, 2)
            self.status = AgentStatus.IDLE

            trace_entry["status"] = output.status
            trace_entry["confidence"] = output.confidence_score
            trace_entry["execution_ms"] = output.execution_time_ms
            self._execution_trace.append(trace_entry)

            logger.info(
                f"[{self.agent_id}] Completed: {output.status} "
                f"(confidence={output.confidence_score:.2f}, {output.execution_time_ms}ms)"
            )
            return output

        except Exception as e:
            self.status = AgentStatus.ERROR
            self._total_errors += 1
            trace_entry["status"] = "error"
            trace_entry["error"] = str(e)
            self._execution_trace.append(trace_entry)

            logger.error(f"[{self.agent_id}] Error: {e}")
            return AgentOutput(
                request_id=input.request_id,
                agent_id=self.agent_id,
                agent_tier=self.tier,
                status="failed",
                result={"error": str(e)},
                confidence=Confidence.UNCERTAIN,
                confidence_score=0.0,
                execution_time_ms=round((time.time() - start) * 1000, 2),
            )

    @abstractmethod
    async def _execute(self, input: AgentInput) -> AgentOutput:
        """Agent-specific execution logic. Override in subclasses."""
        ...

    # ─── Step 50: System Prompt Constraints ───
    def _enforce_system_constraints(self, input: AgentInput):
        """Ensure the agent operates within its defined boundaries."""
        # Agents cannot operate outside their scoped hotel
        if input.hotel_id and self.memory.recall("restricted_hotels"):
            restricted = self.memory.recall("restricted_hotels")
            if input.hotel_id not in restricted:
                raise PermissionError(f"Agent {self.agent_id} not authorized for hotel {input.hotel_id}")

    # ─── Step 51: Hallucination Guards ───
    def _apply_hallucination_guards(self, input: AgentInput):
        """Prevent the agent from hallucinating actions outside its scope."""
        dangerous_patterns = [
            "delete all", "drop table", "transfer funds", "override security",
            "disable authentication", "bypass", "sudo", "rm -rf",
        ]
        msg_lower = input.message.lower()
        for pattern in dangerous_patterns:
            if pattern in msg_lower:
                raise ValueError(
                    f"Hallucination guard triggered: '{pattern}' detected in input. "
                    f"Agent {self.agent_id} refusing to process."
                )

    # ─── Step 52: Confidence Scoring ───
    def _compute_confidence(self, output: AgentOutput) -> AgentOutput:
        """Assign confidence level based on score."""
        score = output.confidence_score
        if score >= 0.8:
            output.confidence = Confidence.HIGH
        elif score >= 0.5:
            output.confidence = Confidence.MEDIUM
        elif score >= 0.2:
            output.confidence = Confidence.LOW
            output.warnings.append(f"Low confidence ({score:.2f}) — human review recommended")
        else:
            output.confidence = Confidence.UNCERTAIN
            output.warnings.append(f"Uncertain ({score:.2f}) — agent refusing autonomous action")
        return output

    # ─── Step 55: Execution Tracing ───
    def get_execution_trace(self, limit: int = 20) -> list[dict]:
        return self._execution_trace[-limit:]

    def get_status(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.agent_name,
            "tier": self.tier.value,
            "status": self.status.value,
            "brain": "connected" if self.brain else "none",
            "scopes": self.scopes,
            "total_executions": self._total_executions,
            "total_errors": self._total_errors,
            "memory_facts": len(self.memory._facts),
            "memory_history": len(self.memory._entries),
        }
