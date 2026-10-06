"""Task State Machine enforcing legal deterministic transitions."""

from typing import Dict, Set

from app.domain.tasks.models import Task, TaskStatus


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state machine transition is attempted."""
    def __init__(self, from_state: TaskStatus, to_state: TaskStatus, reason: str = ""):
        msg = f"Cannot transition task from '{from_state.value}' to '{to_state.value}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason


class TaskStateMachine:
    """Manages the legal deterministic lifecycle of a Task."""

    # Explicit mapping of allowed state transitions
    ALLOWED_TRANSITIONS: Dict[TaskStatus, Set[TaskStatus]] = {
        TaskStatus.CREATED: {TaskStatus.PLANNING, TaskStatus.CANCELLED},
        TaskStatus.PLANNING: {TaskStatus.EXECUTING, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.EXECUTING: {
            TaskStatus.WAITING,
            TaskStatus.BLOCKED,
            TaskStatus.HUMAN_REQUIRED,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.WAITING: {TaskStatus.EXECUTING, TaskStatus.CANCELLED, TaskStatus.FAILED},
        TaskStatus.BLOCKED: {TaskStatus.HUMAN_REQUIRED, TaskStatus.RESUMING, TaskStatus.CANCELLED, TaskStatus.FAILED},
        TaskStatus.HUMAN_REQUIRED: {
            TaskStatus.CALLING,
            TaskStatus.BLOCKED,
            TaskStatus.AWAITING_RESPONSE,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
        },
        TaskStatus.CALLING: {
            TaskStatus.AWAITING_RESPONSE,
            TaskStatus.BLOCKED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.AWAITING_RESPONSE: {
            TaskStatus.RESUMING,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
        },
        TaskStatus.RESUMING: {TaskStatus.EXECUTING, TaskStatus.FAILED, TaskStatus.CANCELLED},
        TaskStatus.COMPLETED: set(),
        TaskStatus.FAILED: set(),
        TaskStatus.CANCELLED: set(),
    }

    @classmethod
    def can_transition(cls, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """Determines if a status change is permissible."""
        return to_status in cls.ALLOWED_TRANSITIONS.get(from_status, set())

    @classmethod
    def transition(cls, task: Task, to_status: TaskStatus, reason: str = "") -> TaskStatus:
        """Applies a transition to a task or raises an InvalidStateTransitionError."""
        if not cls.can_transition(task.status, to_status):
            raise InvalidStateTransitionError(task.status, to_status, reason)
        task.status = to_status
        return task.status
