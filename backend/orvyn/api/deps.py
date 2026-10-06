"""API Dependencies and context injection."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from orvyn.database.session import get_db_session
from orvyn.engine.checkpoint_manager import CheckpointManager, checkpoint_manager
from orvyn.core.events import EventBus, event_bus


def get_checkpoint_manager() -> CheckpointManager:
    """Returns the system checkpoint manager instance."""
    return checkpoint_manager


def get_event_bus() -> EventBus:
    """Returns the system event bus instance."""
    return event_bus
