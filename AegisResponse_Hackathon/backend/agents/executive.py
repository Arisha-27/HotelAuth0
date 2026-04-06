"""
Step 37: Executive Agent — Claude/LLM-driven top-level orchestrator.
Uses the pluggable brain for intent parsing and task decomposition.
Delegates to domain agents via the agent registry.
"""

from backend.agents.base import (
    BaseAgent, AgentInput, AgentOutput, AgentTier, ReasoningStep,
    AgentMessage, Confidence
)
from backend.agents.brain import LLMBrain, default_brain
from backend.logging_config import get_logger

logger = get_logger("agents.executive")


class ExecutiveAgent(BaseAgent):
    """
    Top of the hierarchy. Receives natural language requests,
    parses intent via the LLM brain, builds task plans,
    and dispatches to domain agents.
    """

    def __init__(self, brain: LLMBrain = None):
        super().__init__(
            agent_id="executive",
            agent_name="Executive Agent",
            tier=AgentTier.EXECUTIVE,
            description="Top-level orchestrator: intent parsing, task decomposition, delegation",
            scopes=["unlock:doors", "notify:guests", "manage:bookings", "read:finance"],
            brain=brain or default_brain,
        )

    async def _execute(self, input: AgentInput) -> AgentOutput:
        reasoning = []

        # Step 1: Parse intent
        reasoning.append(ReasoningStep(
            step_number=1,
            thought=f"Parsing intent from: '{input.message[:80]}'",
            action="brain.parse_intent",
        ))

        intent = await self.brain.parse_intent(
            input.message,
            hotel_context={"hotel_id": input.hotel_id, **input.context},
        )

        reasoning[-1].observation = f"Intent: {intent.get('intent')} (confidence: {intent.get('confidence', 0)})"

        # Step 2: Plan tasks
        reasoning.append(ReasoningStep(
            step_number=2,
            thought=f"Decomposing intent '{intent.get('intent')}' into executable task graph",
            action="brain.plan_tasks",
        ))

        available_agents = ["security", "operations", "finance"]
        plan = await self.brain.plan_tasks(intent, available_agents, {"hotel_id": input.hotel_id})

        reasoning[-1].observation = f"Plan: {len(plan.tasks)} tasks across {len(set(t.agent for t in plan.tasks))} domains"

        # Step 3: Assess and decide
        reasoning.append(ReasoningStep(
            step_number=3,
            thought=f"Assessing plan confidence: {plan.confidence:.2f}",
            action="evaluate_plan",
            observation=f"Plan '{plan.plan_id}' ready for execution. Warnings: {plan.warnings or 'none'}",
        ))

        # Store in memory
        self.memory.remember("last_intent", intent)
        self.memory.remember("last_plan", plan.model_dump())

        return AgentOutput(
            request_id=input.request_id,
            agent_id=self.agent_id,
            agent_tier=self.tier,
            status="completed",
            result={
                "intent": intent,
                "plan": plan.model_dump(),
                "summary": f"Parsed intent '{intent.get('intent')}' → {len(plan.tasks)} tasks ready",
            },
            reasoning=reasoning,
            confidence_score=plan.confidence,
            actions_taken=[
                {"action": "parse_intent", "result": intent},
                {"action": "plan_tasks", "result": {"plan_id": plan.plan_id, "task_count": len(plan.tasks)}},
            ],
        )
