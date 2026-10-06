"""Unit tests for the Task State Machine."""

import pytest
from uuid import uuid4

from orvyn.core.exceptions import StateTransitionError
from orvyn.domain.task import Task, TaskState
from orvyn.engine.state_machine import TaskStateMachine


@pytest.mark.asyncio
async def test_valid_forward_transitions():
    """Verify that a task can transition through the standard execution lifecycle."""
    user_id = uuid4()
    task = Task(user_id=user_id, title="Test Workflow", objective="Validate states")

    assert task.current_state == TaskState.CREATED

    # CREATED -> PLANNING
    state = await TaskStateMachine.transition(task, TaskState.PLANNING, reason="Decomposing goal")
    assert state == TaskState.PLANNING
    assert task.current_state == TaskState.PLANNING

    # PLANNING -> EXECUTING
    state = await TaskStateMachine.transition(task, TaskState.EXECUTING, reason="Starting steps")
    assert state == TaskState.EXECUTING

    # EXECUTING -> WAITING
    state = await TaskStateMachine.transition(task, TaskState.WAITING, reason="Waiting for deadline")
    assert state == TaskState.WAITING

    # WAITING -> EXECUTING
    state = await TaskStateMachine.transition(task, TaskState.EXECUTING, reason="Timer fired")
    assert state == TaskState.EXECUTING

    # EXECUTING -> COMPLETED
    state = await TaskStateMachine.transition(task, TaskState.COMPLETED, reason="All steps done")
    assert state == TaskState.COMPLETED


@pytest.mark.asyncio
async def test_human_in_the_loop_transition_cycle():
    """Verify the full Human-in-the-Loop voice call cycle."""
    task = Task(user_id=uuid4(), title="HITL Workflow", objective="Test call cycle")
    await TaskStateMachine.transition(task, TaskState.PLANNING)
    await TaskStateMachine.transition(task, TaskState.EXECUTING)

    checkpoint_id = uuid4()

    # EXECUTING -> HUMAN_REQUIRED (must provide checkpoint_id)
    state = await TaskStateMachine.transition(
        task, TaskState.HUMAN_REQUIRED, reason="Relocation query", checkpoint_id=checkpoint_id
    )
    assert state == TaskState.HUMAN_REQUIRED
    assert task.state_metadata["last_checkpoint_id"] == str(checkpoint_id)

    # HUMAN_REQUIRED -> CALLING
    state = await TaskStateMachine.transition(task, TaskState.CALLING, reason="Dialing phone")
    assert state == TaskState.CALLING

    # CALLING -> AWAITING_RESPONSE
    state = await TaskStateMachine.transition(task, TaskState.AWAITING_RESPONSE, reason="User answered")
    assert state == TaskState.AWAITING_RESPONSE

    # AWAITING_RESPONSE -> RESUMING
    state = await TaskStateMachine.transition(task, TaskState.RESUMING, reason="Decision received")
    assert state == TaskState.RESUMING

    # RESUMING -> EXECUTING
    state = await TaskStateMachine.transition(task, TaskState.EXECUTING, reason="Checkpoint rehydrated")
    assert state == TaskState.EXECUTING


@pytest.mark.asyncio
async def test_illegal_state_transition_raises_error():
    """Verify that jumping across illegal states is blocked."""
    task = Task(user_id=uuid4(), title="Bad Workflow", objective="Test invalid jumps")

    # CREATED cannot jump directly to RESUMING or CALLING
    with pytest.raises(StateTransitionError) as exc_info:
        await TaskStateMachine.transition(task, TaskState.RESUMING)
    assert "Illegal state transition" in str(exc_info.value)

    # CREATED cannot jump directly to EXECUTING
    with pytest.raises(StateTransitionError):
        await TaskStateMachine.transition(task, TaskState.EXECUTING)


@pytest.mark.asyncio
async def test_human_required_fails_without_checkpoint():
    """Verify that transitioning to HUMAN_REQUIRED without a checkpoint raises an error."""
    task = Task(user_id=uuid4(), title="Checkpoint Guard", objective="Test invariant")
    await TaskStateMachine.transition(task, TaskState.PLANNING)
    await TaskStateMachine.transition(task, TaskState.EXECUTING)

    with pytest.raises(StateTransitionError) as exc_info:
        await TaskStateMachine.transition(task, TaskState.HUMAN_REQUIRED, reason="Missing checkpoint")
    assert "requires an atomic checkpoint_id" in str(exc_info.value)
