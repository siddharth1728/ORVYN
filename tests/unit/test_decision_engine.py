"""Unit tests for the Decision Engine."""

from uuid import uuid4

from orvyn.domain.decision import InterventionReason, UrgencyLevel
from orvyn.domain.task import Task
from orvyn.engine.decision_engine import ActionDisposition, DecisionEngine


def test_relocation_required_triggers_human_intervention():
    """Verify that an opportunity requiring relocation with unknown user preference triggers HUMAN_INTERVENTION_REQUIRED."""
    task = Task(user_id=uuid4(), title="Search Jobs", objective="Find jobs")
    checkpoint_id = uuid4()

    opportunity = {
        "title": "Backend Engineering Intern",
        "organization": "Razorpay",
        "requires_relocation": True,
        "location": "Bangalore",
    }

    # User profile has no relocation preference
    user_profile = {"willing_to_relocate": None, "preferred_locations": []}

    result = DecisionEngine.evaluate_opportunity(
        task=task,
        checkpoint_id=checkpoint_id,
        opportunity_data=opportunity,
        user_profile=user_profile,
    )

    assert result.disposition == ActionDisposition.HUMAN_INTERVENTION_REQUIRED
    assert result.intervention_request is not None
    assert result.intervention_request.task_id == task.id
    assert result.intervention_request.checkpoint_id == checkpoint_id
    assert result.intervention_request.reason == InterventionReason.AMBIGUOUS_PREFERENCE
    assert "relocating to Bangalore" in result.intervention_request.question
    assert result.intervention_request.urgency == UrgencyLevel.MEDIUM


def test_known_preferred_location_proceeds_autonomously():
    """Verify that if the location is already approved in user profile, execution proceeds autonomously."""
    task = Task(user_id=uuid4(), title="Search Jobs", objective="Find jobs")
    checkpoint_id = uuid4()

    opportunity = {
        "title": "Backend Engineering Intern",
        "organization": "Razorpay",
        "requires_relocation": True,
        "location": "Bangalore",
    }

    # User profile already has Bangalore in approved locations
    user_profile = {"willing_to_relocate": True, "preferred_locations": ["Bangalore", "Hyderabad"]}

    result = DecisionEngine.evaluate_opportunity(
        task=task,
        checkpoint_id=checkpoint_id,
        opportunity_data=opportunity,
        user_profile=user_profile,
    )

    assert result.disposition == ActionDisposition.AUTONOMOUS_CONTINUE
    assert result.intervention_request is None
    assert "already approved" in result.reason


def test_irreversible_action_requires_explicit_authorization():
    """Verify that submitting an application triggers an authorization intervention."""
    task = Task(user_id=uuid4(), title="Submit Job", objective="Apply for job")
    checkpoint_id = uuid4()

    opportunity = {
        "title": "Software Engineer 1",
        "organization": "Google",
        "action_type": "SUBMIT_APPLICATION",
    }

    result = DecisionEngine.evaluate_opportunity(
        task=task,
        checkpoint_id=checkpoint_id,
        opportunity_data=opportunity,
        user_profile={},
    )

    assert result.disposition == ActionDisposition.HUMAN_INTERVENTION_REQUIRED
    assert result.intervention_request.reason == InterventionReason.IRREVERSIBLE_ACTION
    assert result.intervention_request.urgency == UrgencyLevel.HIGH
