"""
Pydantic Schemas Package.

Exports standard response envelopes, pagination, error schemas, health check models, and authentication schemas.
"""

from app.schemas.common import (
    ApiMeta,
    ApiResponse,
    get_utc_now_iso,
    format_iso_utc,
)
from app.schemas.error import (
    ApiErrorDetail,
    ApiErrorResponse,
)

from app.schemas.pagination import (
    PaginatedMeta,
    ApiPaginatedResponse,
    PaginationParams,
)
from app.schemas.health import HealthCheckResponse, DatabaseStatus
from app.schemas.user import (
    LoginResponseData,
    RefreshTokenRequest,
    RefreshTokenResponseData,
    UserProfileResponse,
    UserRegisterRequest,
    UserLoginRequest,
    UserRole,
    UserSummaryResponse,
)

from app.schemas.project import (
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectOwnerSummary,
    ProjectSummary,
)
from app.schemas.project_member import (
    ProjectMemberCreateRequest,
    ProjectMemberItem,
    ProjectMemberResponse,
)
from app.schemas.project_version import (
    ArtifactItemSummary,
    BlockchainProofSummary,
    ProjectVersionCreateRequest,
    ProjectVersionDetail,
    ProjectVersionResponse,
    ProjectVersionSummary,
)
from app.schemas.artifact import (
    ArtifactItem,
    ArtifactResponse,
)
from app.schemas.verification import (
    VerificationBlockchainProof,
    VerificationProjectSummary,
    VerificationResponseData,
    VerificationVersionSummary,
    VerifyHashRequest,
)

__all__ = [
    # Common Envelopes
    "ApiMeta",
    "ApiResponse",
    "get_utc_now_iso",
    "format_iso_utc",
    # Pagination
    "PaginatedMeta",
    "ApiPaginatedResponse",
    "PaginationParams",
    # Errors
    "ApiErrorDetail",
    "ApiErrorResponse",
    # Health
    "HealthCheckResponse",
    "DatabaseStatus",
    # Authentication & User
    "LoginResponseData",
    "RefreshTokenRequest",
    "RefreshTokenResponseData",
    "UserProfileResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserRole",
    "UserSummaryResponse",
    # Projects
    "ProjectCreateRequest",
    "ProjectSummary",
    "ProjectOwnerSummary",
    "ProjectDetailResponse",
    # Project Members
    "ProjectMemberCreateRequest",
    "ProjectMemberItem",
    "ProjectMemberResponse",
    # Project Versions
    "ArtifactItemSummary",
    "BlockchainProofSummary",
    "ProjectVersionCreateRequest",
    "ProjectVersionDetail",
    "ProjectVersionResponse",
    "ProjectVersionSummary",
    # Artifacts
    "ArtifactItem",
    "ArtifactResponse",
    # Verification
    "VerifyHashRequest",
    "VerificationProjectSummary",
    "VerificationVersionSummary",
    "VerificationBlockchainProof",
    "VerificationResponseData",
]
