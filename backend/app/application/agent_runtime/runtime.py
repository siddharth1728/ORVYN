"""Autonomous Agent Runtime: Multi-agent coordination, DAG dependencies, and memory loop."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.application.agents.specialized import (
    AgentCoordinator,
    FollowUpAgent,
    OpportunityAgent,
    ResearchAgent,
)
from app.application.decision_service.engine import DecisionContext, DecisionEngine, DecisionOutcome
from app.application.memory_service.service import memory_service
from app.application.planning_engine.planner import DependencyEngine, MultiTaskPlanner
from app.core.logging import logger
from app.domain.events.dispatcher import dispatcher
from app.domain.events.models import Event
from app.domain.interventions.models import HumanInterventionRequest
from app.domain.planning.models import Plan, PlanStep, StepStatus
from app.domain.policies.models import AgentPolicy, ToolPermission, default_policy
from app.domain.tasks.models import Task, TaskCheckpoint, TaskStatus
from app.domain.tasks.state_machine import TaskStateMachine
from app.infrastructure.tools.base import ToolCall, tool_registry


class AgentContext(BaseModel):
    task: Task
    plan: Optional[Plan] = None
    working_memory: Dict[str, Any] = Field(default_factory=dict)
    checkpoints: List[TaskCheckpoint] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    pending_intervention: Optional[HumanInterventionRequest] = None
    policy: AgentPolicy = Field(default_factory=AgentPolicy)


class AgentResult(BaseModel):
    task_id: UUID
    status: TaskStatus
    completed_steps: int
    output: Dict[str, Any] = Field(default_factory=dict)
    checkpoint: Optional[TaskCheckpoint] = None
    intervention_request: Optional[HumanInterventionRequest] = None
    interrupted_reason: Optional[str] = None


class Agent:
    """Core autonomous runtime coordinating planning, specialized agents, tools, and decisions."""

    def __init__(
        self,
        name: str = "ORVYN-Core",
        policy: Optional[AgentPolicy] = None,
    ) -> None:
        self.name = name
        self.policy = policy or default_policy
        self.opportunity_agent = OpportunityAgent()
        self.research_agent = ResearchAgent()
        self.followup_agent = FollowUpAgent()

    async def run(self, context: AgentContext, max_iterations: int = 15) -> AgentResult:
        task = context.task

        # 1. Start lifecycle: CREATED -> PLANNING
        if task.status == TaskStatus.CREATED:
            TaskStateMachine.transition(task, TaskStatus.PLANNING, reason="Generating task DAG plan")
            await dispatcher.dispatch(
                Event(event_type="TASK_STARTED", task_id=task.id, payload={"objective": task.objective})
            )

        # 2. Plan Generation: build or restore multi-step plan
        if not context.plan:
            context.plan = await MultiTaskPlanner.generate_plan(task.id, task.objective)
            task.metadata["plan"] = context.plan.model_dump()

        # 3. Transition PLANNING -> EXECUTING
        if task.status == TaskStatus.PLANNING:
            TaskStateMachine.transition(task, TaskStatus.EXECUTING, reason="Plan ready, starting DAG execution")

        # 4. Dependency-Aware Execution Loop
        while max_iterations > 0 and not context.plan.is_complete():
            max_iterations -= 1

            # Retrieve ready steps according to DAG
            dep_status = DependencyEngine.evaluate_plan_dependencies(context.plan)
            ready_steps = dep_status["ready"]

            if not ready_steps:
                if dep_status["blocked"]:
                    TaskStateMachine.transition(task, TaskStatus.BLOCKED, reason="Plan steps blocked by dependency failure")
                    return AgentResult(
                        task_id=task.id,
                        status=task.status,
                        completed_steps=len(dep_status["completed"]),
                        interrupted_reason="Blocked by dependency failure",
                    )
                # No more steps ready or currently blocked
                break

            step = ready_steps[0]
            step.status = StepStatus.RUNNING

            # Retrieve relevant memories for the step
            memories = await memory_service.search_memories(f"{task.objective} {step.name}", limit=3)
            context.working_memory["recent_memories"] = [m.memory.content for m in memories]

            # Determine Tool Permission
            tool_perm = ToolPermission.READ_ONLY
            if step.tool_name:
                t = tool_registry.get_tool(step.tool_name)
                if t:
                    tool_perm = t.definition.permission

            # Decision Engine Gatekeeper Check
            # Check if this step requires relocation or specific preference
            requires_pref = "relocation" if "relocation" in step.name or "match" in step.name else None

            # Pull candidate opportunity info if available in working memory
            opp_info = context.working_memory.get("discovered_opportunity", {})

            decision_ctx = DecisionContext(
                task_id=task.id,
                current_step=step.step_index,
                step_name=step.name,
                proposed_action=step.action,
                tool_permission=tool_perm,
                requires_preference=requires_pref,
                known_preferences=context.user_preferences,
                payload=opp_info if opp_info else {"step": step.name, "location": "Bangalore", "organization": "Razorpay"},
            )

            decision = DecisionEngine.evaluate(decision_ctx, self.policy)

            # Check if Human Intervention is required
            if decision.outcome in [DecisionOutcome.CALL_HUMAN, DecisionOutcome.ASK_HUMAN]:
                step.status = StepStatus.WAITING

                # Capture atomic checkpoint before pausing
                checkpoint = TaskCheckpoint(
                    task_id=task.id,
                    step_index=step.step_index,
                    step_name=step.name,
                    state_snapshot=context.working_memory,
                )
                context.checkpoints.append(checkpoint)
                context.pending_intervention = decision.intervention_request

                # Transition state machine
                TaskStateMachine.transition(task, TaskStatus.HUMAN_REQUIRED, reason=decision.reason)
                if decision.outcome == DecisionOutcome.CALL_HUMAN:
                    TaskStateMachine.transition(task, TaskStatus.CALLING, reason="Urgent decision requires voice intervention")
                    TaskStateMachine.transition(task, TaskStatus.AWAITING_RESPONSE, reason="Call placed, awaiting human response")

                await dispatcher.dispatch(
                    Event(
                        event_type="HUMAN_INTERVENTION_CREATED",
                        task_id=task.id,
                        payload={
                            "reason": decision.reason,
                            "question": decision.intervention_request.question if decision.intervention_request else "",
                            "checkpoint_token": checkpoint.resumption_token,
                            "urgency": decision.intervention_request.urgency.value if decision.intervention_request else "MEDIUM",
                        },
                        source="agent_runtime",
                    )
                )

                return AgentResult(
                    task_id=task.id,
                    status=task.status,
                    completed_steps=len(dep_status["completed"]),
                    checkpoint=checkpoint,
                    intervention_request=decision.intervention_request,
                    interrupted_reason=decision.reason,
                )

            # Step Execution through Specialized Agent or Tool
            try:
                output = await self._execute_assigned_step(step, context)
                DependencyEngine.mark_step_completed(context.plan, step.id, output)
                context.working_memory[step.name] = output
                task.current_step = step.step_index + 1

                # Save atomic step checkpoint
                chk = TaskCheckpoint(
                    task_id=task.id,
                    step_index=task.current_step,
                    step_name=step.name,
                    state_snapshot=context.working_memory,
                )
                context.checkpoints.append(chk)

            except Exception as err:
                logger.error(f"Error executing step {step.name}: {err}", exc_info=True)
                step.retry_count += 1
                if step.retry_count >= step.max_retries:
                    DependencyEngine.mark_step_failed(context.plan, step.id, str(err))
                    TaskStateMachine.transition(task, TaskStatus.FAILED, reason=str(err))
                    return AgentResult(
                        task_id=task.id,
                        status=task.status,
                        completed_steps=len(dep_status["completed"]),
                        interrupted_reason=str(err),
                    )

        # 5. Check if complete
        if context.plan.is_complete():
            TaskStateMachine.transition(task, TaskStatus.COMPLETED, reason="All planned steps executed successfully")
            await dispatcher.dispatch(
                Event(event_type="TASK_COMPLETED", task_id=task.id, payload={"output": context.working_memory})
            )

        return AgentResult(
            task_id=task.id,
            status=task.status,
            completed_steps=len([s for s in context.plan.steps if s.status == StepStatus.COMPLETED]),
            output=context.working_memory,
            checkpoint=context.checkpoints[-1] if context.checkpoints else None,
        )

    async def _execute_assigned_step(self, step: PlanStep, context: AgentContext) -> Dict[str, Any]:
        """Dispatches step execution to specialized agents or general tool registry."""
        task_id = context.task.id

        if step.assigned_agent == "OpportunityAgent":
            await AgentCoordinator.record_handoff(
                task_id=task_id,
                from_agent=self.name,
                to_agent="OpportunityAgent",
                reason=f"Execute {step.name}",
            )
            result = await self.opportunity_agent.execute_discovery(
                task_id=task_id,
                objective=context.task.objective,
                user_profile=context.user_preferences,
            )
            context.working_memory["discovered_opportunity"] = result
            return result

        elif step.assigned_agent == "ResearchAgent":
            await AgentCoordinator.record_handoff(
                task_id=task_id,
                from_agent=self.name,
                to_agent="ResearchAgent",
                reason="Investigate top organization background & relocation",
            )
            org = context.working_memory.get("discovered_opportunity", {}).get("organization", "Razorpay")
            return await self.research_agent.execute_research(task_id=task_id, organization=org)

        elif step.assigned_agent == "FollowUpAgent":
            await AgentCoordinator.record_handoff(
                task_id=task_id,
                from_agent=self.name,
                to_agent="FollowUpAgent",
                reason="Set up tracking & scheduled check",
            )
            org = context.working_memory.get("discovered_opportunity", {}).get("organization", "Razorpay")
            return await self.followup_agent.setup_tracking(
                task_id=task_id,
                title=f"Application tracking for {org}",
                target_entity=org,
            )

        else:
            # General Tool execution via registry
            tool_call = ToolCall(call_id=f"step-{step.step_index}", tool_name=step.tool_name or "get_current_time")
            res = await tool_registry.execute(tool_call, self.policy)
            return {"tool_output": res.output, "success": res.success}

    async def resume(
        self,
        context: AgentContext,
        checkpoint: TaskCheckpoint,
        human_decision: Dict[str, Any],
    ) -> AgentResult:
        """Resumes interrupted task from checkpoint with structured human decision applied."""
        task = context.task

        # 1. Restore working memory & checkpoint snapshot
        context.working_memory = dict(checkpoint.state_snapshot)
        context.working_memory["human_decision"] = human_decision
        task.current_step = checkpoint.step_index

        # 2. Merge human decision into user profile memory
        if "relocation" in human_decision:
            context.user_preferences["willing_to_relocate"] = human_decision["relocation"]
            context.user_preferences["relocation"] = human_decision["relocation"]
            # Store in persistent memory
            await memory_service.set_profile_preference(
                user_id=task.id,
                category="location",
                key="willing_to_relocate",
                value=human_decision["relocation"],
                source_reference="voice_call" if human_decision.get("channel") == "voice_call" else "user_decision",
            )

        # 3. Transition AWAITING_RESPONSE -> RESUMING -> EXECUTING
        if task.status in [TaskStatus.AWAITING_RESPONSE, TaskStatus.HUMAN_REQUIRED, TaskStatus.BLOCKED]:
            TaskStateMachine.transition(task, TaskStatus.RESUMING, reason="Human decision provided")
            TaskStateMachine.transition(task, TaskStatus.EXECUTING, reason="Resuming DAG execution")

        # 4. Mark the waiting step completed in plan
        if context.plan:
            waiting_step = context.plan.get_step(context.plan.steps[checkpoint.step_index].id)
            if waiting_step:
                DependencyEngine.mark_step_completed(
                    context.plan, waiting_step.id, {"human_decision": human_decision}
                )

        await dispatcher.dispatch(
            Event(
                event_type="TASK_RESUMED",
                task_id=task.id,
                payload={"resumed_from_step": checkpoint.step_index, "decision": human_decision},
                source="agent_runtime",
            )
        )

        return await self.run(context)
