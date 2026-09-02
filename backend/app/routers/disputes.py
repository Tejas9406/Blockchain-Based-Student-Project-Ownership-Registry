from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.common import ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.dispute import DisputeCreateRequest, DisputeDetailResponse
from app.schemas.error import ApiErrorResponse
from app.services.dispute_service import (
    get_dispute,
    list_project_disputes,
    raise_dispute,
)

router = APIRouter(prefix="/disputes", tags=["Disputes & Claims"])


@router.post(
    "",
    response_model=ApiResponse[DisputeDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Raise Ownership Dispute",
    description=(
        "Files an academic ownership, plagiarism, or unauthorized use claim against a project version. "
        "Pins dispute evidence to IPFS, records the dispute in PostgreSQL, and submits a raiseDispute "
        "transaction to the EVM ProjectRegistry smart contract via relayer."
    ),
    responses={
        status.HTTP_201_CREATED: {
            "model": ApiResponse[DisputeDetailResponse],
            "description": "Dispute successfully recorded and anchored on-chain.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ApiErrorResponse,
            "description": "Validation error or target version not in ANCHORED status.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Missing or invalid bearer token.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Target project or registration ID not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": "An active dispute already exists on this project or version.",
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
async def create_dispute_endpoint(
    payload: DisputeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT, UserRole.FACULTY, UserRole.ADMIN)),
) -> ApiResponse[DisputeDetailResponse]:
    dispute_data = await raise_dispute(
        db=db,
        current_user=current_user,
        payload=payload,
    )
    return ApiResponse(
        data=dispute_data,
        meta=ApiMeta(timestamp=get_utc_now_iso()),
    )


@router.get(
    "/{dispute_id}",
    response_model=ApiResponse[DisputeDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Dispute Details",
    description="Retrieves the detailed record and status of a dispute by its public ID or internal UUID.",
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[DisputeDetailResponse],
            "description": "Dispute details retrieved successfully.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Authentication required.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Dispute record not found.",
        },
    },
)
def get_dispute_endpoint(
    dispute_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[DisputeDetailResponse]:
    dispute_data = get_dispute(
        db=db,
        dispute_id=dispute_id,
        current_user=current_user,
    )
    return ApiResponse(
        data=dispute_data,
        meta=ApiMeta(timestamp=get_utc_now_iso()),
    )


@router.get(
    "/project/{project_id}",
    response_model=ApiResponse[List[DisputeDetailResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Disputes for Project",
    description="Retrieves all dispute records associated with a specific project.",
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[List[DisputeDetailResponse]],
            "description": "Project disputes retrieved successfully.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Authentication required.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Project not found.",
        },
    },
)
def list_project_disputes_endpoint(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[DisputeDetailResponse]]:
    disputes = list_project_disputes(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )
    return ApiResponse(
        data=disputes,
        meta=ApiMeta(timestamp=get_utc_now_iso()),
    )
