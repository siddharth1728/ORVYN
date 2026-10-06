"""Core Task domain models and states."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TaskState(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    CALLING = "CALLING"
    AWAITING_RESPONSE = "AWAITING_RESPONSE"
    RESUMING = "RESUMING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PlanStep(BaseModel):
    """A discrete executable step in a TaskPlan."""
    step_index: int
    name: str
    description: str
    tool_required: Optional[str] = None
    input_parameters: Dict[str, Any] = Field(default_factory=dict)
    is_completed: bool = False
    result: Optional[Any] = None


class TaskPlan(BaseModel):
    """Decomposed execution plan for achieving an objective."""
    objective: str
    steps: List[PlanStep] = Field(default_factory=list)


class Task(BaseModel):
    """Primary aggregate root representing an autonomous workflow."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str
    objective: str
    current_state: TaskState = TaskState.CREATED
    current_step_index: int = 0
    plan: Optional[TaskPlan] = None
    state_metadata: Dict[str, Any] = Field(default_factory=dict)
    error_details: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
