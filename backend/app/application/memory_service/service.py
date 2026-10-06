"""Persistent Memory Service and Retrieval Subsystem with strict provenance."""

import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.core.exceptions import OrvynError
from app.domain.events.dispatcher import dispatcher
from app.domain.events.models import Event
from app.domain.memory.models import (
    EpisodicMemoryRecord,
    Memory,
    MemoryProvenance,
    MemorySearchResult,
    MemorySourceType,
    MemoryType,
    UserProfilePreference,
)


class InvalidMemoryProvenanceError(OrvynError):
    pass


class MemoryService:
    """Manages User Profile, Episodic, and Semantic memories with provenance enforcement."""

    def __init__(self) -> None:
        # In-memory stores (in production backed by PostgreSQL + pgvector)
        self._memories: Dict[UUID, Memory] = {}
        self._profiles: Dict[UUID, Dict[str, UserProfilePreference]] = {}
        self._episodic_records: List[EpisodicMemoryRecord] = []

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType | str,
        source_type: MemorySourceType | str,
        source_reference: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        related_entity_id: Optional[UUID] = None,
        related_entity_type: Optional[str] = None,
    ) -> Memory:
        """Stores a durable memory item with verified provenance."""
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)
        if isinstance(source_type, str):
            source_type = MemorySourceType(source_type)

        # Provenance Invariant: AGENT_INFERENCE cannot be claimed with 1.0 confidence or as explicit USER fact
        if source_type == MemorySourceType.AGENT_INFERENCE and confidence > 0.85:
            confidence = 0.85

        provenance = MemoryProvenance(
            source_type=source_type,
            source_reference=source_reference,
            confidence=confidence,
            verified_by_user=(source_type in [MemorySourceType.USER, MemorySourceType.VOICE_CALL]),
        )

        memory = Memory(
            type=memory_type,
            content=content,
            provenance=provenance,
            related_entity_id=related_entity_id,
            related_entity_type=related_entity_type,
            metadata=metadata or {},
        )

        self._memories[memory.id] = memory

        # Dispatch memory stored event
        await dispatcher.dispatch(
            Event(
                event_type="MEMORY_STORED",
                payload={
                    "memory_id": str(memory.id),
                    "type": memory.type.value,
                    "source_type": provenance.source_type.value,
                    "confidence": provenance.confidence,
                },
                source="memory_service",
            )
        )
        return memory

    async def set_profile_preference(
        self,
        user_id: UUID,
        category: str,
        key: str,
        value: Any,
        source_type: MemorySourceType = MemorySourceType.USER,
        source_reference: str = "direct_input",
        confidence: float = 1.0,
    ) -> UserProfilePreference:
        """Sets a durable, explicit user profile attribute."""
        provenance = MemoryProvenance(
            source_type=source_type,
            source_reference=source_reference,
            confidence=confidence,
            verified_by_user=(source_type in [MemorySourceType.USER, MemorySourceType.VOICE_CALL]),
        )

        pref = UserProfilePreference(
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            provenance=provenance,
        )

        if user_id not in self._profiles:
            self._profiles[user_id] = {}
        self._profiles[user_id][key] = pref

        # Mirror as a PROFILE memory
        await self.store_memory(
            content=f"User preference [{category}.{key}]: {value}",
            memory_type=MemoryType.PROFILE,
            source_type=source_type,
            source_reference=source_reference,
            confidence=confidence,
            metadata={"user_id": str(user_id), "key": key, "value": value},
            related_entity_id=user_id,
            related_entity_type="USER",
        )
        return pref

    async def get_user_profile(self, user_id: Optional[UUID | str] = None) -> Dict[str, Any]:
        """Returns consolidated user profile dictionary."""
        if not user_id:
            # Return first or default profile if single-user mode
            if self._profiles:
                first_uid = next(iter(self._profiles))
                return {k: p.value for k, p in self._profiles[first_uid].items()}
            return {}

        uid = UUID(str(user_id))
        prefs = self._profiles.get(uid, {})
        return {k: p.value for k, p in prefs.items()}

    async def record_episodic_event(
        self,
        event_type: str,
        summary: str,
        outcome: str,
        task_id: Optional[UUID] = None,
        source_type: MemorySourceType = MemorySourceType.SYSTEM,
        source_reference: str = "agent_loop",
        context: Optional[Dict[str, Any]] = None,
    ) -> EpisodicMemoryRecord:
        """Records notable historical event queryable by task and time."""
        provenance = MemoryProvenance(
            source_type=source_type,
            source_reference=source_reference,
            confidence=1.0,
        )
        record = EpisodicMemoryRecord(
            task_id=task_id,
            event_type=event_type,
            summary=summary,
            outcome=outcome,
            provenance=provenance,
            context=context or {},
        )
        self._episodic_records.append(record)

        # Mirror as EPISODIC memory item
        await self.store_memory(
            content=f"{event_type}: {summary} -> Outcome: {outcome}",
            memory_type=MemoryType.EPISODIC,
            source_type=source_type,
            source_reference=source_reference,
            confidence=1.0,
            metadata=context or {},
            related_entity_id=task_id,
            related_entity_type="TASK",
        )
        return record

    async def search_memories(
        self,
        query: str,
        memory_type: Optional[MemoryType | str] = None,
        limit: int = 5,
    ) -> List[MemorySearchResult]:
        """Performs lexical and semantic similarity matching on memories."""
        query_words = set(re.findall(r"\w+", query.lower()))
        results: List[MemorySearchResult] = []

        target_type = MemoryType(memory_type) if isinstance(memory_type, str) else memory_type

        for mem in self._memories.values():
            if target_type and mem.type != target_type:
                continue

            content_words = set(re.findall(r"\w+", mem.content.lower()))
            overlap = query_words.intersection(content_words)
            if overlap:
                # Basic TF-IDF / Jaccard score approximation
                relevance = len(overlap) / max(len(query_words), 1)
            else:
                relevance = 0.05 if not query.strip() else 0.0

            if relevance > 0.0:
                results.append(
                    MemorySearchResult(
                        memory=mem,
                        relevance_score=round(relevance, 3),
                        provenance=mem.provenance,
                        confidence=mem.provenance.confidence,
                    )
                )

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:limit]

    async def query_contextual_memories(
        self,
        user_id: Optional[UUID],
        context_query: str,
        limit: int = 5,
    ) -> List[MemorySearchResult]:
        """High-level retrieval answering agent contextual queries with provenance."""
        # 1. Search semantic & episodic memories
        memories = await self.search_memories(query=context_query, limit=limit)
        await dispatcher.dispatch(
            Event(
                event_type="MEMORY_RETRIEVED",
                payload={"query": context_query, "matched_count": len(memories)},
                source="memory_service",
            )
        )
        return memories


# Global singleton instance
memory_service = MemoryService()
