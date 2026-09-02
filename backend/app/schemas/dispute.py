from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import DisputeStatus, DisputeType


class DisputeClaimantSummary(BaseModel):
    """Public representation of the user who raised the dispute."""
    public_id: str = Field(..., description="Public user identifier (USR-YYYYMM-XXXXX)")
    full_name: str = Field(..., description="Full name of claimant")
    institution_id: Optional[str] = Field(default=None, description="Claimant institution or university")

    model_config = ConfigDict(from_attributes=True)


class DisputeCreateRequest(BaseModel):
    """
    Request payload for filing an ownership or plagiarism dispute (API_CONTRACT Section 11.1).
    Allows identifying the disputed target by project_id, registration_id, or both.
    """
    project_id: Optional[str] = Field(
        default=None,
        description="Public project identifier (PRJ-YYYYMM-XXXXX) or project UUID",
        examples=["PRJ-202609-A8F92"],
    )
    registration_id: Optional[str] = Field(
        default=None,
        description="Public certificate registration ID (REG-YYYY-XXXXX)",
        examples=["REG-2026-A8F92"],
    )
    dispute_type: DisputeType = Field(
        ...,
        description="Nature of the dispute: PLAGIARISM, UNAUTHORIZED_USE, CITATION_FAILURE, OTHER",
        examples=["PLAGIARISM"],
    )
    claim_description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed factual description of the dispute claim and prior art assertion",
        examples=["The architecture diagram and methodology were copied verbatim from our 2024 published paper."],
    )
    evidence_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="IPFS CID or external proof URL demonstrating prior art or plagiarism",
        examples=["bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"],
    )

    @field_validator("claim_description")
    @classmethod
    def validate_claim_description(cls, v: str) -> str:
        v_clean = v.strip()
        if len(v_clean) < 10:
            raise ValueError("Claim description must contain at least 10 non-whitespace characters.")
        return v_clean


class DisputeAdjudicateRequest(BaseModel):
    """
    Request payload for administrative adjudication of a dispute (API_CONTRACT Section 12.1).
    Restricted to ADMIN role only.
    """
    resolution_status: DisputeStatus = Field(
        ...,
        description="Adjudication outcome: RESOLVED (claim upheld) or REJECTED (claim dismissed)",
        examples=["REJECTED"],
    )
    resolution_notes: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Administrative rationale explaining the evidence evaluation and outcome",
        examples=["Claimant failed to demonstrate prior art; on-chain timestamp confirms respondent precedence."],
    )

    @field_validator("resolution_status")
    @classmethod
    def validate_status(cls, v: DisputeStatus) -> DisputeStatus:
        if v not in (DisputeStatus.RESOLVED, DisputeStatus.REJECTED):
            raise ValueError("Adjudication resolution_status must be either RESOLVED or REJECTED.")
        return v

    @field_validator("resolution_notes")
    @classmethod
    def validate_notes(cls, v: str) -> str:
        v_clean = v.strip()
        if len(v_clean) < 5:
            raise ValueError("Resolution notes must contain at least 5 non-whitespace characters.")
        return v_clean


class DisputeDetailResponse(BaseModel):
    """
    Full public representation of a dispute record with on-chain tracking metadata.
    """
    public_id: str = Field(..., description="Public dispute identifier (DSP-YYYYMM-XXXXX)")
    project_public_id: str = Field(..., description="Target project public identifier")
    project_title: str = Field(..., description="Target project title")
    registration_id: Optional[str] = Field(default=None, description="Disputed certificate registration ID")
    dispute_type: str = Field(..., description="Dispute classification category")
    claim_description: str = Field(..., description="Claimant detailed description")
    evidence_url: Optional[str] = Field(default=None, description="Evidence reference URL or IPFS CID")
    status: str = Field(..., description="Current dispute status (OPEN, UNDER_REVIEW, RESOLVED, REJECTED)")
    resolution_notes: Optional[str] = Field(default=None, description="Admin adjudication notes if resolved")
    transaction_hash: Optional[str] = Field(default=None, description="On-chain raiseDispute transaction hash")
    resolution_transaction_hash: Optional[str] = Field(default=None, description="On-chain resolveDispute transaction hash")
    claimant: Optional[DisputeClaimantSummary] = Field(default=None, description="Claimant details")
    created_at: datetime = Field(..., description="Filing timestamp UTC")
    resolved_at: Optional[datetime] = Field(default=None, description="Adjudication timestamp UTC if resolved")

    model_config = ConfigDict(from_attributes=True)


class DisputeListResponse(BaseModel):
    """List of dispute records."""
    items: List[DisputeDetailResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
