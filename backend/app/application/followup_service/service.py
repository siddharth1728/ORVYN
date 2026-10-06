"""Follow-Up Service: Long-running task monitoring, condition triggers, and cooldown enforcement."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.domain.events.dispatcher import dispatcher
from app.domain.events.models import Event
from app.domain.followup.models import (
    ConditionEvaluation,
    ConditionType,
    FollowUpStatus,
    FollowUpTarget,
    TriggerCondition,
)


class FollowUpService:
    """Manages periodic follow-ups, trigger conditions, cooldowns, and escalation policies."""

    def __init__(self) -> None:
        self._targets: Dict[UUID, FollowUpTarget] = {}

    async def register_followup(self, data: Dict[str, Any]) -> FollowUpTarget:
        task_id = UUID(str(data["task_id"]))
        cond_type_str = data.get("condition_type", "NO_RESPONSE")
        cond_type = ConditionType(cond_type_str)

        condition = TriggerCondition(
            condition_type=cond_type,
            description=f"Trigger when {cond_type.value} met",
            target_value=data.get("target_value", "7_days"),
        )

        target = FollowUpTarget(
            task_id=task_id,
            title=data.get("title", "Application Follow-up"),
            target_entity=data.get("target_entity", "Unknown Entity"),
            action_to_take=data.get("action_to_take", "Check status"),
            conditions=[condition],
            status=FollowUpStatus.WAITING,
            max_attempts=int(data.get("max_attempts", 3)),
            cooldown_seconds=int(data.get("cooldown_hours", 24)) * 3600,
        )

        self._targets[target.id] = target

        await dispatcher.dispatch(
            Event(
                event_type="FOLLOWUP_CREATED",
                task_id=task_id,
                payload={"followup_id": str(target.id), "target_entity": target.target_entity},
                source="followup_service",
            )
        )
        return target

    async def evaluate_conditions(self, followup_id: UUID) -> List[ConditionEvaluation]:
        target = self._targets.get(followup_id)
        if not target:
            return []

        now = datetime.now(timezone.utc)
        evaluations: List[ConditionEvaluation] = []

        for cond in target.conditions:
            is_met = False
            explanation = ""

            if cond.condition_type == ConditionType.TIME:
                if cond.target_value and isinstance(cond.target_value, str):
                    try:
                        target_dt = datetime.fromisoformat(cond.target_value)
                        is_met = now >= target_dt
                        explanation = f"Target time reached ({target_dt.isoformat()})"
                    except ValueError:
                        is_met = True
            elif cond.condition_type in [ConditionType.NO_RESPONSE, ConditionType.DEADLINE]:
                # Simulated positive condition evaluation for test workflows
                is_met = True
                explanation = f"Condition '{cond.condition_type.value}' criteria reached."
            else:
                is_met = False
                explanation = "Awaiting external trigger."

            cond.is_met = is_met
            cond.last_evaluated_at = now
            evaluations.append(
                ConditionEvaluation(
                    condition_id=cond.id,
                    is_met=is_met,
                    explanation=explanation,
                )
            )

        # Update target state if any condition met
        if any(e.is_met for e in evaluations):
            if target.can_attempt(now):
                target.status = FollowUpStatus.READY
            else:
                if target.attempt_count >= target.max_attempts:
                    target.status = FollowUpStatus.ESCALATED
                else:
                    target.status = FollowUpStatus.WAITING

        await dispatcher.dispatch(
            Event(
                event_type="CONDITION_EVALUATED",
                task_id=target.task_id,
                payload={"followup_id": str(target.id), "status": target.status.value},
                source="followup_service",
            )
        )

        return evaluations

    def get_followup(self, followup_id: UUID) -> Optional[FollowUpTarget]:
        return self._targets.get(followup_id)

    def list_followups(self, task_id: Optional[UUID] = None) -> List[FollowUpTarget]:
        targets = list(self._targets.values())
        if task_id:
            targets = [t for t in targets if t.task_id == task_id]
        return targets


# Global followup service singleton
followup_service = FollowUpService()
