from fastapi import APIRouter
from app.core.exceptions import NotImplementedAppError

router = APIRouter(prefix="/projects", tags=["Projects & Milestones"])


@router.get(
    "",
    summary="List Projects (Placeholder)",
    description="Retrieves a paginated catalog of projects (Phase 4).",
    include_in_schema=False,
)
def list_projects_placeholder():
    raise NotImplementedAppError(
        message="Project catalog endpoint is scheduled for Phase 4.",
        code="PROJECTS_NOT_IMPLEMENTED",
    )
