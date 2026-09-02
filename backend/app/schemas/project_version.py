from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import AnchoringStatus, DisputeStatus, ProjectVersionStage


class BlockchainProofSummary(BaseModel):
    """
    Public blockchain receipt proof summary.
    Excludes private internal database identifiers and node secrets.
    """
    transaction_hash: str = Field(..., description="EVM transaction hash")
    block_number: Optional[int] = Field(default=None, description="Mined block number")
    network_name: str = Field(default="hardhat", description="Target network name (hardhat, sepolia, etc.)")
    anchored_timestamp: Optional[datetime] = Field(default=None, description="On-chain block timestamp UTC")

    model_config = ConfigDict(from_attributes=True)


class ArtifactItemSummary(BaseModel):
    """
    Public representation of an artifact file associated with a version snapshot.
    """
    public_id: str = Field(..., description="Public artifact identifier (ART-YYYYMM-XXXXX)")
    file_name: str = Field(..., description="Original uploaded file name")
    file_type: str = Field(..., description="MIME content type")
    file_size_bytes: int = Field(..., description="File size in bytes")
    sha256_hash: str = Field(..., description="SHA-256 cryptographic digest")
    ipfs_cid: str = Field(..., description="IPFS CIDv1 address")
    artifact_category: str = Field(..., description="Artifact category classification")
    uploaded_at: datetime = Field(..., description="Upload timestamp in UTC")

    model_config = ConfigDict(from_attributes=True)


class ProjectVersionCreateRequest(BaseModel):
    """
    Request payload for creating a project milestone version (API_CONTRACT.md Section 7.1).
    Strictly forbids client-injected internal UUIDs, registration IDs, timestamps, or blockchain status.
    """
    version_tag: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Version tag label, e.g. v1.0",
        examples=["v1.0"],
    )
    lifecycle_stage: ProjectVersionStage = Field(
        ...,
        description="Lifecycle milestone stage (IDEA, DESIGN, PROTOTYPE, FINAL)",
        examples=["DESIGN"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Milestone version title",
        examples=["System Architecture & Threat Model"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed milestone notes or changelog",
        examples=["Initial architectural specifications and threat model analysis."],
    )
    artifact_ids: Optional[List[str]] = Field(
        default_factory=list,
        description="List of public artifact IDs (ART-YYYYMM-XXXXX) to attach to this version",
        examples=[["ART-202608-11E54", "ART-202608-11E55"]],
    )

    @field_validator("version_tag", "title")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or whitespace only.")
        return trimmed

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None

    @field_validator("artifact_ids")
    @classmethod
    def validate_artifact_ids(cls, v: Optional[List[str]]) -> List[str]:
        if not v:
            return []
        cleaned = []
        for item in v:
            if isinstance(item, str):
                trimmed = item.strip()
                if trimmed:
                    cleaned.append(trimmed)
        return cleaned


class ProjectVersionDetail(BaseModel):
    """
    Full public representation of a project milestone version (FRONTEND_BACKEND_CONTRACT.md Section 4).
    Strictly excludes internal database UUIDs, private node keys, and database operational fields.
    """
    public_id: str = Field(..., description="Public version identifier (VER-YYYYMM-XXXXX)")
    registration_id: Optional[str] = Field(
        default=None,
        description="Universal certificate registration ID (REG-YYYY-XXXXX)",
    )
    version_index: int = Field(..., description="Sequential version index (1, 2, 3...)")
    version_tag: str = Field(..., description="Version tag label (e.g. v1.0)")
    lifecycle_stage: ProjectVersionStage = Field(..., description="Lifecycle stage (IDEA, DESIGN, PROTOTYPE, FINAL)")
    title: str = Field(..., description="Milestone title")
    description: Optional[str] = Field(default=None, description="Milestone notes or description")
    composite_sha256: Optional[str] = Field(
        default=None,
        description="Deterministic 64-char hex composite SHA-256 hash",
    )
    ipfs_root_cid: Optional[str] = Field(
        default=None,
        description="Root IPFS directory DAG CID",
    )
    anchoring_status: AnchoringStatus = Field(
        ...,
        description="Anchoring lifecycle status (DRAFT, PENDING, ANCHORING, ANCHORED, FAILED)",
    )
    dispute_status: DisputeStatus = Field(
        ...,
        description="Independent dispute status (NONE, OPEN, UNDER_REVIEW, RESOLVED, REJECTED)",
    )
    artifacts: Optional[List[ArtifactItemSummary]] = Field(
        default=None,
        description="Artifact files linked to this version milestone",
    )
    blockchain_record: Optional[BlockchainProofSummary] = Field(
        default=None,
        description="Anchored blockchain receipt proof if available",
    )
    created_at: datetime = Field(..., description="Creation timestamp in UTC")

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
ProjectVersionSummary = ProjectVersionDetail
ProjectVersionResponse = ProjectVersionDetail
