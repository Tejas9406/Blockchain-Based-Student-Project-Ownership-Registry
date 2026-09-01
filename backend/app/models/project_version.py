import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import AnchoringStatus, DisputeStatus, ProjectVersionStage

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.artifact import Artifact
    from app.models.blockchain_record import BlockchainRecord


class ProjectVersion(Base):
    __tablename__ = "project_versions"
    __table_args__ = (
        UniqueConstraint("project_id", "version_index", name="uq_project_version_index"),
    )

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
    registration_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=True,
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=True,
    )
    version_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    version_tag: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    lifecycle_stage: Mapped[ProjectVersionStage] = mapped_column(
        Enum(ProjectVersionStage, name="project_version_stage", native_enum=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    composite_sha256: Mapped[Optional[str]] = mapped_column(
        String(66),
        nullable=True,
    )
    ipfs_root_cid: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    anchoring_status: Mapped[AnchoringStatus] = mapped_column(
        Enum(AnchoringStatus, name="anchoring_status", native_enum=True),
        default=AnchoringStatus.DRAFT,
        nullable=False,
    )
    dispute_status: Mapped[DisputeStatus] = mapped_column(
        Enum(DisputeStatus, name="dispute_status", native_enum=True),
        default=DisputeStatus.NONE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="versions",
    )
    artifacts: Mapped[List["Artifact"]] = relationship(
        "Artifact",
        back_populates="version",
        cascade="all, delete-orphan",
        order_by="Artifact.file_name",
    )
    blockchain_record: Mapped[Optional["BlockchainRecord"]] = relationship(
        "BlockchainRecord",
        back_populates="version",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ProjectVersion public_id={self.public_id} reg_id={self.registration_id} stage={self.lifecycle_stage} status={self.anchoring_status}>"
