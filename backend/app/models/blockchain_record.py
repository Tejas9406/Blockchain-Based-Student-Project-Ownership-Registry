import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.project_version import ProjectVersion


class BlockchainRecord(Base):
    __tablename__ = "blockchain_records"

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
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_versions.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    transaction_hash: Mapped[str] = mapped_column(
        String(66),
        index=True,
        nullable=False,
    )
    block_number: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    block_hash: Mapped[Optional[str]] = mapped_column(
        String(66),
        nullable=True,
    )
    onchain_record_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
    )
    smart_contract_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
    )
    anchored_hash: Mapped[str] = mapped_column(
        String(66),
        nullable=False,
    )
    ipfs_cid_anchored: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    submitter_wallet: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
    )
    author_wallet: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
    )
    network_name: Mapped[str] = mapped_column(
        String(50),
        default="hardhat",
        nullable=False,
    )
    chain_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    anchored_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    version: Mapped["ProjectVersion"] = relationship(
        "ProjectVersion",
        back_populates="blockchain_record",
    )

    def __repr__(self) -> str:
        return f"<BlockchainRecord public_id={self.public_id} tx={self.transaction_hash[:10]}... block={self.block_number}>"
