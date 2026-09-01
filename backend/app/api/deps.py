from typing import Callable, Optional, Set, Union
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.logging import logger
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserRole

# HTTPBearer security scheme (auto_error=False allows custom exception formatting)
http_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency for authenticating Bearer JWT access tokens.
    
    1. Validates presence and format of Authorization Bearer header.
    2. Decodes JWT access token and enforces type == 'access'.
    3. Extracts subject (user public_id).
    4. Queries PostgreSQL for active User record.
    5. Returns authenticated User model.
    """
    if not credentials or not credentials.credentials:
        logger.warning("Authentication failed: Missing or malformed Authorization header.")
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Missing or invalid authentication credentials."
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        logger.warning(f"Authentication failed: Access token validation error: {str(exc)}")
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Invalid or expired access token."
        )

    user_public_id = payload.get("sub")
    if not user_public_id:
        logger.warning("Authentication failed: Token payload missing 'sub' claim.")
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Invalid access token."
        )

    user = db.execute(
        select(User).where(User.public_id == user_public_id)
    ).scalar_one_or_none()

    if not user:
        logger.warning(f"Authentication failed: User '{user_public_id}' not found.")
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="User account not found."
        )

    if not user.is_active:
        logger.warning(f"Authentication failed: Inactive user account '{user_public_id}'.")
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="User account is deactivated."
        )

    return user


def require_role(*allowed_roles: Union[UserRole, str]) -> Callable[[User], User]:
    """
    FastAPI dependency factory for Role-Based Access Control (RBAC).

    Enforces that the authenticated user possesses one of the specified allowed roles.
    Reuses get_current_user() for authentication.
    Returns 401 Unauthorized if unauthenticated, or 403 Forbidden if the authenticated user's role is insufficient.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.ADMIN))])
        or
        def my_route(current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY))):
    """
    valid_roles: Set[str] = {
        role.value if hasattr(role, "value") else str(role)
        for role in allowed_roles
    }

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role_val not in valid_roles and current_user.role not in valid_roles:
            logger.warning(
                f"Authorization failed: User '{current_user.public_id}' with role '{current_user.role}' "
                f"attempted to access an endpoint requiring one of: {sorted(list(valid_roles))}."
            )
            raise ForbiddenException(
                code="FORBIDDEN",
                message="You do not have permission to perform this action."
            )
        return current_user


    return role_checker


# Named single-role dependencies for clean dependency injection
require_student = require_role(UserRole.STUDENT)
require_faculty = require_role(UserRole.FACULTY)
require_admin = require_role(UserRole.ADMIN)
require_verifier = require_role(UserRole.VERIFIER)


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    FastAPI dependency for optionally extracting the authenticated User.
    Returns User if valid Bearer token is present, otherwise returns None.
    Does not raise 401 exceptions on missing or malformed tokens.
    """
    if not credentials or not credentials.credentials:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
        user_public_id = payload.get("sub")
        if not user_public_id:
            return None

        user = db.execute(
            select(User).where(User.public_id == user_public_id)
        ).scalar_one_or_none()

        if user and user.is_active:
            return user
    except Exception:
        return None

    return None

