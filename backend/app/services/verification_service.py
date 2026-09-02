import hashlib
import re
from typing import Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.blockchain_provider import (
    BlockchainVerificationProvider,
    get_blockchain_provider,
)
from app.core.exceptions import NotFoundError, ValidationException
from app.models.artifact import Artifact
from app.models.blockchain_record import BlockchainRecord
from app.models.enums import AnchoringStatus, DisputeStatus
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.schemas.verification import (
    VerificationBlockchainProof,
    VerificationProjectSummary,
    VerificationResponseData,
    VerificationVersionSummary,
)

# Constants
REGISTRATION_ID_PATTERN = re.compile(r"^REG-\d{4}-[A-Z0-9]{5}$")
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
MAX_ARTIFACT_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
STREAM_CHUNK_SIZE: int = 64 * 1024  # 64 KB chunks for memory-safe streaming


def _build_project_summary(project: Project) -> VerificationProjectSummary:
    """Extracts public project summary metadata without leaking internal UUIDs."""
    institution = None
    if project.members:
        owner_member = next((m for m in project.members if m.is_owner), None)
        if owner_member and owner_member.user and owner_member.user.institution_id:
            institution = owner_member.user.institution_id
        elif project.members[0].user and project.members[0].user.institution_id:
            institution = project.members[0].user.institution_id

    if not institution:
        institution = "National Institute of Technology"

    return VerificationProjectSummary(
        public_id=project.public_id,
        title=project.title,
        department=project.department,
        institution_name=institution,
    )


async def verify_by_registration_id(
    db: Session,
    registration_id: str,
    provider: Optional[BlockchainVerificationProvider] = None,
) -> VerificationResponseData:
    """
    Verifies project ownership proof using the public registration ID (REG-YYYY-XXXXX).
    Returns authoritative project and version metadata along with on-chain proof if anchored.
    """
    normalized_id = registration_id.strip().upper()
    if not REGISTRATION_ID_PATTERN.match(normalized_id):
        raise ValidationException(
            code="INVALID_REGISTRATION_ID_FORMAT",
            message=f"Invalid registration ID format '{registration_id}'. Expected format: REG-YYYY-XXXXX (e.g. REG-2026-A8F92).",
            details={"registration_id": registration_id},
        )

    # 1. Lookup ProjectVersion
    version = db.execute(
        select(ProjectVersion).where(ProjectVersion.registration_id == normalized_id)
    ).scalar_one_or_none()

    if not version:
        raise NotFoundError(
            code="REGISTRATION_NOT_FOUND",
            message=f"Registration ID '{normalized_id}' was not found in the registry.",
            details={"registration_id": normalized_id},
        )

    project = version.project

    # 2. Query blockchain provider abstraction
    provider = provider or get_blockchain_provider()
    onchain_res = await provider.verify_project_version(
        registration_id=normalized_id,
        expected_hash=version.composite_sha256,
    )

    record: Optional[BlockchainRecord] = version.blockchain_record
    dispute_val = (
        version.dispute_status.value
        if hasattr(version.dispute_status, "value")
        else str(version.dispute_status)
    )
    anchoring_val = (
        version.anchoring_status.value
        if hasattr(version.anchoring_status, "value")
        else str(version.anchoring_status)
    )

    blockchain_proof: Optional[VerificationBlockchainProof] = None
    if onchain_res and onchain_res.is_valid:
        blockchain_proof = VerificationBlockchainProof(
            transaction_hash=onchain_res.transaction_hash
            or (record.transaction_hash if record else "0x0"),
            block_number=onchain_res.block_number or (record.block_number if record else 0),
            block_timestamp=onchain_res.anchored_timestamp
            or (record.anchored_timestamp if record else None),
            smart_contract_address=onchain_res.smart_contract_address
            or (record.smart_contract_address if record else "0x0"),
            author_wallet=onchain_res.author_wallet
            or (record.author_wallet if record else "0x0"),
            dispute_status=onchain_res.dispute_status,
            match_confirmed=True,
        )
    elif record:
        blockchain_proof = VerificationBlockchainProof(
            transaction_hash=record.transaction_hash,
            block_number=record.block_number,
            block_timestamp=record.anchored_timestamp,
            smart_contract_address=record.smart_contract_address,
            author_wallet=record.author_wallet,
            dispute_status=dispute_val,
            match_confirmed=True,
        )

    # Determine validity: must have no active disputes and not be failed
    is_valid = (
        dispute_val == "NONE" or dispute_val == DisputeStatus.NONE.value
    ) and anchoring_val != "FAILED"

    msg = None
    if dispute_val != "NONE" and dispute_val != DisputeStatus.NONE.value:
        msg = f"Project version is currently under dispute ({dispute_val})."
        is_valid = False
    elif not blockchain_proof:
        msg = f"Project version registration confirmed in database ({anchoring_val}); awaiting blockchain anchoring."

    return VerificationResponseData(
        is_valid=is_valid,
        registration_id=normalized_id,
        verification_method="REGISTRATION_ID",
        anchoring_status=anchoring_val,
        project=_build_project_summary(project),
        version=VerificationVersionSummary(
            version_tag=version.version_tag,
            lifecycle_stage=(
                version.lifecycle_stage.value
                if hasattr(version.lifecycle_stage, "value")
                else str(version.lifecycle_stage)
            ),
            composite_sha256=version.composite_sha256,
            ipfs_root_cid=version.ipfs_root_cid,
        ),
        blockchain_proof=blockchain_proof,
        message=msg,
    )


