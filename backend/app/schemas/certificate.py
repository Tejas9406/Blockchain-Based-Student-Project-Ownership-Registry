from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CertificateMetadataData(BaseModel):
    """
    Metadata representation for a verified project ownership certificate (API_CONTRACT Section 10.1).
    All fields are derived authoritatively from database and blockchain state.
    """
    registration_id: str = Field(
        ...,
        description="Universal certificate registration ID (REG-YYYY-XXXXX)",
        examples=["REG-2026-A8F92D"],
    )
    project_title: str = Field(
        ...,
        description="Official title of the registered academic project",
        examples=["Decentralized IPFS Academic Registry"],
    )
    version_tag: str = Field(
        ...,
        description="Version tag (e.g. v1.0)",
        examples=["v1.0"],
    )
    lifecycle_stage: Optional[str] = Field(
        default="PROTOTYPE",
        description="Milestone lifecycle stage (IDEA, PROTOTYPE, FINAL_SUBMISSION, etc.)",
        examples=["PROTOTYPE"],
    )
    authors: List[str] = Field(
        default_factory=list,
        description="Ordered list of verified student authors / contributors",
        examples=[["Tejas Sharma", "Aman Verma"]],
    )
    institution: Optional[str] = Field(
        default="National Institute of Technology",
        description="Academic institution or university affiliation",
        examples=["National Institute of Technology"],
    )
    department: Optional[str] = Field(
        default=None,
        description="Academic department",
        examples=["Computer Science & Engineering"],
    )
    anchored_timestamp: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when the version was anchored on-chain",
    )
    transaction_hash: str = Field(
        ...,
        description="Blockchain transaction hash of the registration",
        examples=["0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb"],
    )
    block_number: Optional[int] = Field(
        default=None,
        description="Block number where transaction was confirmed",
        examples=[1024],
    )
    composite_sha256: Optional[str] = Field(
        default=None,
        description="Deterministic 64-character hex composite digest of project artifacts",
        examples=["a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8"],
    )
    ipfs_root_cid: Optional[str] = Field(
        default=None,
        description="IPFS root directory CID containing registered artifacts",
        examples=["bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"],
    )
    verification_url: str = Field(
        ...,
        description="Direct public URL to verify this certificate on the portal",
        examples=["https://registry.sih2026.edu/verify/REG-2026-A8F92D"],
    )
    qr_code_svg_url: str = Field(
        ...,
        description="URL to fetch the QR verification code SVG",
        examples=["https://registry.sih2026.edu/api/v1/certificates/REG-2026-A8F92D/qr.svg"],
    )
    pdf_download_url: str = Field(
        ...,
        description="Direct download URL for the official PDF certificate",
        examples=["https://registry.sih2026.edu/api/v1/certificates/REG-2026-A8F92D/download"],
    )
    dispute_status: str = Field(
        default="NONE",
        description="Dispute standing (NONE or REJECTED)",
        examples=["NONE"],
    )

    model_config = ConfigDict(from_attributes=True)


class CertificateMetadataResponse(BaseModel):
    """Envelope response for certificate metadata."""
    success: bool = True
    data: CertificateMetadataData
