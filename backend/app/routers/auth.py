from fastapi import APIRouter
from app.core.exceptions import NotImplementedAppError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    summary="Register New User (Placeholder)",
    description="Registers a new student, faculty, or verifier account (Phase 3).",
    include_in_schema=False,
)
def register_placeholder():
    raise NotImplementedAppError(
        message="User registration endpoint is scheduled for Phase 3.",
        code="AUTH_NOT_IMPLEMENTED",
    )
