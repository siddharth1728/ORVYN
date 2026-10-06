"""Audit timeline and real-time event streaming routes."""

import json
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orvyn.core.events import DomainEvent, event_bus
from orvyn.database.models.event_orm import EventORM
from orvyn.database.session import get_db_session

router = APIRouter(prefix="/timeline", tags=["Timeline"])


@router.get("/{task_id}")
async def get_task_timeline(
    task_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> List[dict]:
    """Retrieves all domain events for a given task, ordered chronologically."""
    stmt = select(EventORM).where(EventORM.task_id == task_id).order_by(EventORM.created_at.asc())
    result = await session.execute(stmt)
    events = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "task_id": str(e.task_id) if e.task_id else None,
            "correlation_id": str(e.correlation_id),
            "event_type": e.event_type,
            "payload": e.payload,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.websocket("/stream/{task_id}")
async def stream_task_events(websocket: WebSocket, task_id: UUID):
    """Streams live domain events for a specific task over WebSocket."""
    await websocket.accept()

    async def handle_event(event: DomainEvent):
        if event.aggregate_id == task_id or (event.payload and event.payload.get("task_id") == str(task_id)):
            await websocket.send_text(
                json.dumps({
                    "event_type": event.event_type,
                    "aggregate_id": str(event.aggregate_id),
                    "payload": event.payload,
                    "timestamp": event.timestamp.isoformat(),
                })
            )

    event_bus.subscribe_all(handle_event)

    try:
        while True:
            # Keep socket alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
