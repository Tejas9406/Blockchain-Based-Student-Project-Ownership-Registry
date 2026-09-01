import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.enums import ProjectMemberRole, ProjectVisibility, UserRole
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project_member import ProjectMemberCreateRequest, ProjectMemberItem
from app.schemas.user import UserProfileResponse


def format_project_member_item(member: ProjectMember) -> ProjectMemberItem:
    """
    Formats a ProjectMember ORM model into the public ProjectMemberItem schema.
    Strictly excludes internal UUIDs, password hashes, and sensitive fields.
    """
    user = member.user
    user_profile = UserProfileResponse(
        public_id=user.public_id,
        email=user.email,
        full_name=user.full_name,
        institution_id=user.institution_id,
        institution_name=user.institution_name,
        department=user.department,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        wallet_address=user.wallet_address,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )
    return ProjectMemberItem(
        user=user_profile,
        role_in_project=member.role_in_project,
        contribution_percentage=float(member.contribution_percentage) if member.contribution_percentage is not None else 0.0,
        is_owner=member.is_owner,
        joined_at=member.joined_at,
    )


def _resolve_project(
    db: Session,
    project_identifier: str,
) -> Project:
    """
    Resolves a project by public_id, slug, or internal UUID.
    """
    stmt = (
        select(Project)
        .options(
            selectinload(Project.members).selectinload(ProjectMember.user)
        )
    )

    if project_identifier.startswith("PRJ-"):
        stmt = stmt.where(Project.public_id == project_identifier.strip())
    else:
        try:
            parsed_uuid = uuid.UUID(project_identifier.strip())
            stmt = stmt.where(
                (Project.public_id == project_identifier.strip())
                | (Project.slug == project_identifier.strip())
                | (Project.id == parsed_uuid)
            )
        except ValueError:
            stmt = stmt.where(
                (Project.public_id == project_identifier.strip())
                | (Project.slug == project_identifier.strip())
            )

    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise NotFoundException(
            code="PROJECT_NOT_FOUND",
            message=f"Project '{project_identifier}' does not exist."
        )
    return project


def _check_project_read_access(
    project: Project,
    current_user: Optional[User],
) -> None:
    """
    Validates that the caller has permission to view project member details.
    """
    if project.visibility == ProjectVisibility.PUBLIC:
        return

    if not current_user:
        raise NotFoundException(
            code="PROJECT_NOT_FOUND",
            message="The requested project does not exist."
        )

    if current_user.role == UserRole.ADMIN:
        return

    if project.visibility == ProjectVisibility.INSTITUTIONAL:
        return

    if project.visibility == ProjectVisibility.PRIVATE:
        is_member = any(m.user_id == current_user.id for m in project.members)
        if not is_member:
            raise NotFoundException(
                code="PROJECT_NOT_FOUND",
                message="The requested project does not exist."
            )


def list_project_members(
    db: Session,
    project_identifier: str,
    current_user: Optional[User] = None,
) -> List[ProjectMemberItem]:
    """
    Retrieves all members for a project according to API_CONTRACT.md Section 6.1.
    Respects visibility access rules.
    """
    project = _resolve_project(db, project_identifier)
    _check_project_read_access(project, current_user)

    stmt = (
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(ProjectMember.project_id == project.id)
        .order_by(ProjectMember.is_owner.desc(), ProjectMember.joined_at.asc())
    )

    members = db.execute(stmt).scalars().all()
    return [format_project_member_item(m) for m in members]


def add_project_member(
    db: Session,
    project_identifier: str,
    current_user: User,
    request: ProjectMemberCreateRequest,
) -> ProjectMemberItem:
    """
    Adds/invites a new member to an existing project according to API_CONTRACT.md Section 6.2.
    Enforces that only the project owner/lead (or system admin) can add members.
    Enforces duplicate membership prevention and preserves primary ownership integrity.
    """
    project = _resolve_project(db, project_identifier)

    # 1. Authorization: Only the Project Lead/Owner (or Admin) can manage members
    is_owner_or_lead = False
    if current_user.role == UserRole.ADMIN:
        is_owner_or_lead = True
    else:
        for m in project.members:
            if m.user_id == current_user.id and (m.is_owner or m.role_in_project == ProjectMemberRole.LEAD):
                is_owner_or_lead = True
                break

    if not is_owner_or_lead:
        raise ForbiddenException(
            code="FORBIDDEN",
            message="Only the project lead or owner is authorized to add team members."
        )

    # 2. Resolve target user to add
    target_user: Optional[User] = None
    if request.user_public_id:
        target_user = db.execute(
            select(User).where(User.public_id == request.user_public_id.strip())
        ).scalar_one_or_none()
    elif request.email:
        target_user = db.execute(
            select(User).where(User.email == request.email.lower().strip())
        ).scalar_one_or_none()

    if not target_user:
        raise NotFoundException(
            code="USER_NOT_FOUND",
            message="The specified user does not exist."
        )

    if not target_user.is_active:
        raise ValidationException(
            code="USER_INACTIVE",
            message="Cannot add an inactive user account to a project."
        )

    # 3. Check for existing membership (prevent duplicate)
    existing_member = db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == target_user.id,
        )
    ).scalar_one_or_none()

    if existing_member:
        raise ConflictException(
            code="MEMBER_ALREADY_EXISTS",
            message=f"User '{target_user.full_name}' is already a member of this project."
        )

    # 4. Create new ProjectMember record
    # Note: Ownership is preserved; normal member addition always sets is_owner=False
    role_to_assign = request.role_in_project or ProjectMemberRole.CONTRIBUTOR
    contribution_to_assign = request.contribution_percentage if request.contribution_percentage is not None else Decimal("0.00")

    new_member = ProjectMember(
        project_id=project.id,
        user_id=target_user.id,
        role_in_project=role_to_assign,
        contribution_percentage=contribution_to_assign,
        is_owner=False,
        invited_at=datetime.now(timezone.utc),
        joined_at=datetime.now(timezone.utc),
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    # Load relationship for serialization
    new_member.user = target_user

    return format_project_member_item(new_member)
