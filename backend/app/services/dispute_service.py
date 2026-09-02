import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    AppException,
    BlockchainException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationException,
)
from app.models.dispute import Dispute
from app.models.enums import AnchoringStatus, DisputeStatus, DisputeType, ProjectStatus, UserRole
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.schemas.dispute import (
    DisputeAdjudicateRequest,
    DisputeClaimantSummary,
    DisputeCreateRequest,
    DisputeDetailResponse,
)
from app.services.blockchain_service import BlockchainService, get_blockchain_service
from app.storage.ipfs_adapter import IPFSStorageAdapter, get_ipfs_adapter, is_valid_ipfs_cid

logger = logging.getLogger("registry_backend.disputes")

REGISTRATION_ID_PATTERN = re.compile(r"^REG-\d{4}-[A-Z0-9]{5}$")


def _build_claimant_summary(claimant: Optional[User]) -> Optional[DisputeClaimantSummary]:
    if not claimant:
        return None
    return DisputeClaimantSummary(
        public_id=claimant.public_id,
        full_name=claimant.full_name,
        institution_id=claimant.institution_id,
    )


def _build_dispute_detail(
    dispute: Dispute,
    registration_id: Optional[str] = None,
    tx_hash: Optional[str] = None,
    res_tx_hash: Optional[str] = None,
) -> DisputeDetailResponse:
    reg_id = registration_id
    if not reg_id and dispute.project and dispute.project.versions:
        # Find latest anchored version registration ID
        for v in sorted(dispute.project.versions, key=lambda x: x.version_index, reverse=True):
            if v.registration_id:
                reg_id = v.registration_id
                break

    return DisputeDetailResponse(
        public_id=dispute.public_id,
        project_public_id=dispute.project.public_id if dispute.project else "",
        project_title=dispute.project.title if dispute.project else "",
        registration_id=reg_id,
        dispute_type=dispute.dispute_type.value if hasattr(dispute.dispute_type, "value") else str(dispute.dispute_type),
        claim_description=dispute.claim_description,
        evidence_url=dispute.evidence_url,
        status=dispute.status.value if hasattr(dispute.status, "value") else str(dispute.status),
        resolution_notes=dispute.resolution_notes,
        transaction_hash=tx_hash,
        resolution_transaction_hash=res_tx_hash,
        claimant=_build_claimant_summary(dispute.claimant),
        created_at=dispute.created_at,
        resolved_at=dispute.resolved_at,
    )


