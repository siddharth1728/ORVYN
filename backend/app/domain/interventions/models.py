"""Human Intervention Request domain models prepared for voice telephony."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class InterventionUrgency(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InterventionResponseType(str, Enum):
    YES_NO = "YES_NO"
    CHOICE = "CHOICE"
    FREE_TEXT = "FREE_TEXT"
    CONFIRMATION = "CONFIRMATION"


class InterventionStatus(str, Enum):
    PENDING = "PENDING"
    CALL_IN_PROGRESS = "CALL_IN_PROGRESS"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class HumanInterventionRequest(BaseModel):
    """The structured contract consumed by the voice/telephony layer in Prompt 03."""
    request_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    reason: str
    question: str
    context: Dict[str, Any] = Field(default_factory=dict)
    urgency: InterventionUrgency = InterventionUrgency.MEDIUM
    options: Optional[List[str]] = None
    required_response_type: InterventionResponseType = InterventionResponseType.YES_NO
    status: InterventionStatus = InterventionStatus.PENDING
    resolution: Optional[Dict[str, Any]] = None
    resolved_by: Optional[str] = None  # "VOICE_CALL", "WEB_DASHBOARD"
    resolved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
