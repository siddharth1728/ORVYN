"""Event Dispatcher abstraction and in-process implementation."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict, List

from app.core.logging import logger
from app.domain.events.models import Event

EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventDispatcher(ABC):
    """Abstract Event Dispatcher interface."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        pass

    @abstractmethod
    def subscribe_all(self, handler: EventHandler) -> None:
        """Register a handler for all events."""
        pass

    @abstractmethod
    async def dispatch(self, event: Event) -> None:
        """Dispatch an event asynchronously to all registered listeners."""
        pass


class InMemoryEventDispatcher(EventDispatcher):
    """In-process async event dispatcher (swappable with Redis/Kafka)."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[Event] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        self._global_handlers.append(handler)

    async def dispatch(self, event: Event) -> None:
        self._event_history.append(event)
        logger.info(
            f"Event Dispatched: {event.event_type} on Task {event.task_id}",
            extra={"task_id": event.task_id, "event_type": event.event_type, "extra_data": event.payload}
        )

        handlers = list(self._global_handlers)
        if event.event_type in self._handlers:
            handlers.extend(self._handlers[event.event_type])

        for handler in handlers:
            try:
                await handler(event)
            except Exception as exc:
                logger.error(f"Error handling event {event.event_type}: {exc}", exc_info=True)

    def get_events_for_task(self, task_id) -> List[Event]:
        """Returns all recorded events for a task."""
        return [e for e in self._event_history if e.task_id == task_id]


# Global singleton instance
dispatcher = InMemoryEventDispatcher()
