from typing import Optional
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.core.logging import logger
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.user import User

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
