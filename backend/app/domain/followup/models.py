"""Follow-Up Agent domain models, conditions, and scheduling policies."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ConditionType(str, Enum):
    TIME = "TIME"                          # Scheduled timestamp
    DEADLINE = "DEADLINE"                  # Proximity to a target deadline
    NO_RESPONSE = "NO_RESPONSE"            # Elapsed time without reply
    NEW_INFORMATION = "NEW_INFORMATION"    # Change in external state/data
    THRESHOLD = "THRESHOLD"                # Numeric or match score limit
    TASK_COMPLETION = "TASK_COMPLETION"    # Prerequisite task finished
    HUMAN_REQUIRED = "HUMAN_REQUIRED"      # Needs human authorization


class FollowUpStatus(str, Enum):
    PENDING = "PENDING"
    WAITING = "WAITING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    ESCALATED = "ESCALATED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class TriggerCondition(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    condition_type: ConditionType
    description: str
    target_value: Any
    is_met: bool = False
    last_evaluated_at: Optional[datetime] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ConditionEvaluation(BaseModel):
    condition_id: UUID
    is_met: bool
    explanation: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FollowUpTarget(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    title: str
    target_entity: str  # e.g., "Razorpay Application"
    action_to_take: str # e.g., "Send polite status check" or "Alert human"
    conditions: List[TriggerCondition] = Field(default_factory=list)
    status: FollowUpStatus = FollowUpStatus.WAITING
    attempt_count: int = 0
    max_attempts: int = 3
    cooldown_seconds: int = 86400  # Default 24 hours between attempts to prevent spam
    last_attempt_at: Optional[datetime] = None
    next_check_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def can_attempt(self, now: datetime) -> bool:
        if self.status in [FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED, FollowUpStatus.EXPIRED]:
            return False
        if self.attempt_count >= self.max_attempts:
            return False
        if self.expires_at and now >= self.expires_at:
            return False
        if self.last_attempt_at:
            elapsed = (now - self.last_attempt_at).total_seconds()
            if elapsed < self.cooldown_seconds:
                return False
        return True
