"""Context Builder assembling bounded context for autonomous execution."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.application.memory_service.service import memory_service
from app.domain.events.dispatcher import dispatcher
from app.domain.planning.models import PlanStep
from app.domain.policies.models import AgentPolicy, default_policy
from app.domain.tasks.models import Task


class AssembledAgentContext:
    def __init__(
        self,
        task: Task,
        current_step: Optional[PlanStep],
        user_profile: Dict[str, Any],
        relevant_memories: List[Dict[str, Any]],
        recent_events: List[Dict[str, Any]],
        policy: AgentPolicy,
    ) -> None:
        self.task = task
        self.current_step = current_step
        self.user_profile = user_profile
        self.relevant_memories = relevant_memories
        self.recent_events = recent_events
        self.policy = policy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": str(self.task.id),
            "objective": self.task.objective,
            "status": self.task.status.value,
            "current_step": self.current_step.model_dump() if self.current_step else None,
            "user_profile": self.user_profile,
            "relevant_memories": self.relevant_memories,
            "recent_events": self.recent_events,
        }


class ContextBuilder:
    """Assembles a bounded context window without overflowing the model context."""

    @classmethod
    async def build_context(
        cls,
        task: Task,
        current_step: Optional[PlanStep] = None,
        policy: Optional[AgentPolicy] = None,
        max_memories: int = 5,
        max_events: int = 5,
    ) -> AssembledAgentContext:
        # 1. Fetch user profile
        user_profile = await memory_service.get_user_profile()

        # 2. Query contextual memories for the current objective
        memories = await memory_service.search_memories(
            query=f"{task.objective} {current_step.name if current_step else ''}",
            limit=max_memories,
        )
        memory_items = [
            {
                "content": m.memory.content,
                "relevance": m.relevance_score,
                "confidence": m.confidence,
                "source": m.provenance.source_reference,
            }
            for m in memories
        ]

        # 3. Retrieve recent task events
        all_events = dispatcher.get_events_for_task(task.id)
        recent_events = [
            {"type": e.event_type, "timestamp": e.timestamp.isoformat(), "source": e.source}
            for e in all_events[-max_events:]
        ]

        return AssembledAgentContext(
            task=task,
            current_step=current_step,
            user_profile=user_profile,
            relevant_memories=memory_items,
            recent_events=recent_events,
            policy=policy or default_policy,
        )
