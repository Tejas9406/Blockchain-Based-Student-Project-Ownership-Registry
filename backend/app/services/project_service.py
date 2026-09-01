from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import distinct, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    AppException,
    ConflictException,
    ForbiddenException,
    NotFoundError,
)
from app.core.logging import logger
from app.models.enums import (
    ProjectMemberRole,
    ProjectStatus,
    ProjectVersionStage,
    ProjectVisibility,
    UserRole,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectOwnerSummary,
    ProjectSummary,
)
from app.utils.identifiers import generate_project_public_id
from app.utils.slug import generate_unique_slug
from app.utils.time import format_iso_utc


def get_project_owner_summary(project: Project) -> ProjectOwnerSummary:
    """
    Extracts the public owner summary from project member associations.
    """
    for member in project.members:
        if member.is_owner and member.user:
            return ProjectOwnerSummary(
                public_id=member.user.public_id,
                full_name=member.user.full_name,
            )
        
    for member in project.members:
        if member.role_in_project == ProjectMemberRole.LEAD and member.user:
            return ProjectOwnerSummary(
                public_id=member.user.public_id,
                full_name=member.user.full_name,
            )

    # Fallback if no explicit owner found in relationship
    return ProjectOwnerSummary(
        public_id="UNKNOWN",
        full_name="Unknown Owner",
    )


def format_project_summary(project: Project) -> ProjectSummary:
    """
    Transforms a Project ORM instance into the standardized ProjectSummary schema.
    """
    owner = get_project_owner_summary(project)
    return ProjectSummary(
        public_id=project.public_id,
        slug=project.slug,
        title=project.title,
        abstract=project.abstract,
        category=project.category,
        department=project.department,
        academic_year=project.academic_year,
        current_lifecycle_stage=project.current_lifecycle_stage,
        visibility=project.visibility,
        status=project.status,
        owner=owner,
        created_at=project.created_at,
    )


def create_project(
    db: Session,
    creator: User,
    request: ProjectCreateRequest,
) -> ProjectSummary:
    """
    Creates a new project record and registers the authenticated creator as the LEAD owner.
    
    1. Validates creator permissions (STUDENT, FACULTY, or ADMIN).
    2. Generates unique PRJ-YYYYMM-XXXXX public identifier.
    3. Generates unique URL-safe slug from title.
    4. Persists Project entity and ProjectMember association.
    5. Safely commits transaction.
    """
    # Enforce role restriction per API contract (STUDENT, FACULTY, or ADMIN)
    allowed_creator_roles = {UserRole.STUDENT, UserRole.FACULTY, UserRole.ADMIN}
    if creator.role not in allowed_creator_roles:
        logger.warning(
            f"Project creation denied: User '{creator.public_id}' with role '{creator.role}' is not authorized."
        )
        raise ForbiddenException(
            code="FORBIDDEN",
            message="Only students and faculty members are permitted to create new projects.",
        )

    # Generate collision-free public_id
    public_id = None
    for _ in range(5):
        candidate_pid = generate_project_public_id()
        existing = db.execute(
            select(Project.id).where(Project.public_id == candidate_pid)
        ).scalar_one_or_none()
        if not existing:
            public_id = candidate_pid
            break

    if not public_id:
        raise AppException(
            message="Failed to generate a unique project identifier. Please try again.",
            code="ID_GENERATION_FAILED",
            status_code=500,
        )

    # Generate collision-free slug from project title
    slug = generate_unique_slug(db=db, title=request.title)

    try:
        new_project = Project(
            public_id=public_id,
            slug=slug,
            title=request.title.strip(),
            abstract=request.abstract,
            category=request.category.strip(),
            department=request.department.strip(),
            academic_year=request.academic_year.strip(),
            current_lifecycle_stage=ProjectVersionStage.IDEA,
            visibility=request.visibility or ProjectVisibility.PUBLIC,
            status=ProjectStatus.ACTIVE,
        )
        db.add(new_project)
        db.flush()  # Allocate new_project.id for foreign key assignment

        # Associate creator as LEAD owner in project_members
        membership = ProjectMember(
            project_id=new_project.id,
            user_id=creator.id,
            role_in_project=ProjectMemberRole.LEAD,
            is_owner=True,
            contribution_percentage=Decimal("100.00"),
        )
        db.add(membership)
        db.commit()

        # Eager load relationships for clean serialization
        created_project = db.execute(
            select(Project)
            .options(
                selectinload(Project.members).selectinload(ProjectMember.user)
            )
            .where(Project.id == new_project.id)
        ).scalar_one()

        logger.info(
            f"Project created successfully: [ID: {created_project.public_id}, Slug: {created_project.slug}, Creator: {creator.public_id}]"
        )
        return format_project_summary(created_project)

    except IntegrityError as exc:
        db.rollback()
        logger.error(f"IntegrityError while creating project: {str(exc)}")
        raise ConflictException(
            code="PROJECT_CREATION_CONFLICT",
            message="A project with these unique attributes already exists.",
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"Unexpected database error during project creation: {str(exc)}", exc_info=True)
        raise AppException(
            status_code=500,
            code="DATABASE_ERROR",
            message="An unexpected database error occurred during project creation.",
        )


