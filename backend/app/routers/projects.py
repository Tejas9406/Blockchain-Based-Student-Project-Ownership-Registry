from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_optional_current_user, require_role
from app.database.session import get_db
from app.models.enums import ProjectVersionStage, UserRole
from app.models.user import User
from app.schemas.common import ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.error import ApiErrorResponse
from app.schemas.pagination import ApiPaginatedResponse, PaginatedMeta
from app.schemas.project import ProjectCreateRequest, ProjectSummary
from app.services.project_service import (
    create_project,
    get_project_by_identifier,
    list_projects,
)

router = APIRouter(prefix="/projects", tags=["Projects & Milestones"])


@router.post(
    "",
    response_model=ApiResponse[ProjectSummary],
    status_code=status.HTTP_201_CREATED,
    summary="Create New Project",
    description="Creates a new student project, generates a unique public identifier and URL slug, and assigns the authenticated user as the project owner.",
    responses={
        status.HTTP_201_CREATED: {
            "model": ApiResponse[ProjectSummary],
            "description": "Project successfully created.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Authentication credentials missing or invalid.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ApiErrorResponse,
            "description": "Role is not authorized to create projects.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": "Conflict generating unique identifiers.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ApiErrorResponse,
            "description": "Validation failure in request payload.",
        },
    },
)
def create_new_project(
    request: Request,
    payload: ProjectCreateRequest,
    current_user: User = Depends(require_role(UserRole.STUDENT, UserRole.FACULTY, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjectSummary]:
    project = create_project(db=db, creator=current_user, request=payload)
    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=project,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )


@router.get(
    "",
    response_model=ApiPaginatedResponse[ProjectSummary],
    status_code=status.HTTP_200_OK,
    summary="List Projects",
    description="Retrieves a paginated catalog of projects with optional category, department, lifecycle stage, and keyword search filters.",
    responses={
        status.HTTP_200_OK: {
            "model": ApiPaginatedResponse[ProjectSummary],
            "description": "Paginated list of projects retrieved successfully.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ApiErrorResponse,
            "description": "Invalid query parameters.",
        },
    },
)
def list_all_projects(
    request: Request,
    page: Annotated[int, Query(ge=1, description="Page number (1-based index)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page (max 100)")] = 20,
    category: Annotated[Optional[str], Query(description="Filter by domain category (e.g. AI, WEB3)")] = None,
    department: Annotated[Optional[str], Query(description="Filter by department")] = None,
    lifecycle_stage: Annotated[Optional[ProjectVersionStage], Query(description="Filter by milestone stage")] = None,
    search: Annotated[Optional[str], Query(description="Search keywords across project title and abstract")] = None,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ApiPaginatedResponse[ProjectSummary]:
    projects, total_items = list_projects(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        category=category,
        department=department,
        lifecycle_stage=lifecycle_stage,
        search=search,
    )
    request_id = getattr(request.state, "request_id", None)

    meta = PaginatedMeta.create(
        page=page,
        page_size=page_size,
        total_items=total_items,
        request_id=request_id,
    )

    return ApiPaginatedResponse(
        success=True,
        data=projects,
        meta=meta,
    )


@router.get(
    "/{project_identifier}",
    response_model=ApiResponse[ProjectSummary],
    status_code=status.HTTP_200_OK,
    summary="Get Project Details",
    description="Retrieves project details by public project ID (PRJ-YYYYMM-XXXXX) or unique slug.",
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[ProjectSummary],
            "description": "Project details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "The requested project identifier does not exist.",
        },
    },
)
def get_project_details(
    request: Request,
    project_identifier: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjectSummary]:
    project = get_project_by_identifier(
        db=db,
        project_identifier=project_identifier,
        current_user=current_user,
    )
    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=project,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )
