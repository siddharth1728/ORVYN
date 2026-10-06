"""Multi-task planning and dependency graph domain models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class TaskDependency(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    step_id: UUID
    depends_on_step_id: UUID
    required_status: StepStatus = StepStatus.COMPLETED


class PlanStep(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    plan_id: UUID
    step_index: int
    name: str
    description: str
    action: str
    tool_name: Optional[str] = None
    assigned_agent: str = "CoreAgent"  # "ResearchAgent", "OpportunityAgent", "FollowUpAgent"
    dependencies: List[UUID] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 120
    checkpoint_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class Plan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    objective: str
    steps: List[PlanStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_step(self, step_id: UUID) -> Optional[PlanStep]:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None

    def get_ready_steps(self) -> List[PlanStep]:
        """Identifies steps whose prerequisites are fully met."""
        completed_ids = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}
        ready = []
        for s in self.steps:
            if s.status in [StepStatus.PENDING, StepStatus.READY]:
                if all(dep in completed_ids for dep in s.dependencies):
                    ready.append(s)
        return ready

    def is_complete(self) -> bool:
        return all(s.status in [StepStatus.COMPLETED, StepStatus.SKIPPED] for s in self.steps)

    def has_failures(self) -> bool:
        return any(s.status == StepStatus.FAILED for s in self.steps)


class TaskExecutionContext(BaseModel):
    task_id: UUID
    plan_id: UUID
    active_step_id: Optional[UUID] = None
    completed_step_ids: List[UUID] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
