"""Opportunity Intelligence Service: Extraction, Deduplication, and Explainable Scoring."""

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.domain.events.dispatcher import dispatcher
from app.domain.events.models import Event
from app.domain.opportunities.models import (
    Opportunity,
    OpportunityScore,
    OpportunityStatus,
    OpportunityType,
)


class OpportunityService:
    """Manages opportunity discovery, multi-signal deduplication, and explainable scoring."""

    def __init__(self) -> None:
        self._opportunities: Dict[UUID, Opportunity] = {}
        self._canonical_index: Dict[str, UUID] = {}

    def _generate_canonical_hash(self, title: str, organization: str, location: Optional[str]) -> str:
        """Computes multi-signal normalization hash for deduplication."""
        norm_title = re.sub(r"[^a-z0-9]", "", title.lower())
        norm_org = re.sub(r"[^a-z0-9]", "", organization.lower())
        norm_loc = re.sub(r"[^a-z0-9]", "", (location or "remote").lower())
        raw_key = f"{norm_org}:{norm_title}:{norm_loc}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    async def ingest_opportunity(
        self,
        title: str,
        organization: str,
        opportunity_type: OpportunityType = OpportunityType.INTERNSHIP,
        location: Optional[str] = None,
        is_remote: bool = False,
        requires_relocation: bool = False,
        required_skills: Optional[List[str]] = None,
        preferred_skills: Optional[List[str]] = None,
        deadline: Optional[datetime] = None,
        application_url: Optional[str] = None,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Opportunity:
        """Normalizes and deduplicates discovered opportunities."""
        canon_hash = self._generate_canonical_hash(title, organization, location)

        # Deduplication check
        if canon_hash in self._canonical_index:
            existing_id = self._canonical_index[canon_hash]
            existing_opp = self._opportunities[existing_id]
            if source_url and source_url not in existing_opp.source_urls:
                existing_opp.source_urls.append(source_url)
            existing_opp.updated_at = datetime.now(timezone.utc)
            return existing_opp

        opp = Opportunity(
            title=title,
            organization=organization,
            opportunity_type=opportunity_type,
            location=location,
            is_remote=is_remote,
            requires_relocation=requires_relocation,
            required_skills=required_skills or [],
            preferred_skills=preferred_skills or [],
            deadline=deadline,
            application_url=application_url,
            source_urls=[source_url] if source_url else [],
            canonical_hash=canon_hash,
            metadata=metadata or {},
        )

        self._opportunities[opp.id] = opp
        self._canonical_index[canon_hash] = opp.id

        await dispatcher.dispatch(
            Event(
                event_type="OPPORTUNITY_DISCOVERED",
                payload={
                    "opportunity_id": str(opp.id),
                    "title": opp.title,
                    "organization": opp.organization,
                    "requires_relocation": opp.requires_relocation,
                },
                source="opportunity_service",
            )
        )

        return opp

    def score_opportunity(
        self,
        opportunity: Opportunity,
        user_profile: Dict[str, Any],
    ) -> OpportunityScore:
        """Calculates an explainable relevance score comparing opportunity against user profile."""
        score_val = 50.0
        positives: List[str] = []
        negatives: List[str] = []
        concerns: List[str] = []
        missing_info: List[str] = []

        # 1. Skill Match
        user_skills = [s.lower() for s in user_profile.get("skills", [])]
        matched_skills = [s for s in opportunity.required_skills if s.lower() in user_skills]
        if matched_skills:
            score_val += 25.0
            positives.append(f"Strong match on required skills: {', '.join(matched_skills)}")
        elif opportunity.required_skills:
            score_val -= 15.0
            concerns.append(f"Requires unconfirmed skills: {', '.join(opportunity.required_skills)}")

        # 2. Work Mode / Remote
        if opportunity.is_remote:
            score_val += 15.0
            positives.append("Remote flexibility matches modern engineering criteria")

        # 3. Relocation & Location Constraints
        if opportunity.requires_relocation:
            relocation_pref = user_profile.get("willing_to_relocate")
            preferred_cities = [c.lower() for c in user_profile.get("preferred_locations", [])]
            target_city = (opportunity.location or "").lower()

            if relocation_pref is False:
                score_val -= 40.0
                negatives.append(f"Requires relocation to {opportunity.location}, but user excludes relocation")
            elif target_city in preferred_cities:
                score_val += 15.0
                positives.append(f"Target location '{opportunity.location}' is in user preferred cities list")
            elif relocation_pref is True:
                score_val += 5.0
                positives.append(f"User is willing to relocate to {opportunity.location}")
            else:
                # Preference unknown
                missing_info.append(f"Relocation preference to {opportunity.location} is unknown")
                concerns.append(f"Requires physical presence in {opportunity.location}; user preference unrecorded")

        # Bound score between 0 and 100
        final_score = max(0.0, min(100.0, score_val))
        match_level = "HIGH" if final_score >= 75.0 else ("MEDIUM" if final_score >= 50.0 else "LOW")

        result = OpportunityScore(
            score=round(final_score, 1),
            match_level=match_level,
            positive_reasons=positives,
            negative_reasons=negatives,
            concerns_or_gaps=concerns,
            missing_user_info=missing_info,
        )

        opportunity.score = result
        return result

    def get_opportunity(self, opp_id: UUID) -> Optional[Opportunity]:
        return self._opportunities.get(opp_id)

    def list_opportunities(self, min_score: Optional[float] = None) -> List[Opportunity]:
        opps = list(self._opportunities.values())
        if min_score is not None:
            opps = [o for o in opps if o.score and o.score.score >= min_score]
        opps.sort(key=lambda o: (o.score.score if o.score else 0), reverse=True)
        return opps


# Global opportunity service singleton
opportunity_service = OpportunityService()
