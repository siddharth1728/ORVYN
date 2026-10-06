"""Deterministic Agent State Machine."""

from typing import Dict, Optional, Set
from uuid import UUID

from orvyn.core.events import DomainEvent, event_bus
from orvyn.core.exceptions import StateTransitionError
from orvyn.domain.task import Task, TaskState


class TaskStateMachine:
    """Manages legal transitions for a Task and emits audit domain events."""

    # Explicit allowed transitions table
    ALLOWED_TRANSITIONS: Dict[TaskState, Set[TaskState]] = {
        TaskState.CREATED: {TaskState.PLANNING, TaskState.CANCELLED},
        TaskState.PLANNING: {TaskState.EXECUTING, TaskState.FAILED, TaskState.CANCELLED},
        TaskState.EXECUTING: {
            TaskState.WAITING,
            TaskState.BLOCKED,
            TaskState.HUMAN_REQUIRED,
            TaskState.COMPLETED,
            TaskState.FAILED,
            TaskState.CANCELLED,
        },
        TaskState.WAITING: {TaskState.EXECUTING, TaskState.CANCELLED},
        TaskState.BLOCKED: {TaskState.HUMAN_REQUIRED, TaskState.CANCELLED, TaskState.FAILED},
        TaskState.HUMAN_REQUIRED: {
            TaskState.CALLING,
            TaskState.BLOCKED,
            TaskState.FAILED,
            TaskState.CANCELLED,
        },
        TaskState.CALLING: {TaskState.AWAITING_RESPONSE, TaskState.BLOCKED, TaskState.FAILED},
        TaskState.AWAITING_RESPONSE: {
            TaskState.RESUMING,
            TaskState.BLOCKED,
            TaskState.FAILED,
        },
        TaskState.RESUMING: {TaskState.EXECUTING, TaskState.FAILED},
        TaskState.COMPLETED: set(),
        TaskState.FAILED: set(),
        TaskState.CANCELLED: set(),
    }

    @classmethod
    def can_transition(cls, from_state: TaskState, to_state: TaskState) -> bool:
        """Checks if a transition from from_state to to_state is permissible."""
        return to_state in cls.ALLOWED_TRANSITIONS.get(from_state, set())

    @classmethod
    async def transition(
        cls,
        task: Task,
        to_state: TaskState,
        reason: str = "",
        checkpoint_id: Optional[UUID] = None,
        correlation_id: Optional[UUID] = None,
        causation_id: Optional[UUID] = None,
    ) -> TaskState:
        """Transitions the task to to_state if legal, enforcing state invariants and emitting audit events."""
        from_state = task.current_state

        if not cls.can_transition(from_state, to_state):
            raise StateTransitionError(
                from_state=from_state.value,
                to_state=to_state.value,
                reason=reason or f"Transition not allowed by state machine rules."
            )

        # Invariant 1: Transitioning to HUMAN_REQUIRED strictly requires a checkpoint reference
        if to_state == TaskState.HUMAN_REQUIRED and checkpoint_id is None:
            # Check if one is already recorded in metadata
            if "last_checkpoint_id" not in task.state_metadata:
                raise StateTransitionError(
                    from_state=from_state.value,
                    to_state=to_state.value,
                    reason="Transition to HUMAN_REQUIRED requires an atomic checkpoint_id."
                )

        if checkpoint_id:
            task.state_metadata["last_checkpoint_id"] = str(checkpoint_id)

        # Update state
        task.current_state = to_state

        # Emit audit domain event
        event = DomainEvent(
            correlation_id=correlation_id or task.id,
            causation_id=causation_id,
            aggregate_type="TASK",
            aggregate_id=task.id,
            event_type=f"TASK_STATE_TRANSITION",
            payload={
                "task_id": str(task.id),
                "from_state": from_state.value,
                "to_state": to_state.value,
                "reason": reason,
                "checkpoint_id": str(checkpoint_id) if checkpoint_id else None,
                "step_index": task.current_step_index,
            },
        )
        await event_bus.publish(event)

        return task.current_state
