from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ProjectStatus, ProjectVersionStage, ProjectVisibility


class ProjectOwnerSummary(BaseModel):
    """
    Summary representation of project owner.
    Excludes sensitive internal database identifiers and credentials.
    """
    public_id: str = Field(..., description="Public user identifier (USR-YYYYMM-XXXXX)")
    full_name: str = Field(..., description="Full name of the project owner")

    model_config = ConfigDict(from_attributes=True)


class ProjectCreateRequest(BaseModel):
    """
    Payload for creating a new project entity (API_CONTRACT.md Section 5.1).
    Strictly forbids client-injected internal UUIDs, slugs, statuses, timestamps, or arbitrary ownership.
    """
    title: str = Field(..., min_length=3, max_length=255, description="Project title")
    abstract: Optional[str] = Field(default=None, max_length=5000, description="Project overview or abstract")
    category: str = Field(..., min_length=2, max_length=100, description="Project domain category (e.g. AI, WEB3, CYBERSECURITY)")
    department: str = Field(..., min_length=2, max_length=100, description="Academic department (e.g. Computer Science)")
    academic_year: str = Field(..., min_length=4, max_length=50, description="Academic year (e.g. 2025-2026)")
    visibility: Optional[ProjectVisibility] = Field(
        default=ProjectVisibility.PUBLIC,
        description="Project visibility level (PUBLIC, INSTITUTIONAL, PRIVATE)"
    )

    @field_validator("title", "category", "department", "academic_year")
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or whitespace only.")
        return trimmed

    @field_validator("abstract")
    @classmethod
    def validate_abstract(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            return trimmed if trimmed else None
        return None


class ProjectSummary(BaseModel):
    """
    Standard project summary schema (FRONTEND_BACKEND_CONTRACT.md Section 4).
    Conforms to the universal API contract.
    """
    public_id: str = Field(..., description="Public project identifier (PRJ-YYYYMM-XXXXX)")
    slug: str = Field(..., description="URL-friendly unique slug")
    title: str = Field(..., description="Project title")
    abstract: Optional[str] = Field(default=None, description="Project abstract / overview")
    category: str = Field(..., description="Project domain category")
    department: str = Field(..., description="Academic department")
    academic_year: str = Field(..., description="Academic year")
    current_lifecycle_stage: ProjectVersionStage = Field(..., description="Current milestone stage (IDEA, DESIGN, PROTOTYPE, FINAL)")
    visibility: ProjectVisibility = Field(..., description="Visibility scope")
    status: ProjectStatus = Field(..., description="Project status (ACTIVE, ARCHIVED, UNDER_DISPUTE)")
    owner: ProjectOwnerSummary = Field(..., description="Primary owner / lead author summary")
    created_at: datetime = Field(..., description="Project creation timestamp in UTC")

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectSummary):
    """
    Detailed project response representation.
    """
    updated_at: datetime = Field(..., description="Last modification timestamp in UTC")

    model_config = ConfigDict(from_attributes=True)
