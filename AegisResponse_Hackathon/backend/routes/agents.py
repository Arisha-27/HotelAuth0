"""
Phase 4 Routes: Hierarchical Agent System API
Exposes the multi-agent system via REST endpoints.
"""

from fastapi import APIRouter
from typing import Optional

from backend.agents.registry import agent_registry, AgentExecutionRequest
from backend.agents.base import AgentInput
from backend.logging_config import get_logger

logger = get_logger("routes.agents")
router = APIRouter()


# ═══════════════════════════════════════════
# 🧠 Agent Execution
# ═══════════════════════════════════════════
@router.post("/agents/execute", tags=["Agents"])
async def execute_agent_request(request: AgentExecutionRequest):
    """
    Main entry point for the agent system.
    Send a natural language message and the executive agent will:
    1. Parse intent
    2. Build a task plan
    3. Dispatch to domain agents
    4. Return results from all agents
    """
    result = await agent_registry.execute(request)
    return result.model_dump()


@router.post("/agents/{agent_id}/direct", tags=["Agents"])
async def direct_agent_call(agent_id: str, request: AgentExecutionRequest):
    """Dispatch directly to a specific agent (bypasses executive)."""
    request.target_agent = agent_id
    result = await agent_registry.execute(request)
    return result.model_dump()


# ═══════════════════════════════════════════
# 📋 Agent Registry
# ═══════════════════════════════════════════
@router.get("/agents", tags=["Agents"])
async def list_agents():
    """List all registered agents and their status."""
    return {
        "agents": agent_registry.list_agents(),
        "brain": agent_registry.get_brain_info(),
        "total": len(agent_registry.list_agents()),
    }


@router.get("/agents/hierarchy", tags=["Agents"])
async def get_hierarchy():
    """Get the agent hierarchy tree."""
    return agent_registry.get_hierarchy()


@router.get("/agents/{agent_id}/status", tags=["Agents"])
async def get_agent_status(agent_id: str):
    """Get a specific agent's status."""
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        return {"error": f"Agent '{agent_id}' not found"}
    return agent.get_status()


@router.get("/agents/{agent_id}/trace", tags=["Agents"])
async def get_agent_trace(agent_id: str, limit: int = 20):
    """Get execution trace for a specific agent."""
    return {"agent_id": agent_id, "trace": agent_registry.get_agent_trace(agent_id, limit)}


@router.get("/agents/{agent_id}/memory", tags=["Agents"])
async def get_agent_memory(agent_id: str):
    """Get an agent's current memory state."""
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        return {"error": f"Agent '{agent_id}' not found"}
    return {
        "agent_id": agent_id,
        "context": agent.memory.get_context_summary(),
        "history": agent.memory.get_history(10),
    }


# ═══════════════════════════════════════════
# 📊 Execution History
# ═══════════════════════════════════════════
@router.get("/agents/history", tags=["Agents"])
async def get_execution_history(limit: int = 20):
    """Get recent execution history across all agents."""
    return {"history": agent_registry.get_execution_history(limit)}


# ═══════════════════════════════════════════
# 🧠 Brain Info
# ═══════════════════════════════════════════
@router.get("/agents/brain/info", tags=["Agents"])
async def get_brain_info():
    """Get information about the current LLM brain provider."""
    return agent_registry.get_brain_info()
