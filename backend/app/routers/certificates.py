from fastapi import APIRouter
from app.core.exceptions import NotImplementedAppError

router = APIRouter(prefix="/certificates", tags=["Certificates & QR"])


@router.get(
    "/{registration_id}",
    summary="Get Certificate Metadata (Placeholder)",
    description="Retrieves PDF and QR verification metadata (Phase 7).",
    include_in_schema=False,
)
def get_certificate_placeholder(registration_id: str):
    raise NotImplementedAppError(
        message="Certificate generation endpoint is scheduled for Phase 7.",
        code="CERTIFICATES_NOT_IMPLEMENTED",
    )
