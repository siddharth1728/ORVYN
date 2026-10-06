"""Opportunity intelligence domain models, scoring, and deduplication."""

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
    TECHNICAL_PROGRAM = "TECHNICAL_PROGRAM"
    FELLOWSHIP = "FELLOWSHIP"
    EVENT = "EVENT"


class OpportunityStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    EVALUATING = "EVALUATING"
    MATCHED = "MATCHED"
    SHORTLISTED = "SHORTLISTED"
    AWAITING_HUMAN = "AWAITING_HUMAN"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class OpportunityRequirement(BaseModel):
    name: str
    requirement_type: str = "SKILL"  # "SKILL", "EDUCATION", "YEARS_EXPERIENCE", "CITIZENSHIP"
    is_mandatory: bool = True
    details: Optional[str] = None


class OpportunityScore(BaseModel):
    score: float = 0.0  # 0 to 100
    match_level: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW"
    positive_reasons: List[str] = Field(default_factory=list)
    negative_reasons: List[str] = Field(default_factory=list)
    concerns_or_gaps: List[str] = Field(default_factory=list)
    missing_user_info: List[str] = Field(default_factory=list)
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Opportunity(BaseModel):
    """Canonical deduplicated opportunity entity."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    organization: str
    opportunity_type: OpportunityType = OpportunityType.INTERNSHIP
    description: str = ""
    location: Optional[str] = None
    is_remote: bool = False
    requires_relocation: bool = False
    eligibility_criteria: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    application_url: Optional[str] = None
    source_urls: List[str] = Field(default_factory=list)
    canonical_hash: str = ""
    status: OpportunityStatus = OpportunityStatus.DISCOVERED
    score: Optional[OpportunityScore] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
