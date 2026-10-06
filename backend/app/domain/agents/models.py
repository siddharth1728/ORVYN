"""AgentRun and execution tracking domain entities."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class AgentRunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class AgentRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    agent_name: str
    status: AgentRunStatus = AgentRunStatus.PENDING
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    errors: Optional[str] = None
    usage_metadata: Dict[str, Any] = Field(default_factory=dict)
