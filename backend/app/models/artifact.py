import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import ArtifactCategory

if TYPE_CHECKING:
    from app.models.project_version import ProjectVersion


class Artifact(Base):
    __tablename__ = "artifacts"

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
    version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_versions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    sha256_hash: Mapped[str] = mapped_column(
        String(64),
        index=True,
        nullable=False,
    )
    ipfs_cid: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        default=None,
    )
    artifact_category: Mapped[ArtifactCategory] = mapped_column(
        Enum(ArtifactCategory, name="artifact_category", native_enum=True),
        default=ArtifactCategory.OTHER,
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    version: Mapped[Optional["ProjectVersion"]] = relationship(
        "ProjectVersion",
        back_populates="artifacts",
    )

    def __repr__(self) -> str:
        return f"<Artifact public_id={self.public_id} file_name={self.file_name} sha256={self.sha256_hash[:12]}...>"
