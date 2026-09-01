"""
API Module Package.
Exports dependencies, authentication helpers, and exception handlers.
"""

from app.api.dependencies import (
    CurrentUser,
    DbSession,
    Pagination,
    RequestId,
    get_pagination_params,
    get_request_id,
)
from app.api.deps import (
    get_current_user,
    http_bearer,
    require_admin,
    require_faculty,
    require_role,
    require_student,
    require_verifier,
)

__all__ = [
    "CurrentUser",
    "DbSession",
    "Pagination",
    "RequestId",
    "get_pagination_params",
    "get_request_id",
    "get_current_user",
    "http_bearer",
    "require_admin",
    "require_faculty",
    "require_role",
    "require_student",
    "require_verifier",
]
