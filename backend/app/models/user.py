import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    """
    SQLAlchemy ORM Model for User entity.
    Corresponds to USER table in DATABASE_DESIGN.md (Section 3).
    """
    __tablename__ = "users"

    # Internal Primary Key (RFC 4122 UUIDv4) - Internal DB Only
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        index=True
    )

    # Public Reference ID (USR-YYYYMM-XXXXX) - Exposed to Frontend/API
    public_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False
    )

    # Normalized lowercase email
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    # Stored Argon2id password hash
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Full legal name
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Institutional ID (College / University roll/registration number)
    institution_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # College / University Name (optional)
    institution_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    # Academic Department (e.g. Computer Science & Engineering)
    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Role (STUDENT | FACULTY | ADMIN | VERIFIER)
    role: Mapped[str] = mapped_column(
        String(50),
        default="STUDENT",
        nullable=False
    )

    # Optional EVM Wallet Address (0x...)
    wallet_address: Mapped[Optional[str]] = mapped_column(
        String(42),
        nullable=True
    )

    # Account Active Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Institutional Verification Status
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Timestamps in UTC
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    @property
    def password_hash(self) -> str:
        """Convenience property alias for hashed_password."""
        return self.hashed_password

    @password_hash.setter
    def password_hash(self, value: str) -> None:
        self.hashed_password = value
