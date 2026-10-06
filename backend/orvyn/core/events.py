"""Domain Event primitives and asynchronous Event Bus."""

from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from orvyn.core.logging import logger


class DomainEvent(BaseModel):
    """Immutable record of an event that occurred in the domain."""
    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID
    causation_id: Optional[UUID] = None
    aggregate_type: str  # "TASK", "CALL", "CHECKPOINT", "MEMORY", etc.
    aggregate_id: UUID
    event_type: str      # e.g., "TASK_CREATED", "HUMAN_DECISION_REQUIRED"
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventBus:
    """In-process asynchronous event bus with pub/sub subscriber registry."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribes an async handler to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribes an async handler to receive all emitted domain events."""
        self._global_subscribers.append(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publishes an event to all interested handlers."""
        logger.info(
            f"Event Emitted: {event.event_type} on {event.aggregate_type}:{event.aggregate_id}",
            extra={"task_id": event.aggregate_id, "event_type": event.event_type, "metadata": event.payload}
        )

        handlers = list(self._global_subscribers)
        if event.event_type in self._subscribers:
            handlers.extend(self._subscribers[event.event_type])

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"Error in event handler for {event.event_type}: {e}",
                    exc_info=True,
                    extra={"task_id": event.aggregate_id, "event_type": event.event_type}
                )


# Global singleton event bus instance
event_bus = EventBus()
