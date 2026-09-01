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
    """
    SQLAlchemy ORM Model for User entity.
    Corresponds to USER table in DATABASE_DESIGN.md (Section 3).
    """
    __tablename__ = "users"

    # Internal Primary Key (UUIDv4) - Internal DB Only
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Public Reference ID (USR-YYYYMM-XXXXX) - Exposed to Frontend/API
    public_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )

    # Normalized lowercase email
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # Stored Argon2id password hash
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Full legal name
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Institutional ID (College / University roll/registration number)
    institution_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # College / University Name (optional)
    institution_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Academic Department (e.g. Computer Science & Engineering)
    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Role (STUDENT | FACULTY | ADMIN | VERIFIER)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        default=UserRole.STUDENT,
        nullable=False,
    )

    # Optional EVM Wallet Address (0x...)
    wallet_address: Mapped[Optional[str]] = mapped_column(
        String(42),
        nullable=True,
    )

    # Account Active Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Institutional Verification Status
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Timestamps in UTC
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

    @property
    def password_hash(self) -> str:
        """Convenience property alias for hashed_password."""
        return self.hashed_password

    @password_hash.setter
    def password_hash(self, value: str) -> None:
        self.hashed_password = value

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
