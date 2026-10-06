"""Task domain entities, statuses, and checkpoints."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.core.security import generate_resumption_token, hash_state


class TaskStatus(str, Enum):
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


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskCheckpoint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    step_index: int
    step_name: str
    state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    resumption_token: str = Field(default_factory=generate_resumption_token)
    state_hash: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __context: Any) -> None:
        if not self.state_hash:
            import json
            serialized = json.dumps(self.state_snapshot, sort_keys=True, default=str)
            self.state_hash = hash_state(serialized)


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    objective: str
    status: TaskStatus = TaskStatus.CREATED
    priority: TaskPriority = TaskPriority.MEDIUM
    current_step: int = 0
    parent_task: Optional[UUID] = None
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
