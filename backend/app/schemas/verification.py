from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class VerifyHashRequest(BaseModel):
    """Payload for raw SHA-256 hash verification."""
    sha256_hash: str = Field(
        ...,
        description="64-character hexadecimal SHA-256 hash",
        examples=["9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"],
    )
    registration_id: Optional[str] = Field(
        None,
        description="Optional project registration ID to verify against (e.g. REG-2026-A8F92)",
        examples=["REG-2026-A8F92"],
    )


class VerificationProjectSummary(BaseModel):
    """Public project summary included in verification proofs."""
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    title: str
    department: str
    institution_name: Optional[str] = None


class VerificationVersionSummary(BaseModel):
    """Public project version summary included in verification proofs."""
    model_config = ConfigDict(from_attributes=True)

    version_tag: str
    lifecycle_stage: str
    composite_sha256: Optional[str] = None
    ipfs_root_cid: Optional[str] = None


class VerificationBlockchainProof(BaseModel):
    """Authoritative on-chain proof metadata conforming to API_CONTRACT Section 9.1."""
    model_config = ConfigDict(from_attributes=True)

    transaction_hash: str
    block_number: int
    block_timestamp: Optional[datetime] = None
    smart_contract_address: str
    author_wallet: str
    dispute_status: str = "NONE"
    match_confirmed: bool = True


class VerificationResponseData(BaseModel):
    """Universal public verification response payload."""
    model_config = ConfigDict(from_attributes=True)

    is_valid: bool
    registration_id: Optional[str] = None
    verification_method: str = "REGISTRATION_ID"
    anchoring_status: Optional[str] = None
    matched_hash: Optional[str] = None
    matched_file_name: Optional[str] = None
    project: Optional[VerificationProjectSummary] = None
    version: Optional[VerificationVersionSummary] = None
    blockchain_proof: Optional[VerificationBlockchainProof] = None
    message: Optional[str] = None
