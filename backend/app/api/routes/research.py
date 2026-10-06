"""Research API routes for evidence synthesis, sources, and auditability."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.application.research_service.service import research_service
from app.domain.research.models import ResearchReport

router = APIRouter(prefix="/research", tags=["Research"])


class ConductResearchRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    task_id: Optional[UUID] = None
    max_sources: int = Field(default=5, ge=1, le=20)


@router.post("", response_model=ResearchReport, status_code=status.HTTP_201_CREATED)
async def conduct_research(payload: ConductResearchRequest) -> ResearchReport:
    return await research_service.conduct_research(
        topic=payload.topic,
        task_id=payload.task_id,
        max_sources=payload.max_sources,
    )


@router.get("/{report_id}", response_model=ResearchReport)
async def get_research_report(report_id: UUID) -> ResearchReport:
    report = research_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research report {report_id} not found")
    return report
