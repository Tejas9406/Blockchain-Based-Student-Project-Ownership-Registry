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
# Authentication & Role Dependencies (Integrated from Phase 3 Auth)
# ==============================================================================

from app.api.deps import get_current_user, require_role, http_bearer

# Type aliases for clean endpoint dependency injection
DbSession = Annotated[Session, Depends(get_db)]
RequestId = Annotated[str, Depends(get_request_id)]
Pagination = Annotated[PaginationParams, Depends(get_pagination_params)]
CurrentUser = Annotated[User, Depends(get_current_user)]
