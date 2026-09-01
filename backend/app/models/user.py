import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.project_member import ProjectMember
    from app.models.dispute import Dispute
    from app.models.notification import Notification


class User(Base):
    __tablename__ = "users"

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
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    institution_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        default=UserRole.STUDENT,
        nullable=False,
    )
    wallet_address: Mapped[Optional[str]] = mapped_column(
        String(42),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project_memberships: Mapped[List["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    disputes_raised: Mapped[List["Dispute"]] = relationship(
        "Dispute",
        foreign_keys="Dispute.claimant_user_id",
        back_populates="claimant",
        cascade="all, delete-orphan",
    )
    disputes_resolved: Mapped[List["Dispute"]] = relationship(
        "Dispute",
        foreign_keys="Dispute.resolved_by_admin_id",
        back_populates="resolver",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User public_id={self.public_id} email={self.email} role={self.role}>"
