"""User domain entity and profile."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
