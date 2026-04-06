"""
Task Queue Manager.
Handles background asynchronous processing of agent tasks.
"""

import asyncio
from typing import Callable, Coroutine, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field

from backend.logging_config import get_logger

logger = get_logger("services.task_queue")


@dataclass(order=True)
class TaskItem:
    priority: int
    task_id: str = field(compare=False)
    coro: Coroutine = field(compare=False)
    timestamp: float = field(compare=False, default_factory=lambda: datetime.now(timezone.utc).timestamp())


class TaskQueue:
    """In-memory async task queue for orchestrating agent actions."""

    def __init__(self, num_workers: int = 3):
        self._queue: asyncio.PriorityQueue[TaskItem] = asyncio.PriorityQueue()
        self._num_workers = num_workers
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._tasks_processed = 0

    async def _worker(self, worker_id: int):
        logger.info(f"Task worker {worker_id} started")
        while self._running:
            try:
                task_item = await self._queue.get()
                logger.info(f"Worker {worker_id} processing task: {task_item.task_id}")
                
                try:
                    await task_item.coro
                    self._tasks_processed += 1
                    logger.info(f"Worker {worker_id} completed task: {task_item.task_id}")
                except Exception as e:
                    logger.error(f"Worker {worker_id} failed task {task_item.task_id}: {e}", exc_info=True)
                finally:
                    self._queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in worker {worker_id}: {e}", exc_info=True)
                
        logger.info(f"Task worker {worker_id} stopped")

    def start(self):
        """Start the task queue worker pool."""
        if self._running:
            return
            
        self._running = True
        for i in range(self._num_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)

    async def stop(self, wait_completion: bool = True):
        """Stop the task queue workers, optionally waiting for pending tasks."""
        self._running = False
        
        if wait_completion:
            await self._queue.join()
            
        for worker in self._workers:
            worker.cancel()
            
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def enqueue(self, task_id: str, coro: Coroutine, priority: int = 10) -> None:
        """Enqueue a new async task. Lower priority number means higher priority."""
        item = TaskItem(priority=priority, task_id=task_id, coro=coro)
        await self._queue.put(item)
        logger.info(f"Enqueued task: {task_id} with priority {priority}")

    def get_status(self) -> dict:
        """Get metrics about the task queue."""
        return {
            "queue_size": self._queue.qsize(),
            "workers_active": len(self._workers),
            "tasks_processed": self._tasks_processed,
            "running": self._running
        }

# Global singleton instance
task_queue = TaskQueue()
