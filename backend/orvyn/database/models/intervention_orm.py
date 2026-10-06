"""Human Intervention ORM model."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orvyn.database.base import Base
from orvyn.domain.decision import InterventionReason, UrgencyLevel


class HumanInterventionORM(Base):
    __tablename__ = "human_interventions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    checkpoint_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("task_checkpoints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[InterventionReason] = mapped_column(Enum(InterventionReason), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[UrgencyLevel] = mapped_column(Enum(UrgencyLevel), nullable=False, default=UrgencyLevel.MEDIUM)
    context: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    decision: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    task = relationship("TaskORM", back_populates="interventions")
    checkpoint = relationship("TaskCheckpointORM", back_populates="interventions")
    calls = relationship("VoiceCallORM", back_populates="intervention", cascade="all, delete-orphan")
