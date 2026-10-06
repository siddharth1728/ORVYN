"""Dependency-aware Multi-Task Planning Engine."""

from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

from app.domain.events.dispatcher import dispatcher
from app.domain.events.models import Event
from app.domain.planning.models import Plan, PlanStep, StepStatus


class DependencyEngine:
    """Evaluates DAG dependency status and resolves step execution order."""

    @classmethod
    def evaluate_plan_dependencies(cls, plan: Plan) -> Dict[str, List[PlanStep]]:
        """Classifies all plan steps based on dependency satisfaction."""
        completed_ids = {s.id for s in plan.steps if s.status == StepStatus.COMPLETED}
        failed_ids = {s.id for s in plan.steps if s.status == StepStatus.FAILED}

        ready: List[PlanStep] = []
        blocked: List[PlanStep] = []
        running: List[PlanStep] = []
        waiting: List[PlanStep] = []
        completed: List[PlanStep] = []

        for step in plan.steps:
            if step.status == StepStatus.COMPLETED:
                completed.append(step)
            elif step.status == StepStatus.RUNNING:
                running.append(step)
            elif step.status == StepStatus.WAITING:
                waiting.append(step)
            elif step.status == StepStatus.BLOCKED:
                blocked.append(step)
            else:
                # Check for upstream failures
                has_failed_dep = any(dep_id in failed_ids for dep_id in step.dependencies)
                if has_failed_dep:
                    step.status = StepStatus.BLOCKED
                    step.error_message = "Upstream prerequisite step failed."
                    blocked.append(step)
                    continue

                # Check if all prerequisites completed
                all_deps_satisfied = all(dep_id in completed_ids for dep_id in step.dependencies)
                if all_deps_satisfied:
                    step.status = StepStatus.READY
                    ready.append(step)
                else:
                    step.status = StepStatus.PENDING
                    waiting.append(step)

        return {
            "ready": ready,
            "blocked": blocked,
            "running": running,
            "waiting": waiting,
            "completed": completed,
        }

    @classmethod
    def mark_step_completed(cls, plan: Plan, step_id: UUID, outputs: Dict[str, Any]) -> None:
        step = plan.get_step(step_id)
        if step:
            step.status = StepStatus.COMPLETED
            step.outputs = outputs
            # Re-evaluate remaining dependencies
            cls.evaluate_plan_dependencies(plan)

    @classmethod
    def mark_step_failed(cls, plan: Plan, step_id: UUID, error: str) -> None:
        step = plan.get_step(step_id)
        if step:
            step.status = StepStatus.FAILED
            step.error_message = error
            # Re-evaluate dependencies so downstream steps are marked BLOCKED
            cls.evaluate_plan_dependencies(plan)


class MultiTaskPlanner:
    """Generates structured DAG plans for high-level user objectives."""

    @classmethod
    async def generate_plan(cls, task_id: UUID, objective: str) -> Plan:
        """Decomposes intent into structured steps with explicit dependencies."""
        step0_id = uuid4()
        step1_id = uuid4()
        step2_id = uuid4()
        step3_id = uuid4()

        steps: List[PlanStep] = [
            PlanStep(
                id=step0_id,
                plan_id=uuid4(),
                step_index=0,
                name="discover_opportunities",
                description="Search relevant job boards and databases for matching positions.",
                action="discover_and_extract",
                tool_name="search_web",
                assigned_agent="OpportunityAgent",
                dependencies=[],
                status=StepStatus.READY,
            ),
            PlanStep(
                id=step1_id,
                plan_id=uuid4(),
                step_index=1,
                name="evaluate_matches",
                description="Deduplicate candidates, score relevance against profile, and research relocation policies.",
                action="score_and_research",
                tool_name="research",
                assigned_agent="ResearchAgent",
                dependencies=[step0_id],
                status=StepStatus.PENDING,
            ),
            PlanStep(
                id=step2_id,
                plan_id=uuid4(),
                step_index=2,
                name="finalize_recommendation",
                description="Synthesize final recommendation and establish condition-based follow-up schedule.",
                action="schedule_followup_tracking",
                tool_name="create_followup",
                assigned_agent="FollowUpAgent",
                dependencies=[step1_id],
                status=StepStatus.PENDING,
            ),
        ]


        plan = Plan(
            task_id=task_id,
            objective=objective,
            steps=steps,
        )

        for s in plan.steps:
            s.plan_id = plan.id

        await dispatcher.dispatch(
            Event(
                event_type="PLAN_CREATED",
                task_id=task_id,
                payload={"step_count": len(steps), "objective": objective},
                source="planner",
            )
        )

        return plan
