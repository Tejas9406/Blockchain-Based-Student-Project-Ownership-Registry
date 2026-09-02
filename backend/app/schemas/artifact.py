from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ArtifactCategory


class ArtifactResponse(BaseModel):
    """
    Standard Artifact response schema conforming to FRONTEND_BACKEND_CONTRACT.md Section 4.
    Strictly excludes internal database UUIDs, filesystem paths, and storage secrets.
    """
    public_id: str = Field(
        ...,
        description="Public artifact identifier (ART-YYYYMM-XXXXX)",
        examples=["ART-202609-11E54"],
    )
    file_name: str = Field(
        ...,
        description="Original sanitized file name",
        examples=["architecture_v1.pdf"],
    )
    file_type: str = Field(
        ...,
        description="MIME content type",
        examples=["application/pdf"],
    )
    file_size_bytes: int = Field(
        ...,
        description="File size in bytes",
        examples=[1048576],
    )
    sha256_hash: str = Field(
        ...,
        description="Cryptographic SHA-256 digest (64-char lowercase hex)",
        examples=["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    )
    ipfs_cid: Optional[str] = Field(
        default=None,
        description="IPFS CIDv1 content address (null until decentralized pinning occurs)",
        examples=["bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"],
    )
    artifact_category: ArtifactCategory = Field(
        ...,
        description="Artifact classification category (SOURCE_CODE, DOCUMENTATION, DESIGN_SPEC, PRESENTATION, OTHER)",
        examples=[ArtifactCategory.DESIGN_SPEC],
    )
    uploaded_at: datetime = Field(
        ...,
        description="UTC upload timestamp formatted as ISO 8601 string",
    )

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
ArtifactItem = ArtifactResponse
