"""Plan API routes for inspecting and generating DAG task plans."""

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.application.planning_engine.planner import DependencyEngine, MultiTaskPlanner
from app.domain.planning.models import Plan, PlanStep, StepStatus

router = APIRouter(prefix="/plans", tags=["Plans"])

# In-memory store for fast plan querying (synchronized with DB)
_plans_store: Dict[UUID, Plan] = {}


class CreatePlanRequest(BaseModel):
    task_id: UUID
    objective: str


@router.post("", response_model=Plan, status_code=status.HTTP_201_CREATED)
async def create_plan(payload: CreatePlanRequest) -> Plan:
    plan = await MultiTaskPlanner.generate_plan(task_id=payload.task_id, objective=payload.objective)
    _plans_store[plan.id] = plan
    return plan


@router.get("", response_model=List[Plan])
async def list_plans() -> List[Plan]:
    return list(_plans_store.values())


@router.get("/{plan_id}", response_model=Plan)
async def get_plan(plan_id: UUID) -> Plan:
    plan = _plans_store.get(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")
    return plan


@router.get("/{plan_id}/dependencies", response_model=Dict[str, List[PlanStep]])
async def get_plan_dependencies(plan_id: UUID) -> Dict[str, List[PlanStep]]:
    plan = _plans_store.get(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {plan_id} not found")
    return DependencyEngine.evaluate_plan_dependencies(plan)
