"""Multi-agent coordination and handoff models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class AgentHandoff(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    from_agent: str  # e.g., "OpportunityAgent"
    to_agent: str    # e.g., "ResearchAgent"
    reason: str      # e.g., "Investigate employer background & relocation policies"
    context: Dict[str, Any] = Field(default_factory=dict)
    artifact_ids: List[UUID] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
