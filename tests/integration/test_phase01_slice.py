"""Integration test for the Phase 01 Vertical Slice.

Verifies the entire autonomous-to-human loop:
Goal -> Execution -> Relocation Block -> Checkpoint Snapshot -> Voice Call -> Decision Received -> Resumption -> Completion.
"""

import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from orvyn.database.base import Base
from orvyn.database.models.task_orm import TaskORM
from orvyn.database.models.checkpoint_orm import TaskCheckpointORM
from orvyn.database.models.event_orm import EventORM
from orvyn.domain.task import Task, TaskState
from orvyn.engine.decision_engine import ActionDisposition, DecisionEngine
from orvyn.engine.state_machine import TaskStateMachine
from orvyn.engine.checkpoint_manager import CheckpointManager
from orvyn.core.events import DomainEvent, event_bus


@pytest.fixture
async def async_session():
    """Isolated SQLite async DB session for end-to-end slice verification."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_complete_phase01_vertical_slice(async_session: AsyncSession):
    """Executes the complete Phase 01 Vertical Slice with zero-loss resumption."""
    recorded_events = []

    async def audit_listener(event: DomainEvent):
        recorded_events.append(event)

    event_bus.subscribe_all(audit_listener)

    # 1. User submits high-level objective
    user_id = uuid.uuid4()
    task_orm = TaskORM(
        user_id=user_id,
        title="Find Backend Roles",
        objective="Find relevant backend engineering opportunities for me and help me pursue the best ones.",
        current_state=TaskState.CREATED,
        current_step_index=0,
    )
    async_session.add(task_orm)
    await async_session.commit()
    await async_session.refresh(task_orm)

    # In-memory Domain Task mirror
    task = Task(
        id=task_orm.id,
        user_id=task_orm.user_id,
        title=task_orm.title,
        objective=task_orm.objective,
        current_state=task_orm.current_state,
        current_step_index=0,
    )

    # 2. State Machine: CREATED -> PLANNING -> EXECUTING
    await TaskStateMachine.transition(task, TaskState.PLANNING, reason="Decomposing goal into search steps")
    await TaskStateMachine.transition(task, TaskState.EXECUTING, reason="Searching job boards")
    assert task.current_state == TaskState.EXECUTING

    # 3. Discovers a strong opportunity requiring relocation
    opportunity = {
        "title": "Backend Engineering Intern",
        "organization": "Razorpay",
        "location": "Bangalore",
        "requires_relocation": True,
        "match_score": 0.94,
    }

    # 4. User profile check: User is in Mumbai, relocation preference is unknown
    user_profile = {
        "user_id": str(user_id),
        "current_city": "Mumbai",
        "willing_to_relocate": None,  # Missing information
        "preferred_locations": [],
    }

    # 5. Checkpoint snapshot created before human intervention
    checkpoint_mgr = CheckpointManager()
    working_state = {
        "step_name": "evaluate_opportunity_match",
        "candidate_opportunity": opportunity,
        "profile_location": "Mumbai",
        "search_iteration": 1,
    }
    checkpoint = checkpoint_mgr.create_checkpoint(
        task=task,
        step_name="awaiting_relocation_decision",
        state_snapshot=working_state,
    )
    assert checkpoint.id is not None
    assert checkpoint.resumption_token != ""

    # Persist checkpoint to database
    checkpoint_orm = TaskCheckpointORM(
        id=checkpoint.id,
        task_id=task.id,
        step_index=checkpoint.step_index,
        step_name=checkpoint.step_name,
        state_snapshot=checkpoint.state_snapshot,
        resumption_token=checkpoint.resumption_token,
        state_hash=checkpoint.state_hash,
    )
    async_session.add(checkpoint_orm)
    await async_session.commit()

    # 6. Decision Engine evaluates opportunity
    eval_result = DecisionEngine.evaluate_opportunity(
        task=task,
        checkpoint_id=checkpoint.id,
        opportunity_data=opportunity,
        user_profile=user_profile,
    )
    assert eval_result.disposition == ActionDisposition.HUMAN_INTERVENTION_REQUIRED
    assert eval_result.intervention_request is not None
    assert "relocating to Bangalore" in eval_result.intervention_request.question

    # 7. State Machine: EXECUTING -> HUMAN_REQUIRED -> CALLING -> AWAITING_RESPONSE
    await TaskStateMachine.transition(
        task,
        TaskState.HUMAN_REQUIRED,
        reason="Relocation preference unknown",
        checkpoint_id=checkpoint.id,
    )
    await TaskStateMachine.transition(task, TaskState.CALLING, reason="Dialing user phone")
    await TaskStateMachine.transition(task, TaskState.AWAITING_RESPONSE, reason="User answered call")
    assert task.current_state == TaskState.AWAITING_RESPONSE

    # 8. Human Voice Call Conversation & Structured Extraction (Simulated Telephony Webhook)
    mock_voice_call_transcript = (
        "Agent: Hi, this is ORVYN. I found a strong backend role at Razorpay, but it requires relocating to Bangalore. Are you open to relocating?\n"
        "User: Yes, I am happy to relocate to Bangalore if it's hybrid or full-time."
    )
    extracted_decision = {
        "relocation_accepted": True,
        "city": "Bangalore",
        "notes": "Accepts hybrid or full-time",
        "confidence": 0.98,
    }

    # 9. Resume task using Checkpoint Resumption Token
    retrieved_checkpoint = checkpoint_mgr.get_by_token(checkpoint.resumption_token)
    assert retrieved_checkpoint.id == checkpoint.id

    # Transition to RESUMING
    await TaskStateMachine.transition(task, TaskState.RESUMING, reason="Structured decision received from voice call")
    assert task.current_state == TaskState.RESUMING

    # 10. Restore state and merge human decision
    restored_state = await checkpoint_mgr.restore_task(
        task=task,
        checkpoint=retrieved_checkpoint,
        decision_payload=extracted_decision,
    )
    assert restored_state["human_decision"]["relocation_accepted"] is True
    assert restored_state["decision_applied"] is True

    # 11. State Machine: RESUMING -> EXECUTING -> COMPLETED
    await TaskStateMachine.transition(task, TaskState.EXECUTING, reason="Resumed step with updated user preference")
    # Advance task to next step index
    task.current_step_index = 1
    await TaskStateMachine.transition(task, TaskState.COMPLETED, reason="Opportunity evaluation completed")

    # Update database record
    task_orm.current_state = task.current_state
    task_orm.current_step_index = task.current_step_index
    task_orm.state_metadata = task.state_metadata
    await async_session.commit()

    # 12. Verify DB persistence and complete audit timeline
    target_task_id = task.id
    stmt = select(TaskORM).where(TaskORM.id == target_task_id)
    res = await async_session.execute(stmt)
    persisted_task = res.scalar_one()

    assert persisted_task.current_state == TaskState.COMPLETED
    assert persisted_task.current_step_index == 1
    assert persisted_task.state_metadata["restored_from_checkpoint"] == str(checkpoint.id)

    # 13. Verify Audit Event Stream
    event_types = [e.event_type for e in recorded_events]
    assert "TASK_STATE_TRANSITION" in event_types
    assert "TASK_CHECKPOINT_RESTORED" in event_types
    assert len(recorded_events) >= 6
