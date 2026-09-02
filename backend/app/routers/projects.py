from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_current_user, require_role
from app.database.session import get_db
from app.models.enums import ProjectVersionStage, UserRole
from app.models.user import User
from app.schemas.common import ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.error import ApiErrorResponse
from app.schemas.pagination import ApiPaginatedResponse, PaginatedMeta
from app.schemas.project import ProjectCreateRequest, ProjectSummary
from app.schemas.project_member import ProjectMemberCreateRequest, ProjectMemberItem
from app.schemas.project_version import ProjectVersionCreateRequest, ProjectVersionDetail
from app.services.project_member_service import (
    add_project_member,
    list_project_members,
)
from app.services.project_service import (
    create_project,
    get_project_by_identifier,
    list_projects,
)
from app.services.project_version_service import (
    create_project_version,
    list_project_versions,
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


@router.get(
    "/{project_id}/members",
    response_model=ApiResponse[List[ProjectMemberItem]],
    status_code=status.HTTP_200_OK,
    summary="List Project Members",
    description="Retrieves the list of team members, mentors, and the project lead for the specified project.",
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[List[ProjectMemberItem]],
            "description": "Project members retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "The requested project identifier does not exist.",
        },
    },
)
def get_project_members(
    request: Request,
    project_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ProjectMemberItem]]:
    members = list_project_members(
        db=db,
        project_identifier=project_id,
        current_user=current_user,
    )
    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=members,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )


@router.post(
    "/{project_id}/members",
    response_model=ApiResponse[ProjectMemberItem],
    status_code=status.HTTP_201_CREATED,
    summary="Add Project Team Member",
    description="Adds or invites a registered student contributor or faculty mentor to the project team. Requires project owner/lead permissions.",
    responses={
        status.HTTP_201_CREATED: {
            "model": ApiResponse[ProjectMemberItem],
            "description": "Project member successfully added.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Authentication credentials missing or invalid.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ApiErrorResponse,
            "description": "Caller is not authorized to manage project members.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Project or target user not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": "User is already a member of this project.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ApiErrorResponse,
            "description": "Validation failure in request payload.",
        },
    },
)
def add_member_to_project(
    request: Request,
    project_id: str,
    payload: ProjectMemberCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjectMemberItem]:
    member = add_project_member(
        db=db,
        project_identifier=project_id,
        current_user=current_user,
        request=payload,
    )
    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=member,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )


@router.post(
    "/{project_id}/versions",
    response_model=ApiResponse[ProjectVersionDetail],
    status_code=status.HTTP_201_CREATED,
    summary="Create Project Version Milestone",
    description="Creates an immutable milestone version snapshot for a student project. Requires project lead or owner permissions.",
    responses={
        status.HTTP_201_CREATED: {
            "model": ApiResponse[ProjectVersionDetail],
            "description": "Milestone version successfully created and queued for anchoring.",
        },
        status.HTTP_200_OK: {
            "model": ApiResponse[ProjectVersionDetail],
            "description": "Idempotent request; returning existing version snapshot.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Authentication credentials missing or invalid.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ApiErrorResponse,
            "description": "Caller is not authorized to create versions for this project.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Project or referenced artifact not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": "Duplicate version or identifier collision.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ApiErrorResponse,
            "description": "Invalid payload or prohibited lifecycle transition.",
        },
    },
)
async def create_version_for_project(
    request: Request,
    response: Response,
    project_id: str,
    payload: ProjectVersionCreateRequest,
    idempotency_key: Annotated[
        Optional[str],
        Header(alias="Idempotency-Key", description="Optional unique client deduplication key"),
    ] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjectVersionDetail]:
    version, is_created = await create_project_version(
        db=db,
        project_identifier=project_id,
        creator=current_user,
        request=payload,
        idempotency_key=idempotency_key,
    )
    if is_created:
        response.status_code = status.HTTP_201_CREATED

    else:
        response.status_code = status.HTTP_200_OK

    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=version,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )


@router.get(
    "/{project_id}/versions",
    response_model=ApiResponse[List[ProjectVersionDetail]],
    status_code=status.HTTP_200_OK,
    summary="List Project Versions",
    description="Retrieves all immutable milestone snapshots for a project in sequential ascending order.",
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[List[ProjectVersionDetail]],
            "description": "Project versions retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "The requested project identifier does not exist.",
        },
    },
)
def list_versions_for_project(
    request: Request,
    project_id: str,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ProjectVersionDetail]]:
    versions = list_project_versions(
        db=db,
        project_identifier=project_id,
        current_user=current_user,
    )
    request_id = getattr(request.state, "request_id", None)

    return ApiResponse(
        success=True,
        data=versions,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=request_id,
        ),
    )
