"""Health check route."""

from typing import Any, Dict
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
        "llm_provider": settings.llm_provider,
        "voice_provider": settings.voice_provider,
        "search_provider": settings.search_provider,
    }
