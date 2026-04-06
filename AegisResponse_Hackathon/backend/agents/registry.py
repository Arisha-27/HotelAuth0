"""
Steps 46-47, 49, 53-55: Agent Registry & Multi-Agent Collaboration
Central registry for all agents with:
  - Agent isolation (Step 46): each agent gets its own scoped token
  - Scoped tokens per agent (Step 47)
  - OpenClaw skill boundaries (Step 49)
  - Multi-agent collaboration (Step 53)
  - Fallback agent logic (Step 54)
  - Execution tracing (Step 55)
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from backend.agents.base import (
    BaseAgent, AgentInput, AgentOutput, AgentTier,
    AgentMessage, AgentStatus, Confidence
)
from backend.agents.brain import create_brain, LLMBrain
from backend.agents.executive import ExecutiveAgent
from backend.agents.domain_agents import SecurityAgent, OperationsAgent, FinanceAgent
from backend.agents.sub_agents import (
    AccessControlAgent, HousekeepingAgent, BookingAgent, MaintenanceAgent
)
from backend.logging_config import get_logger

logger = get_logger("agents.registry")


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class AgentExecutionRequest(BaseModel):
    """Request to execute something via the agent system."""
    message: str = Field(..., description="Natural language instruction or task")
    hotel_id: str = Field(default="hotel-downtown")
    context: dict = Field(default_factory=dict)
    priority: str = Field(default="normal")
    target_agent: Optional[str] = Field(default=None, description="Direct dispatch to a specific agent (skip executive)")
    requires_approval: bool = False


class AgentExecutionResult(BaseModel):
    """Full result of an agent execution."""
    execution_id: str
    request: dict
    executive_output: Optional[dict] = None
    agent_outputs: list[dict] = Field(default_factory=list)
    status: str = "completed"
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    execution_time_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────
# Agent Registry
# ─────────────────────────────────────────────
class AgentRegistry:
    """
    Central registry and orchestrator for all agents.
    Manages agent lifecycle, token isolation, and multi-agent collaboration.
    """

    def __init__(self):
        self.brain: LLMBrain = create_brain()
        self._agents: dict[str, BaseAgent] = {}
        self._message_log: list[dict] = []
        self._execution_history: list[dict] = []
        self._init_agents()

    def _init_agents(self):
        """Initialize all agents with the shared brain."""
        # Executive (top of hierarchy)
        self._register(ExecutiveAgent(brain=self.brain))

        # Domain agents (mid-level)
        self._register(SecurityAgent(brain=self.brain))
        self._register(OperationsAgent(brain=self.brain))
        self._register(FinanceAgent(brain=self.brain))

        # Sub-agents (leaf-level)
        self._register(AccessControlAgent(brain=self.brain))
        self._register(HousekeepingAgent(brain=self.brain))
        self._register(BookingAgent(brain=self.brain))
        self._register(MaintenanceAgent(brain=self.brain))

        logger.info(f"Agent registry initialized: {len(self._agents)} agents")
        for agent_id, agent in self._agents.items():
            logger.info(f"  [{agent.tier.value:>10}] {agent_id}: {agent.agent_name} (scopes: {agent.scopes})")

    def _register(self, agent: BaseAgent):
        self._agents[agent.agent_id] = agent

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def list_agents(self) -> list[dict]:
        return [agent.get_status() for agent in self._agents.values()]

    def get_hierarchy(self) -> dict:
        """Get the agent hierarchy tree."""
        hierarchy = {"executive": [], "domain": [], "sub_agent": []}
        for agent in self._agents.values():
            hierarchy[agent.tier.value].append({
                "id": agent.agent_id,
                "name": agent.agent_name,
                "scopes": agent.scopes,
                "status": agent.status.value,
            })
        return hierarchy

    # ─── Step 53: Multi-Agent Collaboration ───
    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        """
        Main entry point for the agent system.
        If target_agent is specified, dispatches directly.
        Otherwise, routes through the Executive Agent for intent parsing + planning.
        """
        import time
        start = time.time()
        execution_id = f"exec-{uuid.uuid4().hex[:8]}"

        agent_input = AgentInput(
            message=request.message,
            hotel_id=request.hotel_id,
            context=request.context,
            priority=request.priority,
            requires_approval=request.requires_approval,
        )

        result = AgentExecutionResult(
            execution_id=execution_id,
            request=request.model_dump(),
        )

        try:
            if request.target_agent:
                # Direct dispatch to a specific agent
                output = await self._dispatch_to_agent(request.target_agent, agent_input)
                result.agent_outputs.append(output.model_dump())
                result.total_tasks = 1
                result.completed_tasks = 1 if output.status == "completed" else 0
                result.failed_tasks = 1 if output.status == "failed" else 0
            else:
                # Route through Executive Agent
                executive = self.get_agent("executive")
                exec_output = await executive.process(agent_input)
                result.executive_output = exec_output.model_dump()

                # Extract plan and execute tasks
                if exec_output.status == "completed" and exec_output.result:
                    plan = exec_output.result.get("plan", {})
                    tasks = plan.get("tasks", [])
                    result.total_tasks = len(tasks)

                    # Execute tasks respecting dependencies
                    await self._execute_task_plan(tasks, agent_input, result)

        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}")
            result.status = "failed"
            result.agent_outputs.append({"error": str(e), "agent": "system"})

        result.execution_time_ms = round((time.time() - start) * 1000, 2)
        result.status = "completed" if result.failed_tasks == 0 else "partial" if result.completed_tasks > 0 else "failed"

        # Log execution
        self._execution_history.append({
            "execution_id": execution_id,
            "message": request.message[:80],
            "hotel_id": request.hotel_id,
            "total_tasks": result.total_tasks,
            "completed": result.completed_tasks,
            "failed": result.failed_tasks,
            "status": result.status,
            "time_ms": result.execution_time_ms,
            "timestamp": result.timestamp,
        })
        if len(self._execution_history) > 200:
            self._execution_history = self._execution_history[-100:]

        logger.info(
            f"Execution {execution_id}: {result.status} "
            f"({result.completed_tasks}/{result.total_tasks} tasks, {result.execution_time_ms}ms)"
        )

        return result

    async def _execute_task_plan(self, tasks: list[dict], base_input: AgentInput, result: AgentExecutionResult):
        """Execute tasks from a plan, respecting dependency order."""
        completed_task_ids = set()
        task_map = {t.get("task_id", f"t{i}"): t for i, t in enumerate(tasks)}

        # Simple topological execution: process tasks whose deps are met
        max_iterations = len(tasks) * 2  # Safety limit
        iteration = 0

        while len(completed_task_ids) < len(tasks) and iteration < max_iterations:
            iteration += 1
            batch = []

            for tid, task in task_map.items():
                if tid in completed_task_ids:
                    continue
                deps = task.get("depends_on", [])
                if all(d in completed_task_ids for d in deps):
                    batch.append((tid, task))

            if not batch:
                break  # No more tasks can run (deadlock or done)

            # Execute batch concurrently
            for tid, task in batch:
                agent_id = task.get("agent", "operations")
                task_input = AgentInput(
                    message=task.get("description", ""),
                    hotel_id=base_input.hotel_id,
                    context={
                        "action": task.get("action", "handle_request"),
                        **task.get("parameters", {}),
                        **base_input.context,
                    },
                    priority=base_input.priority,
                    source_agent="executive",
                    requires_approval=task.get("requires_approval", False),
                )

                try:
                    output = await self._dispatch_to_agent(agent_id, task_input)
                    result.agent_outputs.append({
                        "task_id": tid,
                        "agent": agent_id,
                        "action": task.get("action"),
                        **output.model_dump(),
                    })
                    if output.status == "completed":
                        result.completed_tasks += 1
                    else:
                        result.failed_tasks += 1
                except Exception as e:
                    logger.error(f"Task {tid} failed: {e}")
                    result.agent_outputs.append({"task_id": tid, "agent": agent_id, "status": "failed", "error": str(e)})
                    result.failed_tasks += 1

                completed_task_ids.add(tid)

    # ─── Step 54: Fallback Agent Logic ───
    async def _dispatch_to_agent(self, agent_id: str, input: AgentInput) -> AgentOutput:
        """Dispatch to an agent with fallback if the target is unavailable."""
        agent = self.get_agent(agent_id)

        if not agent:
            # Fallback: try to find a suitable agent
            logger.warning(f"Agent '{agent_id}' not found, trying fallback")
            fallback_map = {
                "access_control": "security",
                "housekeeping": "operations",
                "booking": "operations",
                "maintenance": "operations",
            }
            fallback_id = fallback_map.get(agent_id, "operations")
            agent = self.get_agent(fallback_id)
            if not agent:
                raise ValueError(f"No agent available for '{agent_id}' (fallback '{fallback_id}' also missing)")
            logger.info(f"Falling back from '{agent_id}' to '{fallback_id}'")

        if agent.status == AgentStatus.ERROR:
            logger.warning(f"Agent '{agent_id}' in error state, attempting anyway")

        return await agent.process(input)

    # ─── Queries ───
    def get_execution_history(self, limit: int = 20) -> list[dict]:
        return self._execution_history[-limit:]

    def get_agent_trace(self, agent_id: str, limit: int = 20) -> list[dict]:
        agent = self.get_agent(agent_id)
        return agent.get_execution_trace(limit) if agent else []

    def get_brain_info(self) -> dict:
        return self.brain.get_info()


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────
agent_registry = AgentRegistry()