async def verify_by_hash(
    db: Session,
    sha256_hash: str,
    registration_id: Optional[str] = None,
    provider: Optional[BlockchainVerificationProvider] = None,
) -> VerificationResponseData:
    """
    Verifies project ownership proof against a 64-character hexadecimal SHA-256 hash.
    Matches against composite version hashes or individual artifact hashes.
    """
    clean_hash = sha256_hash.strip().lower()
    if not SHA256_PATTERN.match(clean_hash):
        raise ValidationException(
            code="INVALID_HASH_FORMAT",
            message="Hash must be a valid 64-character hexadecimal SHA-256 string.",
            details={"sha256_hash": sha256_hash},
        )

    normalized_reg_id = registration_id.strip().upper() if registration_id else None
    if normalized_reg_id and not REGISTRATION_ID_PATTERN.match(normalized_reg_id):
        raise ValidationException(
            code="INVALID_REGISTRATION_ID_FORMAT",
            message=f"Invalid registration ID format '{registration_id}'. Expected format: REG-YYYY-XXXXX.",
            details={"registration_id": registration_id},
        )

    # 1. Search for matching ProjectVersion by composite_sha256
    version_query = select(ProjectVersion).where(ProjectVersion.composite_sha256 == clean_hash)
    if normalized_reg_id:
        version_query = version_query.where(ProjectVersion.registration_id == normalized_reg_id)
    matched_version = db.execute(version_query).scalars().first()

    matched_artifact = None
    if not matched_version:
        # 2. Search for matching Artifact by sha256_hash
        artifact_query = select(Artifact).where(Artifact.sha256_hash == clean_hash)
        artifacts = db.execute(artifact_query).scalars().all()
        for art in artifacts:
            if art.version:
                if normalized_reg_id and art.version.registration_id != normalized_reg_id:
                    continue
                matched_artifact = art
                matched_version = art.version
                break

    if not matched_version:
        reg_ctx = f" for registration ID '{normalized_reg_id}'" if normalized_reg_id else ""
        return VerificationResponseData(
            is_valid=False,
            registration_id=normalized_reg_id,
            verification_method="SHA256_HASH",
            matched_hash=clean_hash,
            message=f"Submitted SHA-256 hash does not match any registered project version or artifact{reg_ctx}.",
        )

    project = matched_version.project
    provider = provider or get_blockchain_provider()
    onchain_res = await provider.verify_project_version(
        registration_id=matched_version.registration_id,
        expected_hash=clean_hash,
    )

    record: Optional[BlockchainRecord] = matched_version.blockchain_record
    dispute_val = (
        matched_version.dispute_status.value
        if hasattr(matched_version.dispute_status, "value")
        else str(matched_version.dispute_status)
    )
    anchoring_val = (
        matched_version.anchoring_status.value
        if hasattr(matched_version.anchoring_status, "value")
        else str(matched_version.anchoring_status)
    )

    blockchain_proof: Optional[VerificationBlockchainProof] = None
    if onchain_res and onchain_res.is_valid:
        blockchain_proof = VerificationBlockchainProof(
            transaction_hash=onchain_res.transaction_hash
            or (record.transaction_hash if record else "0x0"),
            block_number=onchain_res.block_number or (record.block_number if record else 0),
            block_timestamp=onchain_res.anchored_timestamp
            or (record.anchored_timestamp if record else None),
            smart_contract_address=onchain_res.smart_contract_address
            or (record.smart_contract_address if record else "0x0"),
            author_wallet=onchain_res.author_wallet
            or (record.author_wallet if record else "0x0"),
            dispute_status=onchain_res.dispute_status,
            match_confirmed=True,
        )
    elif record:
        blockchain_proof = VerificationBlockchainProof(
            transaction_hash=record.transaction_hash,
            block_number=record.block_number,
            block_timestamp=record.anchored_timestamp,
            smart_contract_address=record.smart_contract_address,
            author_wallet=record.author_wallet,
            dispute_status=dispute_val,
            match_confirmed=True,
        )

    is_valid = (
        dispute_val == "NONE" or dispute_val == DisputeStatus.NONE.value
    ) and anchoring_val != "FAILED"

    msg = "Cryptographic SHA-256 match confirmed against registered project records."
    if not is_valid:
        msg = f"Hash matched record with dispute standing: {dispute_val}"
    elif not blockchain_proof:
        msg = f"Cryptographic SHA-256 match confirmed; awaiting blockchain anchoring ({anchoring_val})."

    return VerificationResponseData(
        is_valid=is_valid,
        registration_id=matched_version.registration_id,
        verification_method="SHA256_HASH",
        anchoring_status=anchoring_val,
        matched_hash=clean_hash,
        matched_file_name=matched_artifact.file_name if matched_artifact else None,
        project=_build_project_summary(project),
        version=VerificationVersionSummary(
            version_tag=matched_version.version_tag,
            lifecycle_stage=(
                matched_version.lifecycle_stage.value
                if hasattr(matched_version.lifecycle_stage, "value")
                else str(matched_version.lifecycle_stage)
            ),
            composite_sha256=matched_version.composite_sha256,
            ipfs_root_cid=matched_version.ipfs_root_cid,
        ),
        blockchain_proof=blockchain_proof,
        message=msg,
    )


