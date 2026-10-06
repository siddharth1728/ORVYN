"""Decision Engine (Second Iteration): Multi-factor evaluation and intervention generator."""

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.domain.interventions.models import (
    HumanInterventionRequest,
    InterventionResponseType,
    InterventionStatus,
    InterventionUrgency,
)
from app.domain.policies.models import AgentPolicy, ToolPermission, default_policy


class DecisionOutcome(str, Enum):
    CONTINUE = "CONTINUE"
    WAIT = "WAIT"
    RETRY = "RETRY"
    ESCALATE = "ESCALATE"
    ASK_HUMAN = "ASK_HUMAN"
    CALL_HUMAN = "CALL_HUMAN"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"


class DecisionContext(BaseModel):
    task_id: UUID
    current_step: int
    step_name: str
    proposed_action: str
    tool_permission: ToolPermission = ToolPermission.READ_ONLY
    requires_preference: Optional[str] = None
    known_preferences: Dict[str, Any] = Field(default_factory=dict)
    urgency: str = "MEDIUM"
    confidence: float = 1.0
    retry_count: int = 0
    max_retries: int = 3
    deadline_near: bool = False
    payload: Dict[str, Any] = Field(default_factory=dict)


class DecisionResult(BaseModel):
    outcome: DecisionOutcome
    reason: str
    confidence: float = 1.0
    intervention_request: Optional[HumanInterventionRequest] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DecisionEngine:
    """Second-iteration central gatekeeper combining policy, permissions, memory, and confidence."""

    @classmethod
    def evaluate(
        cls,
        context: DecisionContext,
        policy: Optional[AgentPolicy] = None,
    ) -> DecisionResult:
        pol = policy or default_policy

        # 1. Check Max Retries / Failure condition
        if context.retry_count >= context.max_retries:
            return DecisionResult(
                outcome=DecisionOutcome.FAIL,
                reason=f"Exceeded maximum allowable retries ({context.max_retries}) on step '{context.step_name}'.",
                confidence=1.0,
            )

        # 2. Tool Permission: Explicit Human Approval Required
        if context.tool_permission == ToolPermission.HUMAN_APPROVAL_REQUIRED:
            intervention = HumanInterventionRequest(
                task_id=context.task_id,
                reason=f"Action '{context.proposed_action}' requires mandatory human sign-off.",
                question=f"Do you authorize executing '{context.proposed_action}'?",
                context=context.payload,
                urgency=InterventionUrgency.HIGH,
                options=["Authorize", "Reject"],
                required_response_type=InterventionResponseType.CONFIRMATION,
            )
            return DecisionResult(
                outcome=DecisionOutcome.CALL_HUMAN if context.urgency in ["HIGH", "CRITICAL"] else DecisionOutcome.ASK_HUMAN,
                reason="Tool requires explicit human approval.",
                confidence=1.0,
                intervention_request=intervention,
            )

        # 3. Tool Permission: External Action with Policy Enforcement
        if context.tool_permission == ToolPermission.EXTERNAL_ACTION and pol.require_approval_for_external_actions:
            intervention = HumanInterventionRequest(
                task_id=context.task_id,
                reason=f"Action '{context.proposed_action}' interacts with an external system.",
                question=f"ORVYN is ready to perform external action '{context.proposed_action}'. Should it proceed?",
                context=context.payload,
                urgency=InterventionUrgency.MEDIUM,
                options=["Approve", "Cancel"],
                required_response_type=InterventionResponseType.YES_NO,
            )
            return DecisionResult(
                outcome=DecisionOutcome.CALL_HUMAN if context.urgency == "HIGH" else DecisionOutcome.ASK_HUMAN,
                reason="Policy requires approval for external actions.",
                confidence=1.0,
                intervention_request=intervention,
            )

        # 4. Missing Required User Preference (e.g., relocation, salary, work mode)
        if context.requires_preference:
            pref_val = context.known_preferences.get(context.requires_preference)
            if pref_val is None:
                target_loc = context.payload.get("location", "the target location")
                org_name = context.payload.get("organization", "this organization")

                question_text = (
                    f"I found a strong backend role at {org_name}, but it requires relocating to {target_loc}. "
                    f"Are you open to relocating?"
                ) if context.requires_preference == "relocation" else (
                    f"Please confirm your preference for {context.requires_preference} to continue evaluation."
                )

                intervention = HumanInterventionRequest(
                    task_id=context.task_id,
                    reason=f"User preference '{context.requires_preference}' is unknown.",
                    question=question_text,
                    context=context.payload,
                    urgency=InterventionUrgency.MEDIUM,
                    options=["Yes, willing to relocate", "No, keep local/remote only"],
                    required_response_type=InterventionResponseType.CHOICE,
                )
                return DecisionResult(
                    outcome=DecisionOutcome.CALL_HUMAN if context.urgency in ["MEDIUM", "HIGH"] else DecisionOutcome.ASK_HUMAN,
                    reason=f"Required preference '{context.requires_preference}' missing from user profile.",
                    confidence=0.95,
                    intervention_request=intervention,
                )

        # 5. Low Confidence / Ambiguity Gate
        if context.confidence < 0.60:
            intervention = HumanInterventionRequest(
                task_id=context.task_id,
                reason=f"Low model confidence ({round(context.confidence, 2)}) on step '{context.step_name}'.",
                question=f"I encountered ambiguity regarding {context.proposed_action}. How would you like to proceed?",
                context=context.payload,
                urgency=InterventionUrgency.MEDIUM,
                required_response_type=InterventionResponseType.FREE_TEXT,
            )
            return DecisionResult(
                outcome=DecisionOutcome.ASK_HUMAN,
                reason="Confidence below autonomous threshold.",
                confidence=context.confidence,
                intervention_request=intervention,
            )

        # 6. Default: Safe Autonomous Continuation
        return DecisionResult(
            outcome=DecisionOutcome.CONTINUE,
            reason="Action is safe to execute autonomously.",
            confidence=1.0,
        )
