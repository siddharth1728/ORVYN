"""Memory system domain models and provenance tracking."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class MemoryCategory(str, Enum):
    PROFILE = "PROFILE"          # User preferences, skills, constraints
    TASK = "TASK"                # Checkpoints, steps, outputs
    DECISION = "DECISION"        # Historical human interventions & outcomes
    OPPORTUNITY = "OPPORTUNITY"  # Discovered roles and their statuses
    INTERACTION = "INTERACTION"  # Transcripts and user communications
    RESEARCH = "RESEARCH"        # Verified facts extracted from web/documents


class MemoryProvenance(BaseModel):
    """Immutable evidence trail for every stored memory item."""
    source_type: str  # "VOICE_CALL" | "WEB_SCRAPE" | "USER_PROFILE" | "DIRECT_INPUT"
    source_reference: str  # URL or Call ID or Document identifier
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_by_human: bool = False
    confidence: float = 1.0


class MemoryItem(BaseModel):
    """Discrete factual memory item with strict provenance."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    category: MemoryCategory
    content: str
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    provenance: MemoryProvenance
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
