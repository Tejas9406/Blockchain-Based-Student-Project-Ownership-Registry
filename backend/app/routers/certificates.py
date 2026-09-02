from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.certificate import CertificateMetadataData
from app.schemas.common import ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.error import ApiErrorResponse
from app.services.certificate_service import generate_certificate_pdf, get_certificate_metadata

router = APIRouter(prefix="/certificates", tags=["Certificates & QR"])


@router.get(
    "/{registration_id}",
    response_model=ApiResponse[CertificateMetadataData],
    status_code=status.HTTP_200_OK,
    summary="Get Certificate Metadata",
    description=(
        "Public endpoint to retrieve authoritative ownership certificate metadata "
        "for an anchored project version (API_CONTRACT Module 7.1)."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": ApiResponse[CertificateMetadataData],
            "description": "Certificate metadata retrieved successfully.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ApiErrorResponse,
            "description": "Version is not anchored, missing blockchain record, or has cryptographic mismatch.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Certificate registration ID not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": "Version has an active dispute or dispute was upheld against it.",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ApiErrorResponse,
            "description": "Invalid registration ID format.",
        },
    },
)
async def get_certificate_metadata_endpoint(
    registration_id: str,
    db: Session = Depends(get_db),
) -> ApiResponse[CertificateMetadataData]:
    metadata = await get_certificate_metadata(registration_id=registration_id, db=db)
    return ApiResponse(
        success=True,
        data=metadata,
        meta=ApiMeta(timestamp=get_utc_now_iso()),
    )


@router.get(
    "/{registration_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download Ownership Certificate PDF",
    description=(
        "Public endpoint to download a specification-compliant, read-only PDF ownership certificate "
        "representing verified on-chain registration proof."
    ),
    responses={
        status.HTTP_200_OK: {
            "content": {"application/pdf": {}},
            "description": "Returns generated PDF binary certificate.",
        },
        status.HTTP_400_BAD_REQUEST: {"model": ApiErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ApiErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ApiErrorResponse},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ApiErrorResponse},
    },
)
async def download_certificate_pdf_endpoint(
    registration_id: str,
    db: Session = Depends(get_db),
) -> Response:
    pdf_bytes = await generate_certificate_pdf(registration_id=registration_id, db=db)
    clean_id = registration_id.strip().upper()
    filename = f"ownership-certificate-{clean_id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=3600",
        },
    )
