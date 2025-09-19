"""
Progress tracking for Telegram bot operations.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TaskProgress:
    """Progress information for a task."""

    task_id: str
    task_type: str
    user_id: int
    started_at: datetime
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    percentage: float = 0.0
    status: str = "running"  # running, completed, failed, cancelled
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class ProgressTracker:
    """Track progress of long-running tasks for the Telegram bot."""

    def __init__(self):
        """Initialize the progress tracker."""
        self.active_tasks: dict[int, TaskProgress] = {}  # user_id -> TaskProgress

    def start_task(
        self, user_id: int, task_type: str, metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """Start tracking a new task for a user."""
        task_id = f"{task_type}_{user_id}_{datetime.now().timestamp()}"

        # Cancel any existing task for this user
        if user_id in self.active_tasks:
            self.cancel_task(user_id)

        task_progress = TaskProgress(
            task_id=task_id,
            task_type=task_type,
            user_id=user_id,
            started_at=datetime.now(),
            metadata=metadata or {},
        )

        self.active_tasks[user_id] = task_progress
        logger.info(f"Started task {task_id} for user {user_id}")

        return task_id

    def update_progress(
        self,
        user_id: int,
        step: str,
        completed_steps: int = None,
        total_steps: int = None,
        percentage: float = None,
    ) -> bool:
        """Update progress for a user's task."""
        if user_id not in self.active_tasks:
            logger.warning(f"No active task found for user {user_id}")
            return False

        task = self.active_tasks[user_id]
        task.current_step = step

        if completed_steps is not None:
            task.completed_steps = completed_steps

        if total_steps is not None:
            task.total_steps = total_steps

        if percentage is not None:
            task.percentage = percentage
        elif task.total_steps > 0:
            task.percentage = (task.completed_steps / task.total_steps) * 100

        logger.debug(
            f"Updated progress for user {user_id}: {task.percentage:.1f}% - {step}"
        )
        return True

    def complete_task(
        self, user_id: int, success: bool = True, error_message: Optional[str] = None
    ):
        """Mark a task as completed."""
        if user_id not in self.active_tasks:
            logger.warning(f"No active task found for user {user_id}")
            return

        task = self.active_tasks[user_id]
        task.status = "completed" if success else "failed"
        task.percentage = 100.0 if success else task.percentage
        task.error_message = error_message

        logger.info(
            f"Task {task.task_id} {'completed' if success else 'failed'} for user {user_id}"
        )

        # Remove from active tasks
        del self.active_tasks[user_id]

    def cancel_task(self, user_id: int):
        """Cancel a user's active task."""
        if user_id not in self.active_tasks:
            return

        task = self.active_tasks[user_id]
        task.status = "cancelled"

        logger.info(f"Task {task.task_id} cancelled for user {user_id}")

        # Remove from active tasks
        del self.active_tasks[user_id]

    def get_progress(self, user_id: int) -> Optional[dict[str, Any]]:
        """Get current progress for a user's task."""
        if user_id not in self.active_tasks:
            return None

        task = self.active_tasks[user_id]
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "current_step": task.current_step,
            "completed_steps": task.completed_steps,
            "total_steps": task.total_steps,
            "percentage": task.percentage,
            "status": task.status,
            "started_at": task.started_at.isoformat(),
            "duration_seconds": (datetime.now() - task.started_at).total_seconds(),
            "metadata": task.metadata,
            "error_message": task.error_message,
        }

    def has_active_task(self, user_id: int) -> bool:
        """Check if user has an active task."""
        return user_id in self.active_tasks

    def get_all_active_tasks(self) -> dict[int, dict[str, Any]]:
        """Get all active tasks."""
        return {user_id: self.get_progress(user_id) for user_id in self.active_tasks}

    def cleanup_stale_tasks(self, max_age_hours: int = 2):
        """Clean up tasks that have been running too long."""
        now = datetime.now()
        stale_users = []

        for user_id, task in self.active_tasks.items():
            age = (now - task.started_at).total_seconds() / 3600
            if age > max_age_hours:
                stale_users.append(user_id)

        for user_id in stale_users:
            logger.warning(f"Cleaning up stale task for user {user_id}")
            self.cancel_task(user_id)

        return len(stale_users)


class YouTubeProcessingSteps:
    """Define standard steps for YouTube processing tasks."""

    STEPS = [
        "Validating URL",
        "Downloading audio",
        "Transcribing audio",
        "Processing text",
        "Creating embeddings",
        "Storing in database",
        "Finalizing",
    ]

    @classmethod
    def get_step_percentage(cls, step_name: str) -> float:
        """Get the percentage for a given step."""
        try:
            step_index = cls.STEPS.index(step_name)
            return (step_index / len(cls.STEPS)) * 100
        except ValueError:
            return 0.0

    @classmethod
    def get_total_steps(cls) -> int:
        """Get total number of steps."""
        return len(cls.STEPS)


class RAGQuerySteps:
    """Define standard steps for RAG query processing."""

    STEPS = [
        "Processing query",
        "Searching database",
        "Ranking results",
        "Generating response",
        "Formatting output",
    ]

    @classmethod
    def get_step_percentage(cls, step_name: str) -> float:
        """Get the percentage for a given step."""
        try:
            step_index = cls.STEPS.index(step_name)
            return (step_index / len(cls.STEPS)) * 100
        except ValueError:
            return 0.0

    @classmethod
    def get_total_steps(cls) -> int:
        """Get total number of steps."""
        return len(cls.STEPS)
