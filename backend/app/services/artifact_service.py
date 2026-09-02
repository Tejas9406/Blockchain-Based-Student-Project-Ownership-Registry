import hashlib
import os
import re
import uuid
from typing import Optional
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    ForbiddenException,
    NotFoundError,
    ValidationException,
)
from app.models.artifact import Artifact
from app.models.enums import ArtifactCategory, ProjectMemberRole, UserRole
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.schemas.artifact import ArtifactResponse
from app.storage.service import StorageService, get_storage_service
from app.utils.identifiers import generate_artifact_public_id

# Contract constants
MAX_ARTIFACT_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
STREAM_CHUNK_SIZE: int = 64 * 1024  # 64 KB chunk size for memory-safe streaming


def sanitize_filename(filename: Optional[str]) -> str:
    """
    Sanitizes untrusted filenames to prevent directory traversal and filesystem attacks.
    Removes path separators, null bytes, and traversal sequences.
    """
    if not filename:
        raise ValidationException(
            code="INVALID_FILENAME",
            message="Filename must not be empty.",
            details={"field": "file"},
        )

    # Remove null bytes
    cleaned = filename.replace("\x00", "")

    # Strip directory paths (both forward and backward slashes)
    cleaned = cleaned.replace("\\", "/")
    cleaned = os.path.basename(cleaned)

    # Strip leading/trailing whitespaces and dots
    cleaned = cleaned.strip(" .")

    if not cleaned:
        raise ValidationException(
            code="INVALID_FILENAME",
            message="Filename is invalid or empty after sanitization.",
            details={"field": "file", "original": filename},
        )

    return cleaned


def _resolve_project(db: Session, project_identifier: str) -> Project:
    """
    Resolves project by public_id (PRJ-...), slug, or internal UUID.
    """
    query = select(Project).where(
        (Project.public_id == project_identifier) | (Project.slug == project_identifier)
    )
    try:
        val_uuid = uuid.UUID(project_identifier)
        query = select(Project).where(
            (Project.public_id == project_identifier)
            | (Project.slug == project_identifier)
            | (Project.id == val_uuid)
        )
    except ValueError:
        pass

    project = db.execute(query).scalar_one_or_none()
    if not project:
        raise NotFoundError(
            code="PROJECT_NOT_FOUND",
            message=f"Project '{project_identifier}' does not exist.",
            details={"field": "project_id", "value": project_identifier},
        )
    return project


def _resolve_version(db: Session, version_identifier: str) -> ProjectVersion:
    """
    Resolves project version by public_id (VER-...) or internal UUID.
    """
    query = select(ProjectVersion).where(ProjectVersion.public_id == version_identifier)
    try:
        val_uuid = uuid.UUID(version_identifier)
        query = select(ProjectVersion).where(
            (ProjectVersion.public_id == version_identifier) | (ProjectVersion.id == val_uuid)
        )
    except ValueError:
        pass

    version = db.execute(query).scalar_one_or_none()
    if not version:
        raise NotFoundError(
            code="VERSION_NOT_FOUND",
            message=f"Project version '{version_identifier}' does not exist.",
            details={"field": "version_id", "value": version_identifier},
        )
    return version


def _check_user_project_access(db: Session, project: Project, user: User) -> None:
    """
    Validates that the authenticated user has permission to upload artifacts to the project.
    Allowed: Project Owner (is_owner=True), Active Project Members (LEAD, CONTRIBUTOR, FACULTY_MENTOR), ADMIN.
    """
    if user.role == UserRole.ADMIN:
        return

    membership = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
        )
    ).scalar_one_or_none()

    if membership and (
        membership.is_owner
        or membership.role_in_project
        in {
            ProjectMemberRole.LEAD,
            ProjectMemberRole.CONTRIBUTOR,
            ProjectMemberRole.FACULTY_MENTOR,
        }
    ):
        return

    raise ForbiddenException(
        code="FORBIDDEN",
        message="You do not have permission to upload artifacts to this project.",
        details={"project_id": project.public_id, "user_id": user.public_id},
    )


