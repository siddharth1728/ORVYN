"""Task API routes and schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_event_dispatcher, get_task_service
from app.application.task_service.service import TaskNotFoundError, TaskService
from app.core.exceptions import InvalidStateTransitionError
from app.domain.events.dispatcher import EventDispatcher
from app.domain.tasks.models import TaskPriority, TaskStatus

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    objective: str = Field(..., min_length=1)
    priority: TaskPriority = TaskPriority.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    id: UUID
    title: str
    objective: str
    status: TaskStatus
    priority: TaskPriority
    current_step: int
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


class ResumeTaskRequest(BaseModel):
    decision: Dict[str, Any] = Field(default_factory=dict)


class PauseTaskRequest(BaseModel):
    reason: str = "User requested pause"


class CheckpointResponse(BaseModel):
    id: UUID
    task_id: UUID
    step_index: int
    step_name: str
    state_snapshot: Dict[str, Any]
    resumption_token: str
    created_at: datetime


class EventResponse(BaseModel):
    event_id: UUID
    event_type: str
    task_id: Optional[UUID]
    timestamp: datetime
    payload: Dict[str, Any]
    source: str


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(payload: CreateTaskRequest, service: TaskService = Depends(get_task_service)):
    task = await service.create_task(
        title=payload.title,
        objective=payload.objective,
        priority=payload.priority,
        metadata=payload.metadata,
    )
    return TaskResponse(**task.model_dump())


@router.get("", response_model=List[TaskResponse])
def list_tasks(service: TaskService = Depends(get_task_service)):
    tasks = service.list_tasks()
    return [TaskResponse(**t.model_dump()) for t in tasks]


@router.get("/{id}", response_model=TaskResponse)
def get_task(id: UUID, service: TaskService = Depends(get_task_service)):
    try:
        task = service.get_task(id)
        return TaskResponse(**task.model_dump())
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail=f"Task '{id}' not found.")


@router.post("/{id}/run")
async def run_task(id: UUID, service: TaskService = Depends(get_task_service)):
    try:
        result = await service.run_task(id)
        return {
            "task_id": str(result.task_id),
            "status": result.status.value,
            "completed_steps": result.completed_steps,
            "interrupted_reason": result.interrupted_reason,
            "checkpoint_token": result.checkpoint.resumption_token if result.checkpoint else None,
        }
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail=f"Task '{id}' not found.")
    except InvalidStateTransitionError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/{id}/pause", response_model=TaskResponse)
async def pause_task(
    id: UUID, payload: PauseTaskRequest = PauseTaskRequest(), service: TaskService = Depends(get_task_service)
):
    try:
        task = await service.pause_task(id, reason=payload.reason)
        return TaskResponse(**task.model_dump())
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail=f"Task '{id}' not found.")
    except InvalidStateTransitionError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/{id}/resume")
async def resume_task(
    id: UUID, payload: ResumeTaskRequest = ResumeTaskRequest(), service: TaskService = Depends(get_task_service)
):
    try:
        result = await service.resume_task(id, human_decision=payload.decision)
        return {
            "task_id": str(result.task_id),
            "status": result.status.value,
            "completed_steps": result.completed_steps,
            "interrupted_reason": result.interrupted_reason,
            "output": result.output,
        }
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail=f"Task '{id}' not found.")
    except InvalidStateTransitionError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post("/{id}/cancel", response_model=TaskResponse)
async def cancel_task(id: UUID, service: TaskService = Depends(get_task_service)):
    try:
        task = await service.cancel_task(id)
        return TaskResponse(**task.model_dump())
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail=f"Task '{id}' not found.")
    except InvalidStateTransitionError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/{id}/checkpoints", response_model=List[CheckpointResponse])
def get_task_checkpoints(id: UUID, service: TaskService = Depends(get_task_service)):
    try:
        service.get_task(id)  # Validate exists
        checkpoints = service.get_checkpoints(id)
        return [CheckpointResponse(**c.model_dump()) for c in checkpoints]
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail=f"Task '{id}' not found.")


@router.get("/{id}/events", response_model=List[EventResponse])
def get_task_events(id: UUID, dispatcher: EventDispatcher = Depends(get_event_dispatcher)):
    events = getattr(dispatcher, "get_events_for_task")(id)
    return [EventResponse(**e.model_dump()) for e in events]
