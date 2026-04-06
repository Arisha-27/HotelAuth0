"""
Retry Manager — Handles failure recovery and rollback simulation.
"""

import asyncio
from typing import Callable, Coroutine, Any, List

from backend.logging_config import get_logger

logger = get_logger("services.retry_manager")


class ActionFailedError(Exception):
    pass


class RetryManager:
    """Manages exponential backoff retries and simulated rollbacks."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute_with_retry(
        self,
        task_id: str,
        action: Callable[[], Coroutine[Any, Any, Any]],
        rollback_action: Callable[[], Coroutine[Any, Any, Any]] = None,
    ) -> Any:
        """
        Execute an async action with retries.
        If it fails completely, optionally execute a compensating rollback action.
        """
        retries = 0
        last_error = None

        while retries <= self.max_retries:
            try:
                logger.info(f"Executing task {task_id} (attempt {retries + 1}/{self.max_retries + 1})")
                return await action()
            except Exception as e:
                last_error = e
                retries += 1
                if retries <= self.max_retries:
                    delay = self.base_delay * (2 ** (retries - 1))
                    logger.warning(
                        f"Task {task_id} failed: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)

        logger.error(f"Task {task_id} failed permanently after {self.max_retries} retries")

        if rollback_action:
            logger.info(f"Executing rollback for task {task_id}")
            try:
                await rollback_action()
                logger.info(f"Rollback successful for task {task_id}")
            except Exception as rb_e:
                logger.error(f"CRITICAL: Rollback failed for task {task_id}: {rb_e}", exc_info=True)
                raise ActionFailedError(f"Action and rollback failed. Original error: {last_error}, Rollback error: {rb_e}")

        raise ActionFailedError(f"Action failed permanently: {last_error}")

# Global instance
retry_manager = RetryManager()