async def ingest_artifact(
    db: Session,
    file: UploadFile,
    artifact_category: ArtifactCategory,
    current_user: User,
    project_id: Optional[str] = None,
    version_id: Optional[str] = None,
    storage_service: Optional[StorageService] = None,
) -> ArtifactResponse:
    """
    Processes multipart artifact upload:
    - Validates project and version relationships and ownership
    - Generates server-side public identifier and safe storage key
    - Memory-safe streaming SHA-256 calculation in 64 KB chunks
    - Simultaneously persists chunks through StorageService
    - Strict 50 MB file size limit enforcement during streaming
    - Automatic cleanup of stored content on any failure (transactional rollback)
    - Rejection of 0-byte empty files
    - Persistent database record creation with initial null IPFS CID
    """
    storage = storage_service or get_storage_service()

    # 1. Project & Version Association and Authorization
    resolved_version: Optional[ProjectVersion] = None
    resolved_project: Optional[Project] = None

    if project_id:
        resolved_project = _resolve_project(db, project_id)
        _check_user_project_access(db, resolved_project, current_user)

    if version_id:
        resolved_version = _resolve_version(db, version_id)
        # Check cross-project consistency if project_id was also specified
        if resolved_project and resolved_version.project_id != resolved_project.id:
            raise ValidationException(
                code="CROSS_PROJECT_VERSION_MISMATCH",
                message=f"Project version '{version_id}' does not belong to project '{project_id}'.",
                details={"project_id": project_id, "version_id": version_id},
            )
        # Check access on version's project if project_id was not explicitly specified
        if not resolved_project:
            _check_user_project_access(db, resolved_version.project, current_user)

    # 2. Filename Sanitization
    sanitized_filename = sanitize_filename(file.filename)
    content_type = file.content_type or "application/octet-stream"

    # 3. Generate Unique Public Identifier (ART-YYYYMM-XXXXX) & Storage Key
    public_id = None
    for _ in range(5):
        candidate_id = generate_artifact_public_id()
        existing = db.execute(
            select(Artifact).where(Artifact.public_id == candidate_id)
        ).scalar_one_or_none()
        if not existing:
            public_id = candidate_id
            break

    if not public_id:
        raise ConflictError(
            code="ARTIFACT_ID_COLLISION",
            message="Failed to generate a unique public artifact identifier. Please retry.",
        )

    # Standardized storage key: ART-YYYYMM-XXXXX/content
    storage_key = f"{public_id}/content"

    # 4. Incremental Streaming SHA-256 Hashing & Storage Persistence
    sha256_hasher = hashlib.sha256()
    total_bytes_read = 0
    is_first_chunk = True

    try:
        while True:
            chunk = await file.read(STREAM_CHUNK_SIZE)
            if not chunk:
                break
            total_bytes_read += len(chunk)
            if total_bytes_read > MAX_ARTIFACT_SIZE_BYTES:
                await storage.delete(storage_key)
                raise ValidationException(
                    code="FILE_TOO_LARGE",
                    message=f"Artifact exceeds maximum allowed size of 50 MB ({MAX_ARTIFACT_SIZE_BYTES} bytes).",
                    details={
                        "max_allowed_bytes": MAX_ARTIFACT_SIZE_BYTES,
                        "bytes_read": total_bytes_read,
                    },
                )
            sha256_hasher.update(chunk)
            await storage.write_chunk(storage_key, chunk, is_first_chunk=is_first_chunk)
            is_first_chunk = False

        if total_bytes_read == 0:
            await storage.delete(storage_key)
            raise ValidationException(
                code="EMPTY_FILE_NOT_ALLOWED",
                message="Uploaded artifact file cannot be empty (0 bytes).",
                details={"file_size_bytes": 0},
            )

        calculated_hash = sha256_hasher.hexdigest().lower()

        # 5. Persist Database Record (Transactional)
        try:
            artifact = Artifact(
                public_id=public_id,
                version_id=resolved_version.id if resolved_version else None,
                file_name=sanitized_filename,
                file_type=content_type,
                file_size_bytes=total_bytes_read,
                sha256_hash=calculated_hash,
                ipfs_cid=None,  # Nullable/pending until external IPFS integration
                artifact_category=artifact_category,
            )
            db.add(artifact)
            db.commit()
            db.refresh(artifact)
        except Exception:
            db.rollback()
            await storage.delete(storage_key)
            raise

        return ArtifactResponse.model_validate(artifact)

    except Exception:
        # Guarantee cleanup of stored bytes on any unhandled error during upload
        await storage.delete(storage_key)
        raise


async def get_artifact_content(
    public_id: str, storage_service: Optional[StorageService] = None
) -> bytes:
    """
    Retrieves stored artifact bytes for a given public artifact ID.
    Used by Developer 3 for IPFS pinning in Phase 5.
    """
    storage = storage_service or get_storage_service()
    storage_key = f"{public_id}/content"
    return await storage.retrieve(storage_key)
