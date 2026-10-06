"""Intermediate agent artifacts models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    RESEARCH_REPORT = "RESEARCH_REPORT"
    OPPORTUNITY_LIST = "OPPORTUNITY_LIST"
    COMPARISON_RESULT = "COMPARISON_RESULT"
    FOLLOWUP_PLAN = "FOLLOWUP_PLAN"
    DECISION_REQUEST = "DECISION_REQUEST"


class Artifact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    artifact_type: ArtifactType
    title: str
    content: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    created_by_agent: str = "CoreAgent"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
