import hashlib
import re
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.blockchain_provider import (
    BlockchainVerificationProvider,
    OnChainVerificationResult,
    get_blockchain_provider,
)
from app.core.config import settings
from app.core.exceptions import (
    BlockchainException,
    NotFoundError,
    ValidationException,
)
from app.models.artifact import Artifact
from app.models.blockchain_record import BlockchainRecord
from app.models.enums import AnchoringStatus, DisputeStatus, ProjectMemberRole
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_version import ProjectVersion
from app.schemas.verification import (
    VerificationBlockchainProof,
    VerificationProjectSummary,
    VerificationResponseData,
    VerificationVersionSummary,
)
from app.services.blockchain_service import normalize_address
from app.storage.ipfs_adapter import IPFSStorageAdapter, get_ipfs_adapter, is_valid_ipfs_cid
from app.utils.hashing import compute_composite_sha256

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


def _resolve_expected_author_wallet(project: Project, record: Optional[BlockchainRecord] = None) -> Optional[str]:
    """Resolves authoritative expected author wallet from BlockchainRecord or project owner/lead."""
    if record and record.author_wallet:
        return normalize_address(record.author_wallet)

    owner_m = next((m for m in project.members if m.is_owner), None)
    if not owner_m:
        owner_m = next(
            (m for m in project.members if m.role_in_project == ProjectMemberRole.LEAD),
            None,
        )

    if owner_m and owner_m.user and owner_m.user.wallet_address:
        return normalize_address(owner_m.user.wallet_address)

    return None


def _resolve_expected_co_author_wallets(project: Project) -> List[str]:
    """Resolves authoritative expected contributor wallet addresses from team members."""
    co_authors = []
    for m in project.members:
        if not m.is_owner and m.user and m.user.wallet_address:
            co_authors.append(normalize_address(m.user.wallet_address))
    return sorted(co_authors)


async def verify_ipfs_artifact_content(
    cid: str,
    expected_sha256: str,
    ipfs_adapter: Optional[IPFSStorageAdapter] = None,
) -> bool:
    """
    Validates that the content stored in IPFS under the specified CID
    matches the expected SHA-256 hash digest.
    Preserves CID validation and SSRF protections via IPFSStorageAdapter.
    """
    if not is_valid_ipfs_cid(cid):
        raise ValidationException(
            code="INVALID_CID_FORMAT",
            message=f"Invalid IPFS CID format: '{cid}'. Expected CIDv0 (Qm...) or CIDv1 (bafy...).",
            details={"cid": cid},
        )

    clean_expected = expected_sha256.strip().lower()
    if not SHA256_PATTERN.match(clean_expected):
        raise ValidationException(
            code="INVALID_HASH_FORMAT",
            message="Expected hash must be a valid 64-character hexadecimal SHA-256 string.",
            details={"expected_sha256": expected_sha256},
        )

    adapter = ipfs_adapter or get_ipfs_adapter()
    content_bytes = await adapter.cat(cid)
    computed_hash = hashlib.sha256(content_bytes).hexdigest().lower()
    return computed_hash == clean_expected


