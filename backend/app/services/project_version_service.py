import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundError,
    ValidationException,
)
from app.core.logging import logger
from app.models.artifact import Artifact
from app.models.enums import (
    AnchoringStatus,
    DisputeStatus,
    ProjectMemberRole,
    ProjectVersionStage,
    ProjectVisibility,
    UserRole,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.schemas.project_version import (
    ArtifactItemSummary,
    BlockchainProofSummary,
    ProjectVersionCreateRequest,
    ProjectVersionDetail,
)
from app.utils.identifiers import (
    generate_registration_id,
    generate_version_public_id,
)

STAGE_ORDER = [
    ProjectVersionStage.IDEA,
    ProjectVersionStage.DESIGN,
    ProjectVersionStage.PROTOTYPE,
    ProjectVersionStage.FINAL,
]


def format_version_detail(version: ProjectVersion) -> ProjectVersionDetail:
    """
    Formats a ProjectVersion ORM model into the standardized ProjectVersionDetail schema.
    Strictly excludes internal UUIDs, node private keys, and operational secrets.
    """
    blockchain_proof = None
    if version.blockchain_record:
        blockchain_proof = BlockchainProofSummary(
            transaction_hash=version.blockchain_record.transaction_hash,
            block_number=version.blockchain_record.block_number,
            network_name=version.blockchain_record.network_name,
            anchored_timestamp=version.blockchain_record.anchored_timestamp,
        )

    artifacts_list = []
    if version.artifacts:
        for a in version.artifacts:
            category_val = (
                a.artifact_category.value
                if hasattr(a.artifact_category, "value")
                else str(a.artifact_category)
            )
            artifacts_list.append(
                ArtifactItemSummary(
                    public_id=a.public_id,
                    file_name=a.file_name,
                    file_type=a.file_type,
                    file_size_bytes=a.file_size_bytes,
                    sha256_hash=a.sha256_hash,
                    ipfs_cid=a.ipfs_cid,
                    artifact_category=category_val,
                    uploaded_at=a.uploaded_at,
                )
            )

    return ProjectVersionDetail(
        public_id=version.public_id,
        registration_id=version.registration_id,
        version_index=version.version_index,
        version_tag=version.version_tag,
        lifecycle_stage=version.lifecycle_stage,
        title=version.title,
        description=version.description,
        composite_sha256=version.composite_sha256,
        ipfs_root_cid=version.ipfs_root_cid,
        anchoring_status=version.anchoring_status,
        dispute_status=version.dispute_status,
        blockchain_record=blockchain_proof,
        artifacts=artifacts_list,
        created_at=version.created_at,
    )


def _resolve_project(db: Session, project_identifier: str) -> Project:
    """
    Resolves a project by its public_id (PRJ-YYYYMM-XXXXX), vanity slug, or internal UUID.
    Eagerly loads project members and users for authorization.
    """
    clean_identifier = project_identifier.strip()
    stmt = (
        select(Project)
        .options(
            selectinload(Project.members).selectinload(ProjectMember.user)
        )
    )

    if clean_identifier.startswith("PRJ-"):
        stmt = stmt.where(Project.public_id == clean_identifier)
    else:
        try:
            parsed_uuid = uuid.UUID(clean_identifier)
            stmt = stmt.where(
                (Project.public_id == clean_identifier)
                | (Project.slug == clean_identifier.lower())
                | (Project.id == parsed_uuid)
            )
        except ValueError:
            stmt = stmt.where(
                (Project.public_id == clean_identifier)
                | (Project.slug == clean_identifier.lower())
            )

    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise NotFoundError(
            code="PROJECT_NOT_FOUND",
            message=f"The requested project '{project_identifier}' does not exist.",
            details={"field": "project_identifier", "value": project_identifier},
        )
    return project


def _check_version_create_auth(project: Project, current_user: User) -> None:
    """
    Validates that the authenticated caller has authorization to create a milestone version.
    Authorized: Platform ADMIN or Project Member with is_owner=True or role_in_project=LEAD.
    """
    if current_user.role == UserRole.ADMIN:
        return

    for m in project.members:
        if m.user_id == current_user.id and (m.is_owner or m.role_in_project == ProjectMemberRole.LEAD):
            return

    logger.warning(
        f"Version creation forbidden: User '{current_user.public_id}' is not an owner or lead of project '{project.public_id}'."
    )
    raise ForbiddenException(
        code="FORBIDDEN",
        message="Only the project lead or owner may create milestone versions.",
        details={"project_id": project.public_id, "user_id": current_user.public_id},
    )


def _check_version_read_access(project: Project, current_user: Optional[User]) -> None:
    """
    Validates visibility access control for listing project versions.
    """
    if project.visibility == ProjectVisibility.PUBLIC:
        return

    if not current_user:
        raise NotFoundError(
            code="PROJECT_NOT_FOUND",
            message=f"The requested project '{project.public_id}' does not exist.",
            details={"field": "project_identifier", "value": project.public_id},
        )

    if current_user.role == UserRole.ADMIN:
        return

    if project.visibility == ProjectVisibility.INSTITUTIONAL:
        return

    if project.visibility == ProjectVisibility.PRIVATE:
        is_member = any(m.user_id == current_user.id for m in project.members)
        if not is_member:
            raise NotFoundError(
                code="PROJECT_NOT_FOUND",
                message=f"The requested project '{project.public_id}' does not exist.",
                details={"field": "project_identifier", "value": project.public_id},
            )


def create_project_version(
    db: Session,
    project_identifier: str,
    creator: User,
    request: ProjectVersionCreateRequest,
    idempotency_key: Optional[str] = None,
) -> Tuple[ProjectVersionDetail, bool]:
    """
    Creates an immutable milestone snapshot (ProjectVersion) for a project.
    
    1. Resolves project and validates project existence.
    2. Checks idempotency: if an idempotency_key is provided and already exists, returns existing version (200 OK).
    3. Verifies creator authorization (Project Owner/Lead or Admin).
    4. Computes deterministic sequential version_index (1, 2, 3...).
    5. Validates lifecycle stage transition (no backward jumps; immutable after FINAL).
    6. Validates referenced artifacts (must exist and not belong to another project).
    7. Generates server-controlled REG-YYYY-XXXXX and VER-YYYYMM-XXXXX identifiers.
    8. Persists ProjectVersion in state PENDING.
    9. Returns (ProjectVersionDetail, is_created).
    """
    project = _resolve_project(db, project_identifier)

    # 1. Idempotency Check (DATABASE_DESIGN.md Section 6)
    clean_idempotency_key = idempotency_key.strip() if idempotency_key else None
    if clean_idempotency_key:
        existing_version = db.execute(
            select(ProjectVersion)
            .options(
                selectinload(ProjectVersion.artifacts),
                selectinload(ProjectVersion.blockchain_record),
            )
            .where(ProjectVersion.idempotency_key == clean_idempotency_key)
        ).scalar_one_or_none()

        if existing_version:
            if existing_version.project_id == project.id:
                logger.info(
                    f"Idempotent request intercepted for version '{existing_version.public_id}' with key '{clean_idempotency_key}'."
                )
                return format_version_detail(existing_version), False
            else:
                raise ConflictException(
                    code="IDEMPOTENCY_KEY_REUSED",
                    message="The provided Idempotency-Key has already been used for another project.",
                )

    # 2. Authorization Check
    _check_version_create_auth(project, creator)

    # 3. Compute Sequential Version Index
    max_index_stmt = select(
        func.coalesce(func.max(ProjectVersion.version_index), 0)
    ).where(ProjectVersion.project_id == project.id)
    current_max_index = db.execute(max_index_stmt).scalar() or 0
    next_version_index = current_max_index + 1

    # 4. Lifecycle Stage Transition Validation
    latest_version_stmt = (
        select(ProjectVersion)
        .where(ProjectVersion.project_id == project.id)
        .order_by(ProjectVersion.version_index.desc())
        .limit(1)
    )
    latest_version = db.execute(latest_version_stmt).scalar_one_or_none()

    if latest_version:
        if latest_version.lifecycle_stage == ProjectVersionStage.FINAL:
            raise ValidationException(
                code="FINAL_VERSION_IMMUTABLE",
                message="Project has already reached FINAL stage. Further versions cannot be added.",
                details={
                    "current_stage": latest_version.lifecycle_stage.value,
                    "requested_stage": request.lifecycle_stage.value,
                },
            )

        latest_stage_idx = STAGE_ORDER.index(latest_version.lifecycle_stage)
        requested_stage_idx = STAGE_ORDER.index(request.lifecycle_stage)

        if requested_stage_idx < latest_stage_idx:
            raise ValidationException(
                code="INVALID_LIFECYCLE_TRANSITION",
                message=(
                    f"Invalid lifecycle transition from '{latest_version.lifecycle_stage.value}' "
                    f"to '{request.lifecycle_stage.value}'. Backward transitions are prohibited."
                ),
                details={
                    "current_stage": latest_version.lifecycle_stage.value,
                    "requested_stage": request.lifecycle_stage.value,
                },
            )

    # 5. Validate Referenced Artifacts
    found_artifacts: List[Artifact] = []
    if request.artifact_ids:
        artifact_stmt = select(Artifact).where(Artifact.public_id.in_(request.artifact_ids))
        found_artifacts = list(db.execute(artifact_stmt).scalars().all())
        found_pids = {a.public_id for a in found_artifacts}

        for requested_id in request.artifact_ids:
            if requested_id not in found_pids:
                raise NotFoundError(
                    code="ARTIFACT_NOT_FOUND",
                    message=f"Referenced artifact '{requested_id}' does not exist.",
                    details={"field": "artifact_ids", "value": requested_id},
                )

        for a in found_artifacts:
            # If artifact was previously linked, ensure it does not belong to another project
            if a.version_id:
                other_ver = db.get(ProjectVersion, a.version_id)
                if other_ver and other_ver.project_id != project.id:
                    raise ValidationException(
                        code="INVALID_ARTIFACT_ASSOCIATION",
                        message=f"Artifact '{a.public_id}' is associated with another project.",
                        details={"artifact_id": a.public_id},
                    )

    # 6. Generate Unique Public and Registration Identifiers
    max_retries = 5
    new_public_id = None
    new_reg_id = None

    for _ in range(max_retries):
        candidate_public = generate_version_public_id()
        candidate_reg = generate_registration_id()

        existing_pid = db.execute(
            select(ProjectVersion.id).where(ProjectVersion.public_id == candidate_public)
        ).scalar_one_or_none()

        existing_reg = db.execute(
            select(ProjectVersion.id).where(ProjectVersion.registration_id == candidate_reg)
        ).scalar_one_or_none()

        if not existing_pid and not existing_reg:
            new_public_id = candidate_public
            new_reg_id = candidate_reg
            break

    if not new_public_id or not new_reg_id:
        raise ConflictException(
            code="IDENTIFIER_GENERATION_FAILED",
            message="Failed to generate unique identifiers for the version milestone.",
        )

    try:
        new_version = ProjectVersion(
            public_id=new_public_id,
            project_id=project.id,
            registration_id=new_reg_id,
            idempotency_key=clean_idempotency_key,
            version_index=next_version_index,
            version_tag=request.version_tag.strip(),
            lifecycle_stage=request.lifecycle_stage,
            title=request.title.strip(),
            description=request.description,
            composite_sha256=None,
            ipfs_root_cid=None,
            anchoring_status=AnchoringStatus.PENDING,
            dispute_status=DisputeStatus.NONE,
        )
        db.add(new_version)
        db.flush()

        # Update project's current lifecycle stage
        project.current_lifecycle_stage = request.lifecycle_stage

        # Associate artifacts with this new milestone
        for artifact in found_artifacts:
            artifact.version_id = new_version.id

        db.commit()

        # Eager load relationships for clean serialization
        created_version = db.execute(
            select(ProjectVersion)
            .options(
                selectinload(ProjectVersion.artifacts),
                selectinload(ProjectVersion.blockchain_record),
            )
            .where(ProjectVersion.id == new_version.id)
        ).scalar_one()

        logger.info(
            f"ProjectVersion created successfully: [ID: {created_version.public_id}, "
            f"RegID: {created_version.registration_id}, Project: {project.public_id}, "
            f"Index: {created_version.version_index}, Stage: {created_version.lifecycle_stage.value}]"
        )
        return format_version_detail(created_version), True

    except IntegrityError as exc:
        db.rollback()
        logger.error(f"IntegrityError while creating project version: {str(exc)}")
        raise ConflictException(
            code="PROJECT_VERSION_CONFLICT",
            message="A version with these unique attributes already exists for this project.",
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"Unexpected database error during version creation: {str(exc)}", exc_info=True)
        if isinstance(exc, AppException):
            raise
        raise AppException(
            status_code=500,
            code="DATABASE_ERROR",
            message="An unexpected database error occurred during version creation.",
        )


def list_project_versions(
    db: Session,
    project_identifier: str,
    current_user: Optional[User] = None,
) -> List[ProjectVersionDetail]:
    """
    Retrieves all milestone versions for a project in deterministic ascending order.
    Enforces project visibility rules.
    """
    project = _resolve_project(db, project_identifier)
    _check_version_read_access(project, current_user)

    stmt = (
        select(ProjectVersion)
        .options(
            selectinload(ProjectVersion.artifacts),
            selectinload(ProjectVersion.blockchain_record),
        )
        .where(ProjectVersion.project_id == project.id)
        .order_by(ProjectVersion.version_index.asc())
    )

    versions = db.execute(stmt).scalars().all()
    return [format_version_detail(v) for v in versions]
