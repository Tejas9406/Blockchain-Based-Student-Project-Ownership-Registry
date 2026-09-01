from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import ProjectMemberRole
from app.schemas.user import UserProfileResponse


class ProjectMemberCreateRequest(BaseModel):
    """
    Request schema for adding or inviting a member to a project.
    Conforms to API_CONTRACT.md Section 6.2.
    """
    user_public_id: Optional[str] = Field(
        default=None,
        description="Public user identifier of user to add (USR-YYYYMM-XXXXX)",
        examples=["USR-202608-8F29A"]
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Email address of the user to invite/add",
        examples=["student@sih2026.edu"]
    )
    role_in_project: Optional[ProjectMemberRole] = Field(
        default=ProjectMemberRole.CONTRIBUTOR,
        description="Role assigned to the project member (CONTRIBUTOR | FACULTY_MENTOR | LEAD)"
    )
    contribution_percentage: Optional[Decimal] = Field(
        default=Decimal("0.00"),
        ge=0,
        le=100,
        description="Declared contribution percentage (0.00 to 100.00)"
    )

    @model_validator(mode="after")
    def validate_user_identifier_present(self) -> "ProjectMemberCreateRequest":
        if not self.user_public_id and not self.email:
            raise ValueError("Either 'user_public_id' or 'email' must be provided to add a project member.")
        if self.user_public_id:
            self.user_public_id = self.user_public_id.strip()
        if self.email:
            self.email = self.email.lower().strip()
        return self


class ProjectMemberItem(BaseModel):
    """
    Public representation of a project member item (FRONTEND_BACKEND_CONTRACT.md Section 4).
    Strictly excludes internal database UUIDs, passwords, and sensitive fields.
    """
    user: UserProfileResponse = Field(..., description="Public profile of the project member")
    role_in_project: ProjectMemberRole = Field(..., description="Member role in the project")
    contribution_percentage: Optional[float] = Field(
        default=0.0,
        description="Declared contribution percentage"
    )
    is_owner: bool = Field(default=False, description="Whether this member is the primary project owner")
    joined_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the member was registered/joined in UTC"
    )

    model_config = ConfigDict(from_attributes=True)


# Schema alias for backwards compatibility
ProjectMemberResponse = ProjectMemberItem
