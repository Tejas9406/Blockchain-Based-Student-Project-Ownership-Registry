from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.models.enums import ArtifactCategory, UserRole
from app.models.user import User
from app.schemas.common import ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.artifact import ArtifactResponse
from app.services.artifact_service import ingest_artifact

router = APIRouter(prefix="/artifacts", tags=["Artifacts & Storage"])


@router.post(
    "/upload",
    response_model=ApiResponse[ArtifactResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Ingest Project Artifact",
    description="Uploads a project artifact file, calculates its deterministic SHA-256 digest via streaming, validates maximum size (50 MB), enforces ownership, and indexes metadata.",
    responses={
        201: {"description": "Artifact uploaded and hashed successfully"},
        401: {"description": "Authentication credentials missing or invalid"},
        403: {"description": "Caller lacks permission to upload to this project"},
        404: {"description": "Specified project or version not found"},
        422: {"description": "Validation error (file oversized, empty, invalid format, or version mismatch)"},
    },
)
async def upload_artifact(
    request: Request,
    file: UploadFile = File(..., description="Multipart file stream (max 50 MB)"),
    artifact_category: ArtifactCategory = Form(
        ArtifactCategory.OTHER,
        description="Category classification: SOURCE_CODE, DOCUMENTATION, DESIGN_SPEC, PRESENTATION, OTHER",
    ),
    project_id: Optional[str] = Form(
        None,
        description="Public project identifier (PRJ-...) or slug to associate with",
    ),
    version_id: Optional[str] = Form(
        None,
        description="Public version identifier (VER-...) to associate with",
    ),
    project_id_query: Optional[str] = Query(None, alias="project_id", include_in_schema=False),
    version_id_query: Optional[str] = Query(None, alias="version_id", include_in_schema=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT, UserRole.FACULTY, UserRole.ADMIN)),
) -> ApiResponse[ArtifactResponse]:
    """
    Accepts multipart/form-data upload:
    - Streams file without loading entire file into memory
    - Incremental SHA-256 calculation
    - Enforces 50 MB ceiling
    - Rejects 0-byte files
    - Validates caller authorization and project association
    - Persists metadata under ART-... public identifier
    """
    effective_project_id = project_id or project_id_query
    effective_version_id = version_id or version_id_query

    artifact_data = await ingest_artifact(
        db=db,
        file=file,
        artifact_category=artifact_category,
        current_user=current_user,
        project_id=effective_project_id,
        version_id=effective_version_id,
    )

    request_id = getattr(request.state, "request_id", None)
    return ApiResponse(
        success=True,
        data=artifact_data,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )
