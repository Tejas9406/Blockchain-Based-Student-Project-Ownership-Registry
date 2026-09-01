"""
Pydantic Schemas Package.

Exports standard response envelopes, pagination, error schemas, and health check models.
"""

from app.schemas.common import ApiMeta, ApiResponse
from app.schemas.pagination import (
    PaginatedMeta,
    ApiPaginatedResponse,
    PaginationParams,
)
from app.schemas.error import ApiErrorDetail, ApiErrorResponse
from app.schemas.health import HealthCheckResponse, DatabaseStatus

__all__ = [
    # Common Envelopes
    "ApiMeta",
    "ApiResponse",
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
]
