"""Opportunity intelligence domain models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class OpportunityType(str, Enum):
    INTERNSHIP = "INTERNSHIP"
    FULL_TIME = "FULL_TIME"
    RESEARCH = "RESEARCH"
    HACKATHON = "HACKATHON"
    COMPETITION = "COMPETITION"
    SCHOLARSHIP = "SCHOLARSHIP"


class OpportunityStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    EVALUATING = "EVALUATING"
    REQUIRES_INPUT = "REQUIRES_INPUT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    EXPIRED = "EXPIRED"


class Opportunity(BaseModel):
    """An opportunity discovered and evaluated by the Opportunity Agent."""
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str
    organization: str
    opportunity_type: OpportunityType
    url: Optional[str] = None
    location: Optional[str] = None
    is_remote: bool = False
    requires_relocation: bool = False
    deadline: Optional[datetime] = None
    requirements: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    status: OpportunityStatus = OpportunityStatus.DISCOVERED
    metadata: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
