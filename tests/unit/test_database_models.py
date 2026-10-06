"""Integration tests for database ORM models and schema initialization."""

import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from orvyn.database.base import Base
from orvyn.database.models.task_orm import TaskORM
from orvyn.database.models.checkpoint_orm import TaskCheckpointORM
from orvyn.database.models.event_orm import EventORM
from orvyn.domain.task import TaskState


@pytest.fixture
async def async_test_session():
    """Provides an isolated SQLite in-memory async database session."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_task_orm_persistence(async_test_session: AsyncSession):
    """Verify creating, committing, and querying a Task record."""
    user_id = uuid.uuid4()
    task = TaskORM(
        user_id=user_id,
        title="Find Backend Roles",
        objective="Search internships in Bangalore",
        current_state=TaskState.CREATED,
        current_step_index=0,
        plan={"objective": "Find Backend Roles", "steps": []},
        state_metadata={"test_run": True},
    )

    async_test_session.add(task)
    await async_test_session.commit()
    await async_test_session.refresh(task)

    assert task.id is not None
    assert task.current_state == TaskState.CREATED

    # Query back
    stmt = select(TaskORM).where(TaskORM.id == task.id)
    result = await async_test_session.execute(stmt)
    persisted = result.scalar_one_or_none()
    assert persisted is not None
    assert persisted.title == "Find Backend Roles"
    assert persisted.state_metadata == {"test_run": True}


@pytest.mark.asyncio
async def test_checkpoint_and_events_foreign_keys(async_test_session: AsyncSession):
    """Verify Task checkpoints and audit event cascade relationships."""
    user_id = uuid.uuid4()
    task = TaskORM(
        user_id=user_id,
        title="HITL Task",
        objective="Autonomous search",
        current_state=TaskState.HUMAN_REQUIRED,
        current_step_index=1,
    )
    async_test_session.add(task)
    await async_test_session.commit()
    await async_test_session.refresh(task)

    target_task_id = task.id

    checkpoint = TaskCheckpointORM(
        task_id=target_task_id,
        step_index=1,
        step_name="ask_human_relocation",
        state_snapshot={"opportunities_found": 3},
        resumption_token="token_abc_123",
        state_hash="dummy_hash_for_test",
    )
    event = EventORM(
        task_id=target_task_id,
        correlation_id=target_task_id,
        aggregate_type="TASK",
        aggregate_id=target_task_id,
        event_type="TASK_BLOCKED_FOR_HUMAN",
        payload={"reason": "Relocation preference required"},
    )

    async_test_session.add_all([checkpoint, event])
    await async_test_session.commit()

    # Query checkpoints directly by task_id
    stmt_checkpoints = select(TaskCheckpointORM).where(TaskCheckpointORM.task_id == target_task_id)
    res_checkpoints = await async_test_session.execute(stmt_checkpoints)
    checkpoints = res_checkpoints.scalars().all()

    # Query events directly by task_id
    stmt_events = select(EventORM).where(EventORM.task_id == target_task_id)
    res_events = await async_test_session.execute(stmt_events)
    events = res_events.scalars().all()

    assert len(checkpoints) == 1
    assert checkpoints[0].step_name == "ask_human_relocation"
    assert len(events) == 1
    assert events[0].event_type == "TASK_BLOCKED_FOR_HUMAN"
