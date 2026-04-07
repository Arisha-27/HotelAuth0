"""
Orchestrator Service — Core intelligence bridge.
Accepts task graphs, manages dependencies, and dispatches to agents.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field
import asyncio
import uuid

from backend.logging_config import get_logger
from backend.services.task_queue import task_queue
from backend.services.retry_manager import retry_manager

logger = get_logger("services.orchestrator")


class TaskDefinition(BaseModel):
    task_id: str
    target_agent: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)


class TaskGraph(BaseModel):
    graph_id: str
    tasks: List[TaskDefinition]


class Orchestrator:
    """Manages execution of complex task graphs across multiple agents."""

    def __init__(self):
        self._active_graphs: Dict[str, TaskGraph] = {}
        self._task_results: Dict[str, Dict[str, Any]] = {}

    def validate_graph(self, graph: TaskGraph) -> bool:
        """Validate that all dependencies exist and there are no cycles."""
        task_ids = {t.task_id for t in graph.tasks}
        
        # Check if all dependencies exist
        for task in graph.tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    logger.error(f"Graph validation failed: Task {task.task_id} depends on unknown task {dep}")
                    return False

        # TODO: Implement full cycle detection (DAG validation)
        # For this hackathon iteration, we'll assume linear/simple dependencies
        return True

    async def submit_graph(self, graph: TaskGraph) -> str:
        """Submit a new task graph for execution."""
        if not self.validate_graph(graph):
            raise ValueError("Invalid task graph structure")

        graph_execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        self._active_graphs[graph_execution_id] = graph
        self._task_results[graph_execution_id] = {}

        logger.info(f"Accepted task graph {graph.graph_id} -> Execution ID: {graph_execution_id}")

        # Start execution asynchronously
        asyncio.create_task(self._execute_graph(graph_execution_id, graph))
        
        return graph_execution_id

    async def _mock_agent_call(self, task: TaskDefinition) -> dict:
        """Simulate calling a downstream domain agent"""
        logger.info(f"Dispatching task {task.task_id} to {task.target_agent} agent")
        await asyncio.sleep(0.5)  # Simulate network latency
        return {"status": "success", "agent": task.target_agent, "action_performed": task.action}

    async def _execute_task(self, exec_id: str, task: TaskDefinition) -> None:
        """Execute a single task with retries."""
        logger.info(f"Executing task {task.task_id} in run {exec_id}")
        
        try:
            result = await retry_manager.execute_with_retry(
                task_id=task.task_id,
                action=lambda: self._mock_agent_call(task)
            )
            self._task_results[exec_id][task.task_id] = {
                "status": "completed", 
                "result": result
            }
        except Exception as e:
            self._task_results[exec_id][task.task_id] = {
                "status": "failed", 
                "error": str(e)
            }
            logger.error(f"Task {task.task_id} failed: {e}")

    async def _execute_graph(self, exec_id: str, graph: TaskGraph) -> None:
        """
        Execute tasks respecting their dependencies.
        Simplified runner: processes tasks whose dependencies have completed.
        """
        pending = {t.task_id: t for t in graph.tasks}
        running = set()
        
        logger.info(f"Starting execution of graph {exec_id}")

        while pending or running:
            # Find tasks ready to run (all dependencies met and successful)
            ready_to_run = []
            failed_deps = False

            for task_id, task in list(pending.items()):
                dependencies_met = True
                
                for dep in task.depends_on:
                    dep_result = self._task_results.get(exec_id, {}).get(dep)
                    if not dep_result:
                        dependencies_met = False
                        break
                    if dep_result["status"] == "failed":
                        failed_deps = True
                        break
                
                if failed_deps:
                    logger.warning(f"Aborting task {task_id} due to failed dependencies")
                    self._task_results.setdefault(exec_id, {})[task_id] = {"status": "aborted", "reason": "dependency_failed"}
                    pending.pop(task_id)
                    failed_deps = False # Reset for next task check
                    continue

                if dependencies_met:
                    ready_to_run.append(task)

            # Start ready tasks
            for task in ready_to_run:
                pending.pop(task.task_id)
                running.add(task.task_id)
                
                # Enqueue the actual execution
                await task_queue.enqueue(
                    task_id=f"{exec_id}_{task.task_id}",
                    coro=self._execute_task_wrapper(exec_id, task, running),
                    priority=5 # Standard priority
                )

            # Back off slightly if waiting for running tasks to complete
            if running:
                await asyncio.sleep(0.1)
                
        logger.info(f"Completed execution of graph {exec_id}")

    async def _execute_task_wrapper(self, exec_id: str, task: TaskDefinition, running_set: set):
        try:
            await self._execute_task(exec_id, task)
        finally:
            running_set.discard(task.task_id)


# Global orchestrator
orchestrator = Orchestrator()
