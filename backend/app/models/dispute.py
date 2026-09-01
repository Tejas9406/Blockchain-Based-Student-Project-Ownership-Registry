import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import DisputeStatus, DisputeType

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    public_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claimant_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dispute_type: Mapped[DisputeType] = mapped_column(
        Enum(DisputeType, name="dispute_type", native_enum=True),
        nullable=False,
    )
    claim_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evidence_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    status: Mapped[DisputeStatus] = mapped_column(
        Enum(DisputeStatus, name="dispute_status", native_enum=True),
        default=DisputeStatus.OPEN,
        nullable=False,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    resolved_by_admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="disputes",
    )
    claimant: Mapped["User"] = relationship(
        "User",
        foreign_keys=[claimant_user_id],
        back_populates="disputes_raised",
    )
    resolver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[resolved_by_admin_id],
        back_populates="disputes_resolved",
    )

    def __repr__(self) -> str:
        return f"<Dispute public_id={self.public_id} project_id={self.project_id} status={self.status}>"
