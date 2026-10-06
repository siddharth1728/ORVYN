"""Domain unit tests: Task lifecycle, State Machine, and Checkpointing."""

import pytest
from uuid import uuid4

from app.domain.decisions.models import Decision
from app.domain.tasks.models import Task, TaskCheckpoint, TaskPriority, TaskStatus
from app.domain.tasks.state_machine import InvalidStateTransitionError, TaskStateMachine


def test_task_initialization():
    task = Task(title="Search Internships", objective="Find roles in Bangalore")
    assert task.status == TaskStatus.CREATED
    assert task.priority == TaskPriority.MEDIUM
    assert task.current_step == 0
    assert task.id is not None


def test_valid_forward_state_transitions():
    task = Task(title="Test Task", objective="Objective")
    assert TaskStateMachine.transition(task, TaskStatus.PLANNING) == TaskStatus.PLANNING
    assert TaskStateMachine.transition(task, TaskStatus.EXECUTING) == TaskStatus.EXECUTING
    assert TaskStateMachine.transition(task, TaskStatus.WAITING) == TaskStatus.WAITING
    assert TaskStateMachine.transition(task, TaskStatus.EXECUTING) == TaskStatus.EXECUTING
    assert TaskStateMachine.transition(task, TaskStatus.COMPLETED) == TaskStatus.COMPLETED


def test_invalid_state_transition_rejected():
    task = Task(title="Invalid Transition", objective="Objective")
    # Cannot jump from CREATED directly to RESUMING
    with pytest.raises(InvalidStateTransitionError):
        TaskStateMachine.transition(task, TaskStatus.RESUMING)

    # Cannot transition from COMPLETED to EXECUTING
    task.status = TaskStatus.COMPLETED
    with pytest.raises(InvalidStateTransitionError):
        TaskStateMachine.transition(task, TaskStatus.EXECUTING)


def test_checkpoint_hash_integrity():
    task_id = uuid4()
    state = {"search_results": ["Role A", "Role B"], "count": 2}
    checkpoint = TaskCheckpoint(
        task_id=task_id,
        step_index=1,
        step_name="search_step",
        state_snapshot=state,
    )
    assert checkpoint.state_hash != ""
    assert checkpoint.resumption_token != ""


def test_decision_domain_entity():
    task_id = uuid4()
    decision = Decision(
        task_id=task_id,
        question="Are you willing to relocate to Bangalore?",
        context={"location": "Bangalore"},
        answer={"relocation_accepted": True},
        source="human_voice",
    )
    assert decision.answer == {"relocation_accepted": True}
    assert decision.confidence == 1.0
