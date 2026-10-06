"""Task management and intervention endpoints."""

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orvyn.core.events import DomainEvent, event_bus
from orvyn.database.models.checkpoint_orm import TaskCheckpointORM
from orvyn.database.models.task_orm import TaskORM
from orvyn.database.session import get_db_session
from orvyn.domain.task import Task, TaskState
from orvyn.engine.state_machine import TaskStateMachine
from orvyn.engine.checkpoint_manager import checkpoint_manager

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class CreateTaskRequest(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    title: str
    objective: str


class TaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    objective: str
    current_state: TaskState
    current_step_index: int
    state_metadata: Dict[str, Any]
    created_at: str


class InterveneRequest(BaseModel):
    decision: Dict[str, Any]
    source: str = "MANUAL_WEB_OVERRIDE"


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: CreateTaskRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Creates a new autonomous task and emits the initial TASK_CREATED event."""
    task_orm = TaskORM(
        user_id=payload.user_id,
        title=payload.title,
        objective=payload.objective,
        current_state=TaskState.CREATED,
        current_step_index=0,
    )
    session.add(task_orm)
    await session.commit()
    await session.refresh(task_orm)

    # Emit domain event
    event = DomainEvent(
        correlation_id=task_orm.id,
        aggregate_type="TASK",
        aggregate_id=task_orm.id,
        event_type="TASK_CREATED",
        payload={
            "task_id": str(task_orm.id),
            "title": task_orm.title,
            "objective": task_orm.objective,
        },
    )
    await event_bus.publish(event)

    return TaskResponse(
        id=task_orm.id,
        user_id=task_orm.user_id,
        title=task_orm.title,
        objective=task_orm.objective,
        current_state=task_orm.current_state,
        current_step_index=task_orm.current_step_index,
        state_metadata=task_orm.state_metadata,
        created_at=task_orm.created_at.isoformat(),
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieves current task state and metadata."""
    stmt = select(TaskORM).where(TaskORM.id == task_id)
    result = await session.execute(stmt)
    task_orm = result.scalar_one_or_none()

    if not task_orm:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        id=task_orm.id,
        user_id=task_orm.user_id,
        title=task_orm.title,
        objective=task_orm.objective,
        current_state=task_orm.current_state,
        current_step_index=task_orm.current_step_index,
        state_metadata=task_orm.state_metadata,
        created_at=task_orm.created_at.isoformat(),
    )


@router.post("/{task_id}/intervene")
async def manual_intervention(
    task_id: UUID,
    payload: InterveneRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Allows manual resolution of an awaiting/blocked task, restoring state and resuming execution."""
    stmt = select(TaskORM).where(TaskORM.id == task_id)
    result = await session.execute(stmt)
    task_orm = result.scalar_one_or_none()

    if not task_orm:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_orm.current_state not in [TaskState.AWAITING_RESPONSE, TaskState.BLOCKED, TaskState.HUMAN_REQUIRED]:
        raise HTTPException(
            status_code=400,
            detail=f"Task is in state '{task_orm.current_state}', not awaiting human intervention.",
        )

    # Convert to domain task for state transition
    domain_task = Task(
        id=task_orm.id,
        user_id=task_orm.user_id,
        title=task_orm.title,
        objective=task_orm.objective,
        current_state=task_orm.current_state,
        current_step_index=task_orm.current_step_index,
        state_metadata=task_orm.state_metadata,
    )

    # Transition to RESUMING
    await TaskStateMachine.transition(domain_task, TaskState.RESUMING, reason="Manual intervention provided")

    # If checkpoint exists, restore state with decision
    last_checkpoint_id = domain_task.state_metadata.get("last_checkpoint_id")
    if last_checkpoint_id:
        try:
            chk = checkpoint_manager.get_checkpoint(UUID(last_checkpoint_id))
            await checkpoint_manager.restore_task(domain_task, chk, decision_payload=payload.decision)
        except Exception:
            pass

    # Transition to EXECUTING
    await TaskStateMachine.transition(domain_task, TaskState.EXECUTING, reason="Resuming after intervention")

    # Update database record
    task_orm.current_state = domain_task.current_state
    task_orm.state_metadata = domain_task.state_metadata
    task_orm.current_step_index = domain_task.current_step_index
    await session.commit()

    return {"status": "success", "new_state": task_orm.current_state.value}
