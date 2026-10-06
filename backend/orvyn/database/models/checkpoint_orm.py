"""Task Checkpoint ORM model."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orvyn.database.base import Base


class TaskCheckpointORM(Base):
    __tablename__ = "task_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(100), nullable=False)
    state_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    resumption_token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    task = relationship("TaskORM", back_populates="checkpoints")
    interventions = relationship("HumanInterventionORM", back_populates="checkpoint", cascade="all, delete-orphan")
