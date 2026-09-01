from fastapi import APIRouter
from app.core.exceptions import NotImplementedAppError

router = APIRouter(prefix="/admin", tags=["Admin Management"])


@router.get(
    "/audit-logs",
    summary="Get System Audit Logs (Placeholder)",
    description="Retrieves administrative audit logs (Phase 8).",
    include_in_schema=False,
)
def get_audit_logs_placeholder():
    raise NotImplementedAppError(
        message="Admin management endpoint is scheduled for Phase 8.",
        code="ADMIN_NOT_IMPLEMENTED",
    )
