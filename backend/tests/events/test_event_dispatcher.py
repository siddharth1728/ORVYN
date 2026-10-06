"""Event creation, dispatch, and listener subscription tests."""

import pytest
from uuid import uuid4

from app.domain.events.dispatcher import InMemoryEventDispatcher
from app.domain.events.models import Event


@pytest.mark.asyncio
async def test_event_dispatch_and_subscription():
    dispatcher = InMemoryEventDispatcher()
    received_events = []

    async def on_task_created(event: Event):
        received_events.append(event)

    dispatcher.subscribe("TASK_CREATED", on_task_created)

    task_id = uuid4()
    test_event = Event(
        event_type="TASK_CREATED",
        task_id=task_id,
        payload={"title": "Test Event Title"},
    )

    await dispatcher.dispatch(test_event)

    assert len(received_events) == 1
    assert received_events[0].event_type == "TASK_CREATED"
    assert received_events[0].task_id == task_id


@pytest.mark.asyncio
async def test_global_event_subscription():
    dispatcher = InMemoryEventDispatcher()
    all_events = []

    async def on_any_event(event: Event):
        all_events.append(event)

    dispatcher.subscribe_all(on_any_event)

    task_id = uuid4()
    await dispatcher.dispatch(Event(event_type="STEP_ONE", task_id=task_id))
    await dispatcher.dispatch(Event(event_type="STEP_TWO", task_id=task_id))

    assert len(all_events) == 2
    task_events = dispatcher.get_events_for_task(task_id)
    assert len(task_events) == 2
