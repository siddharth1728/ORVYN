"""FastAPI route dependencies."""

from app.application.task_service.service import TaskService, task_service
from app.domain.events.dispatcher import EventDispatcher, dispatcher


def get_task_service() -> TaskService:
    return task_service


def get_event_dispatcher() -> EventDispatcher:
    return dispatcher
