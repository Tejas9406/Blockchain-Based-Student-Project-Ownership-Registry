from typing import Annotated, Generator, Optional
from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.exceptions import NotImplementedAppError
from app.core.middleware import generate_request_id
from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.pagination import PaginationParams


def get_request_id(request: Request) -> str:
    """
    FastAPI dependency to retrieve the correlation Request ID for the current request.
    """
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = generate_request_id()
        request.state.request_id = request_id
    return request_id


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="Page number (1-based index)")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Items per page (max 100)")
    ] = 20,
) -> PaginationParams:
    """
    FastAPI dependency to parse and validate pagination parameters from query string.
    """
    return PaginationParams(page=page, page_size=page_size)


# ==============================================================================
# Authentication & Role Dependency Placeholders (Phase 3 Hook Locations)
# ==============================================================================


async def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> User:
    """
    Dependency placeholder for authenticating JWT Bearer token and retrieving the active User.
    Full implementation will be added in Backend Phase 3 (Authentication & RBAC).
    """
    raise NotImplementedAppError(
        message="Authentication subsystem is not yet implemented (scheduled for Phase 3).",
        code="AUTH_NOT_IMPLEMENTED",
    )


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory placeholder for Role-Based Access Control (RBAC).
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        raise NotImplementedAppError(
            message="Role authorization subsystem is not yet implemented (scheduled for Phase 3).",
            code="AUTH_NOT_IMPLEMENTED",
        )

    return role_checker


# Type aliases for clean endpoint dependency injection
DbSession = Annotated[Session, Depends(get_db)]
RequestId = Annotated[str, Depends(get_request_id)]
Pagination = Annotated[PaginationParams, Depends(get_pagination_params)]
CurrentUser = Annotated[User, Depends(get_current_user)]
