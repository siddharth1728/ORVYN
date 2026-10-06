"""Voice Call ORM model."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orvyn.database.base import Base
from orvyn.domain.call import CallStatus


class VoiceCallORM(Base):
    __tablename__ = "voice_calls"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intervention_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("human_interventions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_call_sid: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    to_phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[CallStatus] = mapped_column(
        Enum(CallStatus), nullable=False, default=CallStatus.INITIATED, index=True
    )
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_decision: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    task = relationship("TaskORM", back_populates="calls")
    intervention = relationship("HumanInterventionORM", back_populates="calls")
