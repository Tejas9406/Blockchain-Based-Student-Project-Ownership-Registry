from fastapi import APIRouter
from app.core.exceptions import NotImplementedAppError

router = APIRouter(prefix="/disputes", tags=["Disputes & Claims"])


@router.post(
    "",
    summary="File Dispute (Placeholder)",
    description="Files an academic ownership or plagiarism claim (Phase 8).",
    include_in_schema=False,
)
def file_dispute_placeholder():
    raise NotImplementedAppError(
        message="Dispute filing endpoint is scheduled for Phase 8.",
        code="DISPUTES_NOT_IMPLEMENTED",
    )
