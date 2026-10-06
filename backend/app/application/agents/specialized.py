"""Specialized agents operating under the common ORVYN runtime."""

from typing import Any, Dict, Optional
from uuid import UUID

from app.application.followup_service.service import followup_service
from app.application.memory_service.service import memory_service
from app.application.opportunity_service.service import opportunity_service
from app.application.research_service.service import research_service
from app.domain.artifacts.models import Artifact, ArtifactType
from app.domain.events.dispatcher import dispatcher
from app.domain.events.models import Event
from app.domain.handoffs.models import AgentHandoff
from app.domain.opportunities.models import OpportunityType


class OpportunityAgent:
    """Specialized in opportunity discovery, deduplication, and profile scoring."""

    def __init__(self) -> None:
        self.name = "OpportunityAgent"

    async def execute_discovery(
        self,
        task_id: UUID,
        objective: str,
        user_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        await dispatcher.dispatch(
            Event(
                event_type="AGENT_ACTION_STARTED",
                task_id=task_id,
                payload={"agent": self.name, "action": "discover_and_score"},
                source=self.name,
            )
        )

        # 1. Ingest candidate opportunities (e.g., from search/feed)
        opp1 = await opportunity_service.ingest_opportunity(
            title="Backend Engineering Intern",
            organization="Razorpay",
            opportunity_type=OpportunityType.INTERNSHIP,
            location="Bangalore",
            requires_relocation=True,
            required_skills=["Python", "FastAPI", "SQL"],
            application_url="https://razorpay.com/careers/backend-intern",
            source_url="https://linkedin.com/jobs/view/1001",
        )

        # 2. Ingest duplicate candidate from another source to demonstrate multi-signal deduplication
        opp1_dup = await opportunity_service.ingest_opportunity(
            title="Backend Engineering Intern",
            organization="Razorpay",
            opportunity_type=OpportunityType.INTERNSHIP,
            location="Bangalore",
            requires_relocation=True,
            required_skills=["Python", "FastAPI"],
            application_url="https://razorpay.com/careers/backend-intern",
            source_url="https://naukri.com/job/1002",
        )
        assert opp1.id == opp1_dup.id  # Deduplicated to canonical record

        # 3. Score against user profile
        score = opportunity_service.score_opportunity(opp1, user_profile)

        return {
            "canonical_opportunity_id": str(opp1.id),
            "title": opp1.title,
            "organization": opp1.organization,
            "score": score.score,
            "match_level": score.match_level,
            "requires_relocation": opp1.requires_relocation,
            "missing_user_info": score.missing_user_info,
            "deduplicated_sources_count": len(opp1.source_urls),
        }


class ResearchAgent:
    """Specialized in source verification, conflict detection, and factual report generation."""

    def __init__(self) -> None:
        self.name = "ResearchAgent"

    async def execute_research(self, task_id: UUID, organization: str) -> Dict[str, Any]:
        await dispatcher.dispatch(
            Event(
                event_type="AGENT_ACTION_STARTED",
                task_id=task_id,
                payload={"agent": self.name, "action": "conduct_research", "target": organization},
                source=self.name,
            )
        )

        report = await research_service.conduct_research(topic=organization, task_id=task_id)

        artifact = Artifact(
            task_id=task_id,
            artifact_type=ArtifactType.RESEARCH_REPORT,
            title=f"Research Report: {organization}",
            content={
                "report_id": str(report.id),
                "summary": report.summary,
                "findings_count": len(report.findings),
                "sources": [s.url for s in report.sources],
            },
            created_by_agent=self.name,
        )

        return {
            "report_id": str(report.id),
            "artifact_id": str(artifact.id),
            "findings_count": len(report.findings),
            "summary": report.summary,
        }


class FollowUpAgent:
    """Specialized in condition evaluation, scheduling, and anti-spam follow-ups."""

    def __init__(self) -> None:
        self.name = "FollowUpAgent"

    async def setup_tracking(
        self,
        task_id: UUID,
        title: str,
        target_entity: str,
    ) -> Dict[str, Any]:
        target = await followup_service.register_followup({
            "task_id": str(task_id),
            "title": title,
            "target_entity": target_entity,
            "action_to_take": "Send polite status check",
            "condition_type": "NO_RESPONSE",
            "cooldown_hours": 24,
        })

        return {
            "followup_id": str(target.id),
            "target_entity": target.target_entity,
            "status": target.status.value,
            "cooldown_seconds": target.cooldown_seconds,
        }


class AgentCoordinator:
    """Coordinates specialized agent execution and tracks observable handoffs."""

    @classmethod
    async def record_handoff(
        cls,
        task_id: UUID,
        from_agent: str,
        to_agent: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentHandoff:
        handoff = AgentHandoff(
            task_id=task_id,
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            context=context or {},
        )

        await dispatcher.dispatch(
            Event(
                event_type="AGENT_HANDOFF",
                task_id=task_id,
                payload={
                    "from_agent": from_agent,
                    "to_agent": to_agent,
                    "reason": reason,
                },
                source="coordinator",
            )
        )
        return handoff
