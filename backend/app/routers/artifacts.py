from fastapi import APIRouter
from app.core.exceptions import NotImplementedAppError

router = APIRouter(prefix="/artifacts", tags=["Artifacts & Storage"])


@router.post(
    "/upload",
    summary="Upload Artifact File (Placeholder)",
    description="Uploads and pins artifact file to IPFS node (Phase 5).",
    include_in_schema=False,
)
def upload_artifact_placeholder():
    raise NotImplementedAppError(
        message="Artifact upload endpoint is scheduled for Phase 5.",
        code="ARTIFACTS_NOT_IMPLEMENTED",
    )
