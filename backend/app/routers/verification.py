import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.verification import (
    VerificationResponseData,
    VerifyHashRequest,
)
from app.services.verification_service import (
    verify_by_file,
    verify_by_hash,
    verify_by_registration_id,
)

router = APIRouter(prefix="/verification", tags=["Public Verification"])


@router.get(
    "/verify-registration/{registration_id}",
    response_model=ApiResponse[VerificationResponseData],
    status_code=status.HTTP_200_OK,
    summary="Verify Project Version by Registration ID",
    description="Public endpoint to verify a project version proof using its unique certificate registration ID (e.g. REG-2026-A8F92).",
)
async def verify_registration(
    registration_id: str,
    db: Session = Depends(get_db),
):
    """
    Public trustless verification endpoint by Registration ID:
    - Validates registration ID format (REG-YYYY-XXXXX)
    - Resolves authoritative project and version metadata from registry
    - Resolves blockchain proof if version has been anchored on-chain
    - Distinguishes registered/pending, anchored, and disputed states
    - Never leaks internal database UUIDs, passwords, or filesystem paths
    """
    result = await verify_by_registration_id(
        db=db,
        registration_id=registration_id,
    )

    return ApiResponse[VerificationResponseData](
        success=True,
        data=result,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=f"req_{uuid.uuid4().hex[:12]}",
        ),
    )


@router.post(
    "/verify-hash",
    response_model=ApiResponse[VerificationResponseData],
    status_code=status.HTTP_200_OK,
    summary="Verify Project Ownership by SHA-256 Hash",
    description="Public endpoint to verify if a raw 64-character hexadecimal SHA-256 hash matches any registered project composite version or artifact.",
)
async def verify_hash(
    request: VerifyHashRequest,
    db: Session = Depends(get_db),
):
    """
    Public trustless verification endpoint by raw SHA-256 hash:
    - Validates hexadecimal format and exact 64-character length
    - Matches against composite version digests and individual artifact hashes
    - Optionally scopes match to a specific registration ID
    - Returns verified metadata and blockchain proof if matched
    """
    result = await verify_by_hash(
        db=db,
        sha256_hash=request.sha256_hash,
        registration_id=request.registration_id,
    )

    return ApiResponse[VerificationResponseData](
        success=True,
        data=result,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=f"req_{uuid.uuid4().hex[:12]}",
        ),
    )


@router.post(
    "/verify-file",
    response_model=ApiResponse[VerificationResponseData],
    status_code=status.HTTP_200_OK,
    summary="Verify Uploaded File Directly",
    description="Public endpoint to verify project ownership by uploading a file. Streams bytes in 64 KB chunks, computes SHA-256, and matches against registered artifacts. File content is immediately discarded.",
)
async def verify_file(
    file: UploadFile = File(...),
    registration_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Public trustless verification endpoint by uploaded file:
    - Memory-safe incremental streaming SHA-256 calculation (64 KB chunks)
    - Enforces 50 MB ceiling and rejects empty files
    - Matches computed digest against registered project artifacts
    - Never stores the uploaded verification file in storage or database
    """
    result = await verify_by_file(
        db=db,
        file=file,
        registration_id=registration_id,
    )

    return ApiResponse[VerificationResponseData](
        success=True,
        data=result,
        meta=ApiMeta(
            timestamp=get_utc_now_iso(),
            request_id=f"req_{uuid.uuid4().hex[:12]}",
        ),
    )
