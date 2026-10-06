"""Opportunity ORM model."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from orvyn.database.base import Base
from orvyn.domain.opportunity import OpportunityStatus, OpportunityType


class OpportunityORM(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    opportunity_type: Mapped[OpportunityType] = mapped_column(Enum(OpportunityType), nullable=False)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_relocation: Mapped[bool] = mapped_column(Boolean, default=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requirements: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[OpportunityStatus] = mapped_column(
        Enum(OpportunityStatus), nullable=False, default=OpportunityStatus.DISCOVERED, index=True
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_opportunities_user_status", "user_id", "status"),
    )
