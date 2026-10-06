"""Decision domain entities."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Decision(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    question: str
    context: Dict[str, Any] = Field(default_factory=dict)
    answer: Optional[Dict[str, Any]] = None
    source: str = "human_voice"  # "human_voice", "human_web", "autonomous"
    confidence: float = 1.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