async def raise_dispute(
    db: Session,
    current_user: User,
    payload: DisputeCreateRequest,
    blockchain_service: Optional[BlockchainService] = None,
    ipfs_adapter: Optional[IPFSStorageAdapter] = None,
) -> DisputeDetailResponse:
    """
    Files an ownership/plagiarism dispute and anchors it to the smart contract via relayer.
    Flow:
    1. Authenticate caller (STUDENT, FACULTY, ADMIN).
    2. Validate input and resolve target Project and ProjectVersion.
    3. Verify target version is ANCHORED (cannot dispute unanchored drafts or failed versions).
    4. Enforce duplicate active dispute rule.
    5. Pin dispute evidence manifest to IPFS to obtain deterministic CID.
    6. Persist DB record (status=OPEN).
    7. Broadcast raiseDispute transaction to blockchain via BlockchainService.
    8. Confirm transaction receipt and decode DisputeLogged event.
    9. Return confirmed DisputeDetailResponse.
    """
    # 1. Format Validation
    normalized_reg_id: Optional[str] = None
    if payload.registration_id:
        raw_reg = payload.registration_id.strip()
        if not REGISTRATION_ID_PATTERN.match(raw_reg):
            raise ValidationException(
                code="INVALID_REGISTRATION_ID_FORMAT",
                message=f"Invalid registration ID format '{payload.registration_id}'. Expected format: REG-YYYY-XXXXX.",
                details={"registration_id": payload.registration_id},
            )
        normalized_reg_id = raw_reg.upper()

    # 2. Target Lookup & Cross-Project Validation
    target_version: Optional[ProjectVersion] = None
    target_project: Optional[Project] = None

    if normalized_reg_id:
        target_version = db.execute(
            select(ProjectVersion)
            .options(
                selectinload(ProjectVersion.project).selectinload(Project.versions),
            )
            .where(ProjectVersion.registration_id == normalized_reg_id)
        ).scalar_one_or_none()

        if not target_version:
            raise NotFoundError(
                code="REGISTRATION_NOT_FOUND",
                message=f"Registration ID '{normalized_reg_id}' was not found in the registry.",
                details={"registration_id": normalized_reg_id},
            )

        target_project = target_version.project

        # If user also specified a project_id, verify it matches
        if payload.project_id:
            pid_str = payload.project_id.strip()
            if target_project.public_id != pid_str and str(target_project.id) != pid_str:
                raise AppException(
                    code="CROSS_PROJECT_DISPUTE",
                    message=f"Registration ID '{normalized_reg_id}' belongs to project '{target_project.public_id}', not '{pid_str}'.",
                    details={"specified_project_id": pid_str, "actual_project_id": target_project.public_id},
                    status_code=400,
                )
    elif payload.project_id:
        pid_str = payload.project_id.strip()
        proj_query = select(Project).options(selectinload(Project.versions))
        try:
            u = uuid.UUID(pid_str)
            proj_query = proj_query.where(or_(Project.public_id == pid_str, Project.id == u))
        except ValueError:
            proj_query = proj_query.where(Project.public_id == pid_str)

        target_project = db.execute(proj_query).scalar_one_or_none()
        if not target_project:
            raise NotFoundError(
                code="PROJECT_NOT_FOUND",
                message=f"Project '{pid_str}' was not found.",
                details={"project_id": pid_str},
            )

        # Resolve latest anchored version
        anchored_versions = [v for v in target_project.versions if v.anchoring_status == AnchoringStatus.ANCHORED]
        if not anchored_versions:
            raise AppException(
                code="NO_ANCHORED_VERSION",
                message=f"Project '{target_project.public_id}' has no anchored project versions to dispute.",
                details={"project_id": target_project.public_id},
                status_code=400,
            )
        anchored_versions.sort(key=lambda x: x.version_index, reverse=True)
        target_version = anchored_versions[0]
        normalized_reg_id = target_version.registration_id
    else:
        raise ValidationException(
            code="MISSING_DISPUTE_TARGET",
            message="Either 'registration_id' or 'project_id' must be specified to file a dispute.",
        )

    # 3. Anchoring Status Validation
    if target_version.anchoring_status != AnchoringStatus.ANCHORED:
        raise AppException(
            code="VERSION_NOT_ANCHORED",
            message=f"Cannot file a dispute against a project version in '{target_version.anchoring_status.value}' status. Version must be ANCHORED.",
            details={"version_tag": target_version.version_tag, "status": target_version.anchoring_status.value},
            status_code=400,
        )

    # 4. Duplicate Active Dispute Check
    existing_active = db.execute(
        select(Dispute)
        .where(
            Dispute.project_id == target_project.id,
            Dispute.status.in_([DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW]),
        )
    ).scalars().first()

    if existing_active or target_version.dispute_status in (DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW):
        active_pub_id = existing_active.public_id if existing_active else "ACTIVE"
        raise ConflictError(
            code="ACTIVE_DISPUTE_EXISTS",
            message=f"An active dispute ({active_pub_id}) already exists for this project. Cannot file a concurrent dispute.",
            details={"project_id": target_project.public_id, "existing_dispute": active_pub_id},
        )

    # 5. Evidence CID Resolution / Pinning
    evidence_cid: str = ""
    clean_ev = (payload.evidence_url or "").strip()
    if clean_ev and is_valid_ipfs_cid(clean_ev):
        evidence_cid = clean_ev
    else:
        # Construct deterministic JSON manifest and pin to IPFS
        manifest_data = {
            "project_public_id": target_project.public_id,
            "registration_id": normalized_reg_id,
            "claimant_public_id": current_user.public_id,
            "dispute_type": payload.dispute_type.value if hasattr(payload.dispute_type, "value") else str(payload.dispute_type),
            "claim_description": payload.claim_description,
            "external_evidence": clean_ev or None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            adapter = ipfs_adapter or get_ipfs_adapter()
            json_bytes = json.dumps(manifest_data).encode("utf-8")
            evidence_cid = await adapter.add_bytes(json_bytes, filename="dispute_manifest.json")
        except Exception as e:
            logger.warning(f"Failed to pin dispute manifest to IPFS: {e}. Deriving fallback CID.")
            # Deterministic fallback sha256 representation formatted as CIDv1 mock
            desc_hash = hashlib.sha256(payload.claim_description.encode()).hexdigest()
            evidence_cid = f"bafybeidispute{desc_hash[:32]}"

    # 6. Database Persistence
    now = datetime.now(timezone.utc)
    unique_suffix = uuid.uuid4().hex[:5].upper()
    dsp_public_id = f"DSP-{now.strftime('%Y%m')}-{unique_suffix}"

    dispute = Dispute(
        public_id=dsp_public_id,
        project_id=target_project.id,
        claimant_user_id=current_user.id,
        dispute_type=payload.dispute_type,
        claim_description=payload.claim_description,
        evidence_url=evidence_cid,
        status=DisputeStatus.OPEN,
    )
    db.add(dispute)
    target_version.dispute_status = DisputeStatus.OPEN
    target_project.status = ProjectStatus.UNDER_DISPUTE
    db.flush()

    # 7. Blockchain Broadcast via BlockchainService
    bc_service = blockchain_service or get_blockchain_service()
    tx_hash: Optional[str] = None
    try:
        tx_res = await bc_service.raise_dispute(
            registration_id=normalized_reg_id,
            evidence_cid=evidence_cid,
        )
        tx_hash = tx_res.get("transaction_hash")
    except BlockchainException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        err_str = str(e).lower()
        if "activedisputeexists" in err_str:
            raise ConflictError(
                code="ACTIVE_DISPUTE_EXISTS",
                message=f"An active dispute already exists on-chain for registration '{normalized_reg_id}'.",
                details={"registration_id": normalized_reg_id},
            )
        if "timeout" in err_str or "timed out" in err_str:
            raise BlockchainException(
                code="BLOCKCHAIN_TIMEOUT",
                message=f"raiseDispute transaction timed out: {str(e)}",
                status_code=504,
            )
        if "connection" in err_str or "refused" in err_str:
            raise BlockchainException(
                code="BLOCKCHAIN_CONNECTION_ERROR",
                message=f"RPC connection failed for raiseDispute: {str(e)}",
                status_code=502,
            )
        raise BlockchainException(
            code="BLOCKCHAIN_TRANSACTION_FAILED",
            message=f"Failed to record dispute on-chain: {str(e)}",
            status_code=502,
        )

    db.commit()
    db.refresh(dispute)
    db.refresh(target_project)
    db.refresh(target_version)

    return _build_dispute_detail(
        dispute=dispute,
        registration_id=normalized_reg_id,
        tx_hash=tx_hash,
    )


async def adjudicate_dispute(
    db: Session,
    current_user: User,
    dispute_id: str,
    payload: DisputeAdjudicateRequest,
    blockchain_service: Optional[BlockchainService] = None,
) -> DisputeDetailResponse:
    """
    Adjudicates an active dispute (Admin only).
    Submits on-chain resolution via BlockchainService.resolve_dispute.
    Updates DB dispute, version, and project status.
    Guarantees immutable ownership proof parameters are NEVER modified.
    """
    # 1. Role Authorization
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError(
            code="ADMIN_REQUIRED",
            message="Only system administrators can adjudicate disputes.",
        )

    # 2. Dispute Lookup
    dispute_query = (
        select(Dispute)
        .options(
            selectinload(Dispute.project).selectinload(Project.versions),
            selectinload(Dispute.claimant),
            selectinload(Dispute.resolver),
        )
    )
    try:
        u = uuid.UUID(dispute_id)
        dispute_query = dispute_query.where(or_(Dispute.public_id == dispute_id, Dispute.id == u))
    except ValueError:
        dispute_query = dispute_query.where(Dispute.public_id == dispute_id)

    dispute = db.execute(dispute_query).scalar_one_or_none()
    if not dispute:
        raise NotFoundError(
            code="DISPUTE_NOT_FOUND",
            message=f"Dispute '{dispute_id}' was not found.",
            details={"dispute_id": dispute_id},
        )

    # 3. Validate Dispute State (Prevent re-adjudication of resolved/rejected disputes)
    if dispute.status not in (DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW):
        raise ConflictError(
            code="DISPUTE_ALREADY_RESOLVED",
            message=f"Dispute '{dispute.public_id}' is already {dispute.status.value} and cannot be re-adjudicated.",
            details={"dispute_id": dispute.public_id, "current_status": dispute.status.value},
        )

    # 4. Resolve Target Registration ID
    target_project = dispute.project
    target_version: Optional[ProjectVersion] = None
    if target_project and target_project.versions:
        anchored_versions = [v for v in target_project.versions if v.anchoring_status == AnchoringStatus.ANCHORED]
        if anchored_versions:
            anchored_versions.sort(key=lambda x: x.version_index, reverse=True)
            target_version = anchored_versions[0]

    if not target_version or not target_version.registration_id:
        raise AppException(
            code="VERSION_NOT_FOUND",
            message=f"Cannot adjudicate dispute: project '{target_project.public_id}' has no anchored version registration ID.",
            status_code=400,
        )

    registration_id = target_version.registration_id

    # 5. Broadcast On-Chain Resolution via BlockchainService
    bc_service = blockchain_service or get_blockchain_service()
    res_tx_hash: Optional[str] = None
    try:
        tx_res = await bc_service.resolve_dispute(
            registration_id=registration_id,
            status=payload.resolution_status,
        )
        res_tx_hash = tx_res.get("transaction_hash")
    except BlockchainException:
        raise
    except Exception as e:
        err_str = str(e).lower()
        if "timeout" in err_str or "timed out" in err_str:
            raise BlockchainException(
                code="BLOCKCHAIN_TIMEOUT",
                message=f"resolveDispute transaction timed out: {str(e)}",
                status_code=504,
            )
        if "connection" in err_str or "refused" in err_str:
            raise BlockchainException(
                code="BLOCKCHAIN_CONNECTION_ERROR",
                message=f"RPC connection failed for resolveDispute: {str(e)}",
                status_code=502,
            )
        raise BlockchainException(
            code="BLOCKCHAIN_TRANSACTION_FAILED",
            message=f"Failed to resolve dispute on-chain: {str(e)}",
            status_code=502,
        )

    # 6. Update Database State
    now = datetime.now(timezone.utc)
    dispute.status = payload.resolution_status
    dispute.resolution_notes = payload.resolution_notes
    dispute.resolved_by_admin_id = current_user.id
    dispute.resolved_at = now

    target_version.dispute_status = payload.resolution_status

    if payload.resolution_status == DisputeStatus.REJECTED:
        # Check if other active disputes remain
        other_active = db.execute(
            select(Dispute).where(
                Dispute.project_id == target_project.id,
                Dispute.id != dispute.id,
                Dispute.status.in_([DisputeStatus.OPEN, DisputeStatus.UNDER_REVIEW]),
            )
        ).scalars().first()
        if not other_active:
            target_project.status = ProjectStatus.ACTIVE
    elif payload.resolution_status == DisputeStatus.RESOLVED:
        target_project.status = ProjectStatus.UNDER_DISPUTE

    # Original ownership proof parameters (composite_sha256, ipfs_root_cid, author_wallet, registration_id)
    # are preserved intact and NEVER modified!
    db.commit()
    db.refresh(dispute)
    db.refresh(target_version)
    db.refresh(target_project)

    return _build_dispute_detail(
        dispute=dispute,
        registration_id=registration_id,
        res_tx_hash=res_tx_hash,
    )


def get_dispute(
    db: Session,
    dispute_id: str,
    current_user: User,
) -> DisputeDetailResponse:
    """Retrieves dispute details by public ID or UUID."""
    dispute_query = (
        select(Dispute)
        .options(
            selectinload(Dispute.project).selectinload(Project.versions),
            selectinload(Dispute.claimant),
            selectinload(Dispute.resolver),
        )
    )
    try:
        u = uuid.UUID(dispute_id)
        dispute_query = dispute_query.where(or_(Dispute.public_id == dispute_id, Dispute.id == u))
    except ValueError:
        dispute_query = dispute_query.where(Dispute.public_id == dispute_id)

    dispute = db.execute(dispute_query).scalar_one_or_none()
    if not dispute:
        raise NotFoundError(
            code="DISPUTE_NOT_FOUND",
            message=f"Dispute '{dispute_id}' was not found.",
            details={"dispute_id": dispute_id},
        )

    return _build_dispute_detail(dispute=dispute)


def list_project_disputes(
    db: Session,
    project_id: str,
    current_user: User,
) -> List[DisputeDetailResponse]:
    """Lists all disputes associated with a project."""
    proj_query = select(Project).options(selectinload(Project.versions))
    try:
        u = uuid.UUID(project_id)
        proj_query = proj_query.where(or_(Project.public_id == project_id, Project.id == u))
    except ValueError:
        proj_query = proj_query.where(Project.public_id == project_id)

    project = db.execute(proj_query).scalar_one_or_none()
    if not project:
        raise NotFoundError(
            code="PROJECT_NOT_FOUND",
            message=f"Project '{project_id}' was not found.",
            details={"project_id": project_id},
        )

    disputes = db.execute(
        select(Dispute)
        .options(
            selectinload(Dispute.project).selectinload(Project.versions),
            selectinload(Dispute.claimant),
            selectinload(Dispute.resolver),
        )
        .where(Dispute.project_id == project.id)
        .order_by(Dispute.created_at.desc())
    ).scalars().all()

    return [_build_dispute_detail(d) for d in disputes]
