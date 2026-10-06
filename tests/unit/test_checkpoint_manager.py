"""Unit tests for the Checkpoint Manager."""

import pytest
from uuid import uuid4

from orvyn.core.exceptions import CheckpointError, CheckpointNotFoundError
from orvyn.domain.task import Task
from orvyn.engine.checkpoint_manager import CheckpointManager


@pytest.mark.asyncio
async def test_checkpoint_creation_and_retrieval():
    """Verify state snapshot creation, hashing, and retrieval."""
    manager = CheckpointManager()
    task = Task(user_id=uuid4(), title="Checkpoint Test", objective="Test state snapshots")
    task.current_step_index = 2

    state_data = {
        "discovered_opportunities": [{"id": 1, "title": "Backend Intern", "company": "Razorpay"}],
        "current_query": "Backend Internships Bangalore",
        "loop_counter": 5,
    }

    checkpoint = manager.create_checkpoint(task, step_name="evaluate_opportunities", state_snapshot=state_data)

    assert checkpoint.task_id == task.id
    assert checkpoint.step_index == 2
    assert checkpoint.step_name == "evaluate_opportunities"
    assert checkpoint.state_hash != ""
    assert checkpoint.resumption_token != ""

    # Retrieve by ID
    retrieved = manager.get_checkpoint(checkpoint.id)
    assert retrieved.id == checkpoint.id
    assert retrieved.state_snapshot == state_data

    # Retrieve by Token
    retrieved_by_token = manager.get_by_token(checkpoint.resumption_token)
    assert retrieved_by_token.id == checkpoint.id


@pytest.mark.asyncio
async def test_checkpoint_restoration_and_decision_merge():
    """Verify restoring a task from checkpoint and merging human decision."""
    manager = CheckpointManager()
    task = Task(user_id=uuid4(), title="Restore Test", objective="Test restoration")
    task.current_step_index = 3

    original_state = {"search_done": True, "opportunities_count": 4}
    checkpoint = manager.create_checkpoint(task, step_name="await_human", state_snapshot=original_state)

    # Change task state to simulate drift or interruption
    task.current_step_index = 0

    # Restore with decision payload
    decision = {"relocation_accepted": True, "city": "Bangalore"}
    restored_state = await manager.restore_task(task, checkpoint, decision_payload=decision)

    assert task.current_step_index == 3
    assert restored_state["search_done"] is True
    assert restored_state["human_decision"] == decision
    assert restored_state["decision_applied"] is True
    assert task.state_metadata["restored_from_checkpoint"] == str(checkpoint.id)


@pytest.mark.asyncio
async def test_checkpoint_integrity_tampering_fails():
    """Verify that tampering with state_snapshot violates SHA-256 hash check."""
    manager = CheckpointManager()
    task = Task(user_id=uuid4(), title="Tamper Test", objective="Test hash tampering")
    checkpoint = manager.create_checkpoint(task, step_name="step_1", state_snapshot={"balance": 100})

    # Tamper with snapshot in-memory
    checkpoint.state_snapshot["balance"] = 999999

    with pytest.raises(CheckpointError) as exc_info:
        await manager.restore_task(task, checkpoint)
    assert "integrity check failed" in str(exc_info.value)
