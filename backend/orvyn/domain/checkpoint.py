"""Task Checkpointing domain models for zero-loss resumption."""

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any, Dict
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TaskCheckpoint(BaseModel):
    """Immutable snapshot of task state allowing execution to resume exactly where interrupted."""
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    step_index: int
    step_name: str
    state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    resumption_token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    state_hash: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __context: Any) -> None:
        """Compute state integrity hash if not provided."""
        if not self.state_hash:
            serialized = json.dumps(self.state_snapshot, sort_keys=True, default=str)
            self.state_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