async def verify_by_file(
    db: Session,
    file: UploadFile,
    registration_id: Optional[str] = None,
    provider: Optional[BlockchainVerificationProvider] = None,
) -> VerificationResponseData:
    """
    Verifies project ownership proof from an uploaded file directly.
    Streams chunks in memory-safe 64 KB blocks, calculates SHA-256,
    and immediately discards the file content without saving to disk or database.
    """
    sha256_hasher = hashlib.sha256()
    total_bytes_read = 0

    while True:
        chunk = await file.read(STREAM_CHUNK_SIZE)
        if not chunk:
            break
        total_bytes_read += len(chunk)
        if total_bytes_read > MAX_ARTIFACT_SIZE_BYTES:
            raise ValidationException(
                code="FILE_TOO_LARGE",
                message=f"File exceeds maximum allowed size of 50 MB ({MAX_ARTIFACT_SIZE_BYTES} bytes).",
                details={
                    "max_allowed_bytes": MAX_ARTIFACT_SIZE_BYTES,
                    "bytes_read": total_bytes_read,
                },
            )
        sha256_hasher.update(chunk)

    if total_bytes_read == 0:
        raise ValidationException(
            code="EMPTY_FILE_NOT_ALLOWED",
            message="Uploaded verification file cannot be empty (0 bytes).",
            details={"file_size_bytes": 0},
        )

    calculated_hash = sha256_hasher.hexdigest().lower()

    # Re-use verify_by_hash for registry query
    res = await verify_by_hash(
        db=db,
        sha256_hash=calculated_hash,
        registration_id=registration_id,
        provider=provider,
    )
    res.verification_method = "FILE"
    if not res.is_valid:
        res.message = f"Uploaded file content (SHA-256: {calculated_hash}) does not match any registered artifact in the registry."

    return res
