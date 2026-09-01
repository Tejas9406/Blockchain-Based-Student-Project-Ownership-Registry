from fastapi import APIRouter
from app.core.exceptions import NotImplementedAppError

router = APIRouter(prefix="/verification", tags=["Public Verification"])


@router.get(
    "/verify-registration/{registration_id}",
    summary="Verify Registration ID (Placeholder)",
    description="Validates registration on smart contract (Phase 6).",
    include_in_schema=False,
)
def verify_registration_placeholder(registration_id: str):
    raise NotImplementedAppError(
        message="Public verification endpoint is scheduled for Phase 6.",
        code="VERIFICATION_NOT_IMPLEMENTED",
    )
