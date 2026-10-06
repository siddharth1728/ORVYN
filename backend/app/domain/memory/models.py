"""Persistent memory domain entities with strict provenance tracking."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    PROFILE = "PROFILE"          # User preferences, skills, constraints, explicit facts
    EPISODIC = "EPISODIC"        # Past interactions, task outcomes, decisions, milestones
    SEMANTIC = "SEMANTIC"        # Factual research, extracted knowledge, company insights
    DECISION = "DECISION"        # Historical human judgments & rationale
    RESEARCH = "RESEARCH"        # Verified findings & evidence from the web
    TASK = "TASK"                # Checkpoints & execution history
    INTERACTION = "INTERACTION"  # Transcripts & call dialogues


class MemorySourceType(str, Enum):
    USER = "USER"
    WEB_SOURCE = "WEB_SOURCE"
    API = "API"
    SYSTEM = "SYSTEM"
    AGENT_INFERENCE = "AGENT_INFERENCE"
    VOICE_CALL = "VOICE_CALL"


class MemoryProvenance(BaseModel):
    """Immutable provenance record answering who, where, when, and confidence."""
    source_type: MemorySourceType
    source_reference: str  # URL, Call ID, or document reference
    confidence: float = 1.0
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_by_user: bool = False
    notes: Optional[str] = None


class UserProfilePreference(BaseModel):
    """Explicit, durable user profile attribute."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    category: str  # "skill", "role", "tech", "location", "work_mode", "constraint", "goal"
    key: str
    value: Any
    provenance: MemoryProvenance
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EpisodicMemoryRecord(BaseModel):
    """Notable past event queryable by task and time."""
    id: UUID = Field(default_factory=uuid4)
    task_id: Optional[UUID] = None
    event_type: str
    summary: str
    outcome: str
    provenance: MemoryProvenance
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SemanticMemoryItem(BaseModel):
    """Fact or research knowledge stored with vector embedding."""
    id: UUID = Field(default_factory=uuid4)
    content: str
    embedding: Optional[List[float]] = None
    provenance: MemoryProvenance
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Memory(BaseModel):
    """Unified memory entity."""
    id: UUID = Field(default_factory=uuid4)
    type: MemoryType
    content: str
    provenance: MemoryProvenance
    embedding: Optional[List[float]] = None
    related_entity_id: Optional[UUID] = None
    related_entity_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemorySearchResult(BaseModel):
    """Retrieved memory with calculated similarity score and provenance."""
    memory: Memory
    relevance_score: float
    provenance: MemoryProvenance
    confidence: float
