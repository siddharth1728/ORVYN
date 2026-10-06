"""Research agent domain models: Sources, Findings, and Reports."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ResearchSource(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    url: str
    domain: str
    published_at: Optional[datetime] = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_type: str = "WEB_SOURCE"  # "OFFICIAL_SITE", "JOB_BOARD", "NEWS", "ACADEMIC"
    reliability_score: float = 0.85
    content_snippet: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchFinding(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    fact_or_claim: str
    supporting_source_ids: List[UUID] = Field(default_factory=list)
    conflicting_source_ids: List[UUID] = Field(default_factory=list)
    is_interpretation: bool = False  # Distinguish verified facts from AI deductions
    confidence: float = 1.0
    notes: Optional[str] = None


class ResearchReport(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    objective: str
    summary: str
    sources: List[ResearchSource] = Field(default_factory=list)
    findings: List[ResearchFinding] = Field(default_factory=list)
    conflicts_identified: List[str] = Field(default_factory=list)
    uncertainties_and_gaps: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
