"""Task ORM model."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orvyn.database.base import Base
from orvyn.domain.task import TaskState


class TaskORM(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    current_state: Mapped[TaskState] = mapped_column(
        Enum(TaskState), nullable=False, default=TaskState.CREATED, index=True
    )
    current_step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    state_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships with selectin loading for seamless async usage
    checkpoints = relationship(
        "TaskCheckpointORM", back_populates="task", cascade="all, delete-orphan", lazy="selectin"
    )
    interventions = relationship(
        "HumanInterventionORM", back_populates="task", cascade="all, delete-orphan", lazy="selectin"
    )
    calls = relationship(
        "VoiceCallORM", back_populates="task", cascade="all, delete-orphan", lazy="selectin"
    )
    events = relationship(
        "EventORM", back_populates="task", cascade="all, delete-orphan", lazy="selectin"
    )
