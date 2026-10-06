"""Decision Engine: Evaluates action safety, uncertainty, and human-dependence."""

from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from orvyn.core.logging import logger
from orvyn.domain.decision import InterventionReason, InterventionRequest, UrgencyLevel
from orvyn.domain.task import Task


class ActionDisposition(str, Enum):
    AUTONOMOUS_CONTINUE = "AUTONOMOUS_CONTINUE"
    HUMAN_INTERVENTION_REQUIRED = "HUMAN_INTERVENTION_REQUIRED"
    FAIL_SAFELY = "FAIL_SAFELY"


class DecisionEvaluationResult:
    """Result of an evaluation by the Decision Engine."""

    def __init__(
        self,
        disposition: ActionDisposition,
        intervention_request: Optional[InterventionRequest] = None,
        reason: str = "",
        confidence: float = 1.0,
    ) -> None:
        self.disposition = disposition
        self.intervention_request = intervention_request
        self.reason = reason
        self.confidence = confidence


class DecisionEngine:
    """Centralized gatekeeper determining whether to proceed autonomously or interrupt the human."""

    @classmethod
    def evaluate_opportunity(
        cls,
        task: Task,
        checkpoint_id: UUID,
        opportunity_data: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> DecisionEvaluationResult:
        """Evaluates whether an opportunity requires human clarification or can proceed autonomously.

        Key human-intervention cases:
        1. Role requires relocation, and user's relocation preference for that city is NULL/Unknown.
        2. Role requires explicit security clearance or irreversible application submission.
        """
        title = opportunity_data.get("title", "Opportunity")
        organization = opportunity_data.get("organization", "Company")
        requires_relocation = opportunity_data.get("requires_relocation", False)
        target_location = opportunity_data.get("location", "Unknown Location")

        logger.info(
            f"DecisionEngine evaluating: {title} at {organization}. Relocation required: {requires_relocation}",
            extra={"task_id": task.id, "metadata": {"org": organization, "location": target_location}}
        )

        # Check Relocation Requirement
        if requires_relocation:
            relocation_pref = user_profile.get("willing_to_relocate")
            allowed_locations = user_profile.get("preferred_locations", [])

            # If preference is explicitly false
            if relocation_pref is False:
                return DecisionEvaluationResult(
                    disposition=ActionDisposition.AUTONOMOUS_CONTINUE,
                    reason=f"Candidate profile explicitly excludes relocation. Filtering out {organization} autonomously.",
                    confidence=1.0,
                )

            # If location is in already approved locations list
            if target_location in allowed_locations:
                return DecisionEvaluationResult(
                    disposition=ActionDisposition.AUTONOMOUS_CONTINUE,
                    reason=f"Target location '{target_location}' already approved in user profile.",
                    confidence=1.0,
                )

            # Preference is unknown or ambiguous -> MUST ASK HUMAN
            intervention = InterventionRequest(
                task_id=task.id,
                checkpoint_id=checkpoint_id,
                reason=InterventionReason.AMBIGUOUS_PREFERENCE,
                question=f"I found a backend opportunity at {organization}, but it requires relocating to {target_location}. Are you willing to relocate?",
                urgency=UrgencyLevel.MEDIUM,
                context={
                    "opportunity": opportunity_data,
                    "target_location": target_location,
                    "organization": organization,
                    "missing_field": "willing_to_relocate",
                },
                options=["Yes, willing to relocate", "No, keep local/remote only"],
            )

            return DecisionEvaluationResult(
                disposition=ActionDisposition.HUMAN_INTERVENTION_REQUIRED,
                intervention_request=intervention,
                reason=f"Relocation preference unknown for {target_location}.",
                confidence=0.95,
            )

        # Irreversible Action check (e.g. Submitting application)
        if opportunity_data.get("action_type") == "SUBMIT_APPLICATION":
            intervention = InterventionRequest(
                task_id=task.id,
                checkpoint_id=checkpoint_id,
                reason=InterventionReason.IRREVERSIBLE_ACTION,
                question=f"Ready to submit your application to {organization} for '{title}'. Do you authorize submission?",
                urgency=UrgencyLevel.HIGH,
                context={"opportunity": opportunity_data},
            )
            return DecisionEvaluationResult(
                disposition=ActionDisposition.HUMAN_INTERVENTION_REQUIRED,
                intervention_request=intervention,
                reason="Submitting application is an external irreversible action.",
                confidence=1.0,
            )

        # By default, safe read-only operations continue autonomously
        return DecisionEvaluationResult(
            disposition=ActionDisposition.AUTONOMOUS_CONTINUE,
            reason="Action is safe and read-only.",
            confidence=1.0,
        )
