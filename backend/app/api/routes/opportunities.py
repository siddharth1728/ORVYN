"""Opportunity intelligence API routes for discovered positions and score explanations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.application.opportunity_service.service import opportunity_service
from app.domain.opportunities.models import (
    Opportunity,
    OpportunityScore,
    OpportunityStatus,
    OpportunityType,
)

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


class IngestOpportunityRequest(BaseModel):
    title: str = Field(..., min_length=1)
    organization: str = Field(..., min_length=1)
    opportunity_type: OpportunityType = OpportunityType.INTERNSHIP
    location: Optional[str] = None
    is_remote: bool = False
    requires_relocation: bool = False
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    application_url: Optional[str] = None
    source_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScoreOpportunityRequest(BaseModel):
    user_profile: Dict[str, Any]


@router.get("", response_model=List[Opportunity])
async def list_opportunities(
    min_score: Optional[float] = Query(default=None, ge=0.0, le=100.0),
    opportunity_type: Optional[OpportunityType] = None,
    status_filter: Optional[OpportunityStatus] = None,
) -> List[Opportunity]:
    opps = opportunity_service.list_opportunities(min_score=min_score)
    if opportunity_type:
        opps = [o for o in opps if o.opportunity_type == opportunity_type]
    if status_filter:
        opps = [o for o in opps if o.status == status_filter]
    return opps


@router.post("", response_model=Opportunity, status_code=status.HTTP_201_CREATED)
async def ingest_opportunity(payload: IngestOpportunityRequest) -> Opportunity:
    return await opportunity_service.ingest_opportunity(
        title=payload.title,
        organization=payload.organization,
        opportunity_type=payload.opportunity_type,
        location=payload.location,
        is_remote=payload.is_remote,
        requires_relocation=payload.requires_relocation,
        required_skills=payload.required_skills,
        preferred_skills=payload.preferred_skills,
        deadline=payload.deadline,
        application_url=payload.application_url,
        source_url=payload.source_url,
        metadata=payload.metadata,
    )


@router.get("/{opp_id}", response_model=Opportunity)
async def get_opportunity(opp_id: UUID) -> Opportunity:
    opp = opportunity_service.get_opportunity(opp_id)
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Opportunity {opp_id} not found")
    return opp


@router.post("/{opp_id}/score", response_model=OpportunityScore)
async def score_opportunity(opp_id: UUID, payload: ScoreOpportunityRequest) -> OpportunityScore:
    opp = opportunity_service.get_opportunity(opp_id)
    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Opportunity {opp_id} not found")
    return opportunity_service.score_opportunity(opp, payload.user_profile)
