"""Intervention request and decision domain models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class UrgencyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InterventionReason(str, Enum):
    AMBIGUOUS_PREFERENCE = "AMBIGUOUS_PREFERENCE"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    IRREVERSIBLE_ACTION = "IRREVERSIBLE_ACTION"
    HIGH_IMPACT_DECISION = "HIGH_IMPACT_DECISION"
    MISSING_CRITICAL_INFO = "MISSING_CRITICAL_INFO"
    CONFLICTING_OBJECTIVES = "CONFLICTING_OBJECTIVES"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"


class InterventionRequest(BaseModel):
    """Structured request generated when an autonomous step cannot proceed safely."""
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    checkpoint_id: UUID
    reason: InterventionReason
    question: str
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    context: Dict[str, Any] = Field(default_factory=dict)
    options: Optional[list[str]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InterventionDecision(BaseModel):
    """The structured decision extracted from human input (voice call or manual override)."""
    intervention_id: UUID
    task_id: UUID
    decision_payload: Dict[str, Any]
    source: str = "VOICE_CALL"  # "VOICE_CALL" | "WEB_OVERRIDE"
    confidence: float = 1.0
    confirmed_by_user: bool = True
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
