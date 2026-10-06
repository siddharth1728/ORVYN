"""Checkpoint Manager for atomic task state snapshotting and resumption."""

import copy
import hashlib
import json
from typing import Any, Dict, Optional
from uuid import UUID

from orvyn.core.events import DomainEvent, event_bus
from orvyn.core.exceptions import CheckpointError, CheckpointNotFoundError
from orvyn.domain.checkpoint import TaskCheckpoint
from orvyn.domain.task import Task


class CheckpointManager:
    """Handles snapshotting, integrity verification, and restoration of task state."""

    def __init__(self) -> None:
        # In-memory store (supplemented by Database repository)
        self._checkpoints: Dict[UUID, TaskCheckpoint] = {}
        self._token_map: Dict[str, UUID] = {}

    def create_checkpoint(
        self,
        task: Task,
        step_name: str,
        state_snapshot: Dict[str, Any],
    ) -> TaskCheckpoint:
        """Serializes current execution variables, calculates SHA-256 hash, and saves checkpoint."""
        try:
            # Ensure JSON serializability
            serialized = json.dumps(state_snapshot, sort_keys=True, default=str)
            computed_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        except (TypeError, ValueError) as err:
            raise CheckpointError(f"Failed to serialize state snapshot: {err}") from err

        checkpoint = TaskCheckpoint(
            task_id=task.id,
            step_index=task.current_step_index,
            step_name=step_name,
            state_snapshot=copy.deepcopy(state_snapshot),
            state_hash=computed_hash,
        )

        self._checkpoints[checkpoint.id] = checkpoint
        self._token_map[checkpoint.resumption_token] = checkpoint.id

        # Update task state metadata with latest checkpoint
        task.state_metadata["last_checkpoint_id"] = str(checkpoint.id)
        task.state_metadata["last_resumption_token"] = checkpoint.resumption_token

        return checkpoint

    def get_checkpoint(self, checkpoint_id: UUID) -> TaskCheckpoint:
        """Retrieves checkpoint by UUID."""
        if checkpoint_id not in self._checkpoints:
            raise CheckpointNotFoundError(f"Checkpoint '{checkpoint_id}' not found.")
        return self._checkpoints[checkpoint_id]

    def get_by_token(self, token: str) -> TaskCheckpoint:
        """Retrieves checkpoint by secure resumption token."""
        checkpoint_id = self._token_map.get(token)
        if not checkpoint_id:
            raise CheckpointNotFoundError(f"Checkpoint with token '{token}' not found.")
        return self.get_checkpoint(checkpoint_id)

    async def restore_task(
        self,
        task: Task,
        checkpoint: TaskCheckpoint,
        decision_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Verifies checkpoint integrity, restores task indices, merges human decision, and emits event."""
        # 1. Verify hash integrity
        serialized = json.dumps(checkpoint.state_snapshot, sort_keys=True, default=str)
        computed_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        if computed_hash != checkpoint.state_hash:
            raise CheckpointError(
                f"Checkpoint {checkpoint.id} integrity check failed: hash mismatch."
            )

        # 2. Re-hydrate task indices
        task.current_step_index = checkpoint.step_index
        restored_state = copy.deepcopy(checkpoint.state_snapshot)

        # 3. Merge human decision payload if provided
        if decision_payload:
            restored_state["human_decision"] = decision_payload
            restored_state["decision_applied"] = True

        task.state_metadata["restored_from_checkpoint"] = str(checkpoint.id)
        task.state_metadata["current_state_snapshot"] = restored_state

        # 4. Emit domain event
        event = DomainEvent(
            correlation_id=task.id,
            aggregate_type="TASK",
            aggregate_id=task.id,
            event_type="TASK_CHECKPOINT_RESTORED",
            payload={
                "task_id": str(task.id),
                "checkpoint_id": str(checkpoint.id),
                "step_index": checkpoint.step_index,
                "step_name": checkpoint.step_name,
                "has_decision": decision_payload is not None,
            },
        )
        await event_bus.publish(event)

        return restored_state


# Default singleton instance
checkpoint_manager = CheckpointManager()
