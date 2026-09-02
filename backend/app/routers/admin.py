from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.session import get_db
from app.core.exceptions import NotImplementedAppError
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.dispute import DisputeAdjudicateRequest, DisputeDetailResponse
from app.schemas.error import ApiErrorResponse
from app.services.dispute_service import adjudicate_dispute

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


@router.patch(
    "/disputes/{dispute_id}/adjudicate",
    response_model=ApiResponse[DisputeDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Adjudicate Dispute",
    description=(
        "Adjudicates an active dispute (OPEN or UNDER_REVIEW) with a formal outcome: "
        "RESOLVED (claim upheld) or REJECTED (claim dismissed). Submits a resolveDispute "
        "transaction to the EVM ProjectRegistry smart contract via relayer (owner)."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[DisputeDetailResponse],
            "description": "Dispute adjudicated successfully and recorded on blockchain.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ApiErrorResponse,
            "description": "Invalid status transition or project version state.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Authentication credentials missing or invalid.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": ApiErrorResponse,
            "description": "Insufficient permissions (ADMIN role required).",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Dispute not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": "Dispute is already resolved or rejected.",
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": ApiErrorResponse,
            "description": "Blockchain relayer or RPC failure.",
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": ApiErrorResponse,
            "description": "Blockchain transaction confirmation timed out.",
        },
    },
)
async def adjudicate_dispute_endpoint(
    dispute_id: str,
    payload: DisputeAdjudicateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> ApiResponse[DisputeDetailResponse]:
    dispute_data = await adjudicate_dispute(
        db=db,
        current_user=current_user,
        dispute_id=dispute_id,
        payload=payload,
    )
    return ApiResponse(
        data=dispute_data,
        meta=ApiMeta(timestamp=get_utc_now_iso()),
    )