def list_projects(
    db: Session,
    current_user: Optional[User] = None,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    department: Optional[str] = None,
    lifecycle_stage: Optional[ProjectVersionStage] = None,
    search: Optional[str] = None,
) -> Tuple[List[ProjectSummary], int]:
    """
    Retrieves a paginated catalog of projects with optional category/department/search filters.
    Respects project visibility constraints based on authentication context.
    """
    filters = []

    # 1. Apply visibility filters
    if not current_user:
        # Unauthenticated users only see PUBLIC projects
        filters.append(Project.visibility == ProjectVisibility.PUBLIC)
    elif current_user.role == UserRole.ADMIN:
        # Admins can view all projects across all visibilities
        pass
    else:
        # Authenticated users see PUBLIC, INSTITUTIONAL, and PRIVATE projects they belong to
        filters.append(
            or_(
                Project.visibility == ProjectVisibility.PUBLIC,
                Project.visibility == ProjectVisibility.INSTITUTIONAL,
                (Project.visibility == ProjectVisibility.PRIVATE)
                & Project.members.any(ProjectMember.user_id == current_user.id),
            )
        )

    # 2. Filter by category
    if category:
        filters.append(Project.category.ilike(category.strip()))

    # 3. Filter by department
    if department:
        filters.append(Project.department.ilike(department.strip()))

    # 4. Filter by lifecycle stage
    if lifecycle_stage:
        filters.append(Project.current_lifecycle_stage == lifecycle_stage)

    # 5. Full-text / substring search across title and abstract
    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                Project.title.ilike(search_pattern),
                Project.abstract.ilike(search_pattern),
            )
        )

    # Count total matching records
    count_query = select(func.count(distinct(Project.id)))
    if filters:
        count_query = count_query.where(*filters)
    total_items = db.execute(count_query).scalar() or 0

    # Paginate and order by newest first
    offset = (page - 1) * page_size
    base_query = (
        select(Project)
        .options(
            selectinload(Project.members).selectinload(ProjectMember.user)
        )
    )
    if filters:
        base_query = base_query.where(*filters)

    query = base_query.order_by(Project.created_at.desc()).offset(offset).limit(page_size)
    projects = db.execute(query).scalars().all()

    formatted_items = [format_project_summary(p) for p in projects]
    return formatted_items, total_items



def get_project_by_identifier(
    db: Session,
    project_identifier: str,
    current_user: Optional[User] = None,
) -> ProjectSummary:
    """
    Retrieves project details by public project ID (PRJ-YYYYMM-XXXXX) or slug.
    Enforces visibility access control.
    """
    clean_identifier = project_identifier.strip()

    query = (
        select(Project)
        .options(
            selectinload(Project.members).selectinload(ProjectMember.user)
        )
        .where(
            or_(
                Project.public_id == clean_identifier,
                Project.slug == clean_identifier.lower(),
            )
        )
    )

    project = db.execute(query).scalar_one_or_none()

    if not project:
        raise NotFoundError(
            code="PROJECT_NOT_FOUND",
            message=f"The requested project '{project_identifier}' does not exist.",
            details={"field": "project_identifier", "value": project_identifier},
        )

    # Visibility checks
    if project.visibility == ProjectVisibility.PUBLIC:
        return format_project_summary(project)

    if project.visibility == ProjectVisibility.INSTITUTIONAL:
        if not current_user:
            raise NotFoundError(
                code="PROJECT_NOT_FOUND",
                message=f"The requested project '{project_identifier}' does not exist.",
                details={"field": "project_identifier", "value": project_identifier},
            )
        return format_project_summary(project)

    if project.visibility == ProjectVisibility.PRIVATE:
        if current_user:
            if current_user.role == UserRole.ADMIN:
                return format_project_summary(project)
            is_member = any(m.user_id == current_user.id for m in project.members)
            if is_member:
                return format_project_summary(project)

        # Mask existence of private project to unauthorized users
        raise NotFoundError(
            code="PROJECT_NOT_FOUND",
            message=f"The requested project '{project_identifier}' does not exist.",
            details={"field": "project_identifier", "value": project_identifier},
        )

    return format_project_summary(project)
