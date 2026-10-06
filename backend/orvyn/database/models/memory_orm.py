"""Memory ORM model."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import JSON, DateTime, Enum, Float, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from orvyn.database.base import Base
from orvyn.domain.memory import MemoryCategory


class MemoryORM(Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    category: Mapped[MemoryCategory] = mapped_column(Enum(MemoryCategory), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    provenance_source: Mapped[str] = mapped_column(String(255), nullable=False)
    provenance_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_memories_user_category", "user_id", "category"),
    )
