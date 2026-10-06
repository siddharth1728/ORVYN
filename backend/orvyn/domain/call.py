"""Voice telephony and call session domain models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class CallStatus(str, Enum):
    INITIATED = "INITIATED"
    RINGING = "RINGING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BUSY = "BUSY"
    NO_ANSWER = "NO_ANSWER"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class VoiceCallSession(BaseModel):
    """Tracks the lifecycle of an outbound telephony call to the user."""
    id: UUID = Field(default_factory=uuid4)
    intervention_id: UUID
    task_id: UUID
    external_call_sid: Optional[str] = None
    to_phone_number: str
    status: CallStatus = CallStatus.INITIATED
    transcript: str = ""
    extracted_decision: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    duration_seconds: int = 0
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VoiceDecisionResult(BaseModel):
    """Normalized payload resulting from an analyzed voice conversation."""
    call_id: UUID
    task_id: UUID
    transcript: str
    decision: Dict[str, Any]
    confidence: float
    confirmed_by_user: bool
    duration_seconds: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