async def verify_by_registration_id(
    db: Session,
    registration_id: str,
    provider: Optional[BlockchainVerificationProvider] = None,
) -> VerificationResponseData:
    """
    Verifies project ownership proof using the public registration ID (REG-YYYY-XXXXX).
    Flow:
    1. Validate registration ID format.
    2. Retrieve trusted ProjectVersion, Project, Artifacts, and BlockchainRecord.
    3. Check anchoring status: FAILED versions are rejected as invalid proofs.
    4. Query on-chain smart contract via BlockchainService / ProjectRegistry.
    5. Compare on-chain data with authoritative database records across all cryptographic
       and ownership fields (hash, CID, version index, lifecycle stage, author, co-authors).
    6. Return verified result or descriptive mismatch report.
    """
    raw_id = registration_id.strip()
    if not REGISTRATION_ID_PATTERN.match(raw_id):
        raise ValidationException(
            code="INVALID_REGISTRATION_ID_FORMAT",
            message=f"Invalid registration ID format '{registration_id}'. Expected format: REG-YYYY-XXXXX (e.g. REG-2026-A8F92).",
            details={"registration_id": registration_id},
        )
    normalized_id = raw_id.upper()

    # 1. Authoritative Lookup in Database
    version = db.execute(
        select(ProjectVersion)
        .options(
            selectinload(ProjectVersion.project).selectinload(Project.members).selectinload(ProjectMember.user),
            selectinload(ProjectVersion.artifacts),
            selectinload(ProjectVersion.blockchain_record),
        )
        .where(ProjectVersion.registration_id == normalized_id)
    ).scalar_one_or_none()

    if not version:
        raise NotFoundError(
            code="REGISTRATION_NOT_FOUND",
            message=f"Registration ID '{normalized_id}' was not found in the registry.",
            details={"registration_id": normalized_id},
        )

    project = version.project
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

    # State Rule (Section 11): FAILED versions must NEVER be reported as valid blockchain ownership proofs
    if anchoring_val == AnchoringStatus.FAILED.value or anchoring_val == "FAILED":
        return VerificationResponseData(
            is_valid=False,
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
            blockchain_proof=None,
            message="Project version anchoring failed. No valid blockchain ownership proof exists.",
        )

    # 2. Query Blockchain Provider
    provider = provider or get_blockchain_provider()
    onchain_proof_data: Optional[Dict[str, Any]] = None
    try:
        onchain_proof_data = await provider.get_project_version(normalized_id)
    except BlockchainException:
        raise
    except Exception as e:
        err_str = str(e).lower()
        if "timeout" in err_str or "timed out" in err_str:
            raise BlockchainException(
                code="BLOCKCHAIN_TIMEOUT",
                message=f"Blockchain call timed out: {str(e)}",
                status_code=504,
            )
        if "connection" in err_str or "refused" in err_str:
            raise BlockchainException(
                code="BLOCKCHAIN_CONNECTION_ERROR",
                message=f"RPC connection failed: {str(e)}",
                status_code=502,
            )
        raise BlockchainException(
            code="BLOCKCHAIN_CONTRACT_ERROR",
            message=f"Blockchain contract query failed: {str(e)}",
            status_code=502,
        )

    onchain_res: Optional[OnChainVerificationResult] = None
    try:
        onchain_res = await provider.verify_project_version(
            registration_id=normalized_id,
            expected_hash=version.composite_sha256,
        )
    except BlockchainException:
        raise
    except Exception as e:
        err_str = str(e).lower()
        if "timeout" in err_str or "timed out" in err_str:
            raise BlockchainException(
                code="BLOCKCHAIN_TIMEOUT",
                message=f"Blockchain call timed out: {str(e)}",
                status_code=504,
            )
        if "connection" in err_str or "refused" in err_str:
            raise BlockchainException(
                code="BLOCKCHAIN_CONNECTION_ERROR",
                message=f"RPC connection failed: {str(e)}",
                status_code=502,
            )
        raise BlockchainException(
            code="BLOCKCHAIN_CONTRACT_ERROR",
            message=f"Blockchain verification call failed: {str(e)}",
            status_code=502,
        )

    # Case: Unanchored (PENDING / DRAFT / ANCHORING) with no blockchain proof
    if not onchain_proof_data and not onchain_res and not record:
        effective_disp = dispute_val.upper()
        is_disp = effective_disp in ("OPEN", "UNDER_REVIEW", "RESOLVED")
        is_valid = not is_disp
        if is_disp:
            if effective_disp == "RESOLVED":
                msg = "Dispute was upheld against this project version (RESOLVED)."
            else:
                msg = f"Project version is currently under dispute ({effective_disp})."
        else:
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
            blockchain_proof=None,
            message=msg,
        )

    # 3. Compare Trusted DB & On-Chain Values
    mismatch_reasons: List[str] = []

    # Verification using full on-chain struct from getProjectVersion
    if onchain_proof_data is not None:
        if not onchain_proof_data.get("exists", False):
            mismatch_reasons.append("Registration proof does not exist in on-chain smart contract storage.")

        if onchain_proof_data.get("registration_id") != normalized_id:
            mismatch_reasons.append(
                f"Registration ID mismatch: on-chain '{onchain_proof_data.get('registration_id')}' != '{normalized_id}'."
            )

        # Composite SHA-256 Hash Comparison
        onchain_hash = str(onchain_proof_data.get("composite_hash") or "").lower().removeprefix("0x")
        expected_hash = str(version.composite_sha256 or "").lower().removeprefix("0x")
        if onchain_hash != expected_hash:
            mismatch_reasons.append(
                f"Cryptographic hash mismatch: on-chain composite hash does not match trusted project version."
            )


        # IPFS Root CID Comparison
        onchain_cid = onchain_proof_data.get("ipfs_root_cid") or onchain_proof_data.get("ipfs_cid")
        if version.ipfs_root_cid and onchain_cid != version.ipfs_root_cid:
            mismatch_reasons.append(
                f"IPFS root CID mismatch: on-chain '{onchain_cid}' != expected '{version.ipfs_root_cid}'."
            )

        # Version Index Comparison
        if onchain_proof_data.get("version_index") != version.version_index:
            mismatch_reasons.append(
                f"Version index mismatch: on-chain index {onchain_proof_data.get('version_index')} != expected {version.version_index}."
            )

        # Lifecycle Stage Comparison
        expected_stage = (
            version.lifecycle_stage.value
            if hasattr(version.lifecycle_stage, "value")
            else str(version.lifecycle_stage)
        ).upper()
        onchain_stage = str(onchain_proof_data.get("lifecycle_stage") or "").upper()
        if onchain_stage != expected_stage:
            mismatch_reasons.append(
                f"Lifecycle stage mismatch: on-chain stage '{onchain_stage}' != expected '{expected_stage}'."
            )

        # Author Wallet Comparison
        expected_author = _resolve_expected_author_wallet(project, record)
        if expected_author:
            onchain_author = normalize_address(onchain_proof_data.get("author"))
            if onchain_author != expected_author:
                mismatch_reasons.append(
                    f"Author wallet mismatch: on-chain author '{onchain_author}' != expected owner wallet '{expected_author}'."
                )

        # Co-Authors Comparison
        expected_co_authors = _resolve_expected_co_author_wallets(project)
        if expected_co_authors:
            onchain_co_authors = sorted(
                [normalize_address(a) for a in onchain_proof_data.get("co_authors", [])]
            )
            if onchain_co_authors != expected_co_authors:
                mismatch_reasons.append(
                    "Co-author wallets mismatch: on-chain contributors do not match expected registered contributors."
                )

        # BlockchainRecord consistency
        if record and onchain_proof_data.get("block_number"):
            if record.block_number != onchain_proof_data.get("block_number"):
                mismatch_reasons.append(
                    f"Blockchain record mismatch: recorded block {record.block_number} != on-chain {onchain_proof_data.get('block_number')}."
                )

    elif onchain_res is not None:
        # Fallback to verifyProjectVersion result if getProjectVersion was not available
        if not onchain_res.is_valid or not onchain_res.match_confirmed:
            mismatch_reasons.append(
                onchain_res.mismatch_reason
                or "Smart contract verifyProjectVersion returned invalid status."
            )

        if onchain_res.composite_hash:
            exp_hash = str(version.composite_sha256 or "").lower().removeprefix("0x")
            res_hash = str(onchain_res.composite_hash).lower().removeprefix("0x")
            if res_hash != exp_hash:
                mismatch_reasons.append(f"Composite hash mismatch: on-chain {res_hash} != {exp_hash}.")

        if onchain_res.version_index is not None and onchain_res.version_index != version.version_index:
            mismatch_reasons.append(
                f"Version index mismatch: on-chain index {onchain_res.version_index} != expected {version.version_index}."
            )

        if onchain_res.lifecycle_stage:
            exp_stage = (
                version.lifecycle_stage.value
                if hasattr(version.lifecycle_stage, "value")
                else str(version.lifecycle_stage)
            ).upper()
            if onchain_res.lifecycle_stage.upper() != exp_stage:
                mismatch_reasons.append(
                    f"Lifecycle stage mismatch: on-chain '{onchain_res.lifecycle_stage}' != expected '{exp_stage}'."
                )

        if onchain_res.author_wallet:
            expected_author = _resolve_expected_author_wallet(project, record)
            if expected_author and normalize_address(onchain_res.author_wallet) != expected_author:
                mismatch_reasons.append(
                    f"Author wallet mismatch: on-chain author does not match expected owner wallet."
                )

        if onchain_res.ipfs_root_cid and version.ipfs_root_cid:
            if onchain_res.ipfs_root_cid != version.ipfs_root_cid:
                mismatch_reasons.append(
                    f"IPFS CID mismatch: on-chain '{onchain_res.ipfs_root_cid}' != expected '{version.ipfs_root_cid}'."
                )

        if onchain_res.co_authors is not None:
            expected_co_authors = _resolve_expected_co_author_wallets(project)
            if expected_co_authors:
                onchain_co_authors = sorted([normalize_address(a) for a in onchain_res.co_authors])
                if onchain_co_authors != expected_co_authors:
                    mismatch_reasons.append("Co-authors mismatch: on-chain contributors do not match expected contributors.")

    elif record:
        # Default fallback when smart contract is unconfigured: verify database consistency
        rec_hash = record.anchored_hash.lower().removeprefix("0x")
        ver_hash = str(version.composite_sha256 or "").lower().removeprefix("0x")
        if rec_hash != ver_hash:
            mismatch_reasons.append("BlockchainRecord hash does not match version composite hash.")

        if version.ipfs_root_cid and record.ipfs_cid_anchored != version.ipfs_root_cid:
            mismatch_reasons.append("BlockchainRecord IPFS CID does not match version root CID.")

    has_mismatch = len(mismatch_reasons) > 0

    # Dispute status check
    onchain_dispute = (
        onchain_proof_data.get("dispute_state")
        if onchain_proof_data
        else (onchain_res.dispute_status if onchain_res else dispute_val)
    )
    effective_dispute = (onchain_dispute or dispute_val or "NONE").upper()
    is_disputed = effective_dispute in ("OPEN", "UNDER_REVIEW", "RESOLVED")

    is_valid = not has_mismatch and not is_disputed

    # Construct authoritative BlockchainProof
    tx_hash = (
        (onchain_proof_data.get("transaction_hash") if onchain_proof_data else None)
        or (onchain_res.transaction_hash if onchain_res else None)
        or (record.transaction_hash if record else "0x0")
    )
    block_num = (
        (onchain_proof_data.get("block_number") if onchain_proof_data else None)
        or (onchain_res.block_number if onchain_res else None)
        or (record.block_number if record else 0)
    )
    block_time = (
        (onchain_proof_data.get("anchored_timestamp") if onchain_proof_data else None)
        or (onchain_res.anchored_timestamp if onchain_res else None)
        or (record.anchored_timestamp if record else None)
    )
    contract_addr = (
        (onchain_res.smart_contract_address if onchain_res else None)
        or (record.smart_contract_address if record else getattr(settings, "PROJECT_REGISTRY_CONTRACT_ADDRESS", "0x0"))
    )
    auth_wallet = (
        (onchain_proof_data.get("author") if onchain_proof_data else None)
        or (onchain_res.author_wallet if onchain_res else None)
        or (record.author_wallet if record else "0x0")
    )

    blockchain_proof = VerificationBlockchainProof(
        transaction_hash=tx_hash,
        block_number=block_num,
        block_timestamp=block_time,
        smart_contract_address=contract_addr or "0x0",
        author_wallet=auth_wallet or "0x0",
        dispute_status=effective_dispute,
        match_confirmed=not has_mismatch,
    )

    msg = None
    if has_mismatch:
        msg = f"Cryptographic verification mismatch: {'; '.join(mismatch_reasons)}"
    elif is_disputed:
        if effective_dispute == "RESOLVED":
            msg = "Dispute was upheld against this project version (RESOLVED)."
        else:
            msg = f"Project version is currently under dispute ({effective_dispute})."

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
    Enforces the server/blockchain trust model: client registration_id is checked
    against the matched record and never accepted as source of truth.
    """
    clean_hash = sha256_hash.strip().lower()
    if not SHA256_PATTERN.match(clean_hash):
        raise ValidationException(
            code="INVALID_HASH_FORMAT",
            message="Hash must be a valid 64-character hexadecimal SHA-256 string.",
            details={"sha256_hash": sha256_hash},
        )

    if registration_id:
        raw_reg_id = registration_id.strip()
        if not REGISTRATION_ID_PATTERN.match(raw_reg_id):
            raise ValidationException(
                code="INVALID_REGISTRATION_ID_FORMAT",
                message=f"Invalid registration ID format '{registration_id}'. Expected format: REG-YYYY-XXXXX.",
                details={"registration_id": registration_id},
            )
        normalized_reg_id = raw_reg_id.upper()
    else:
        normalized_reg_id = None

    # 1. Search for matching ProjectVersion by composite_sha256
    version_query = (
        select(ProjectVersion)
        .options(
            selectinload(ProjectVersion.project).selectinload(Project.members).selectinload(ProjectMember.user),
            selectinload(ProjectVersion.artifacts),
            selectinload(ProjectVersion.blockchain_record),
        )
        .where(ProjectVersion.composite_sha256 == clean_hash)
    )
    if normalized_reg_id:
        version_query = version_query.where(ProjectVersion.registration_id == normalized_reg_id)
    matched_version = db.execute(version_query).scalars().first()

    matched_artifact = None
    if not matched_version:
        # 2. Search for matching Artifact by sha256_hash
        artifact_query = (
            select(Artifact)
            .options(
                selectinload(Artifact.version).selectinload(ProjectVersion.project).selectinload(Project.members).selectinload(ProjectMember.user),
                selectinload(Artifact.version).selectinload(ProjectVersion.artifacts),
                selectinload(Artifact.version).selectinload(ProjectVersion.blockchain_record),
            )
            .where(Artifact.sha256_hash == clean_hash)
        )
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

    # Check cross-project scope if client provided registration_id
    if normalized_reg_id and matched_version.registration_id != normalized_reg_id:
        return VerificationResponseData(
            is_valid=False,
            registration_id=normalized_reg_id,
            verification_method="SHA256_HASH",
            matched_hash=clean_hash,
            message=f"Submitted SHA-256 hash belongs to a different project version than specified registration ID '{normalized_reg_id}'.",
        )

    # Use comprehensive verify_by_registration_id logic for matched version
    base_result = await verify_by_registration_id(
        db=db,
        registration_id=matched_version.registration_id,
        provider=provider,
    )

    base_result.verification_method = "SHA256_HASH"
    base_result.matched_hash = clean_hash
    base_result.matched_file_name = matched_artifact.file_name if matched_artifact else None

    if matched_version.anchoring_status == AnchoringStatus.FAILED or matched_version.anchoring_status.value == "FAILED":
        base_result.is_valid = False
        base_result.blockchain_proof = None
        base_result.message = f"Hash matched project version, but version anchoring failed ({matched_version.anchoring_status.value})."
    elif base_result.is_valid and not base_result.message:
        base_result.message = "Cryptographic SHA-256 match confirmed against registered project records."

    return base_result


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
    if not res.is_valid and not res.message:
        res.message = f"Uploaded file content (SHA-256: {calculated_hash}) does not match any registered artifact in the registry."

    return res
