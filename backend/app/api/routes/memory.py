"""Memory API routes with strict provenance and semantic search."""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.application.memory_service.service import memory_service
from app.domain.memory.models import (
    Memory,
    MemoryProvenance,
    MemorySearchResult,
    MemorySourceType,
    MemoryType,
    UserProfilePreference,
)

router = APIRouter(prefix="/memory", tags=["Memory"])


class StoreMemoryRequest(BaseModel):
    content: str
    memory_type: MemoryType = MemoryType.SEMANTIC
    source_type: MemorySourceType = MemorySourceType.USER
    source_reference: str = "web_ui"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    related_entity_id: Optional[UUID] = None
    related_entity_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProfilePreferenceRequest(BaseModel):
    category: str
    key: str
    value: Any
    source_reference: str = "web_ui"
    confidence: float = 1.0


@router.get("", response_model=List[Memory])
async def list_memories(
    memory_type: Optional[MemoryType] = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> List[Memory]:
    memories = await memory_service.list_memories(memory_type=memory_type)
    return memories[:limit]


@router.post("", response_model=Memory, status_code=status.HTTP_201_CREATED)
async def store_memory(payload: StoreMemoryRequest) -> Memory:
    provenance = MemoryProvenance(
        source_type=payload.source_type,
        source_reference=payload.source_reference,
        confidence=payload.confidence,
    )
    return await memory_service.store_memory(
        content=payload.content,
        memory_type=payload.memory_type,
        provenance=provenance,
        related_entity_id=payload.related_entity_id,
        related_entity_type=payload.related_entity_type,
        metadata=payload.metadata,
    )


@router.get("/search", response_model=List[MemorySearchResult])
async def search_memories(
    q: str = Query(..., min_length=1),
    memory_type: Optional[MemoryType] = None,
    limit: int = Query(default=10, ge=1, le=50),
) -> List[MemorySearchResult]:
    return await memory_service.search_memories(
        query=q,
        memory_type=memory_type,
        limit=limit,
    )


@router.get("/profile/{user_id}", response_model=List[UserProfilePreference])
async def get_user_profile(user_id: UUID) -> List[UserProfilePreference]:
    return await memory_service.get_user_profile(user_id)


@router.post("/profile/{user_id}", response_model=UserProfilePreference)
async def update_user_profile(user_id: UUID, payload: ProfilePreferenceRequest) -> UserProfilePreference:
    return await memory_service.set_profile_preference(
        user_id=user_id,
        category=payload.category,
        key=payload.key,
        value=payload.value,
        source_reference=payload.source_reference,
    )
