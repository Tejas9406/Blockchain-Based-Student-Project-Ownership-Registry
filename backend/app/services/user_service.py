import secrets
from typing import Tuple
import jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException, ConflictException, UnauthorizedException
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserLoginRequest, UserRegisterRequest
from app.utils.identifiers import generate_user_public_id

# Dummy hash for constant-time defense against timing attacks during failed lookups
DUMMY_TIMING_HASH = "$argon2id$v=19$m=65536,t=3,p=4$dHBhboMIGkw3vpFXx3pyZg$+YOXfuyOi5u/Uj7zzAuqrBN5usg2OZEnv3zwgtU0Qrc"


def register_user(db: Session, request: UserRegisterRequest) -> User:
    """
    Registers a new user in PostgreSQL:
    1. Validates unique email constraint.
    2. Hashes password with Argon2id.
    3. Generates unique public_id (USR-YYYYMM-XXXXX).
    4. Creates User entity and commits the transaction.
    5. Performs automatic rollback on error.
    """
    normalized_email = request.email.lower().strip()

    # Pre-check for existing account with the same email
    existing_user = db.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()

    if existing_user:
        logger.info(f"Registration rejected: Email '{normalized_email}' already registered.")
        raise ConflictException(
            code="EMAIL_ALREADY_EXISTS",
            message="An account with this email address already exists.",
            details={"field": "email", "value": normalized_email}
        )

    # Hash plaintext password using Argon2id
    password_hash = hash_password(request.password)

    # Generate collision-free public_id
    for _ in range(5):
        public_id = generate_user_public_id()
        existing_pid = db.execute(
            select(User).where(User.public_id == public_id)
        ).scalar_one_or_none()
        if not existing_pid:
            break
    else:
        public_id = f"USR-{secrets.token_hex(6).upper()}"

    new_user = User(
        public_id=public_id,
        email=normalized_email,
        hashed_password=password_hash,
        full_name=request.full_name.strip(),
        institution_id=request.institution_id.strip(),
        institution_name=request.institution_name.strip() if request.institution_name else None,
        department=request.department.strip(),
        role=request.role or "STUDENT",
        wallet_address=request.wallet_address.strip() if request.wallet_address else None,
        is_active=True,
        is_verified=False,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User registered successfully: public_id={new_user.public_id}")
        return new_user
    except IntegrityError as exc:
        db.rollback()
        logger.warning(f"Integrity error during registration for {normalized_email}: {str(exc)}")
        raise ConflictException(
            code="USER_ALREADY_EXISTS",
            message="An account with matching unique details already exists.",
            details={"field": "email"}
        )
    except Exception as exc:
        db.rollback()
        logger.error(f"Unexpected error during user registration: {str(exc)}")
        raise AppException(
            status_code=500,
            code="REGISTRATION_FAILED",
            message="An unexpected error occurred while creating the user account. Please try again."
        )


def authenticate_user(db: Session, request: UserLoginRequest) -> Tuple[User, str, str, int]:
    """
    Authenticates user credentials and issues JWT access and refresh tokens:
    1. Looks up the user by normalized email.
    2. Verifies password with Argon2id.
    3. Handles non-existent users and bad passwords identically to prevent user enumeration.
    4. Creates and returns (User, access_token, refresh_token, expires_in_seconds).
    """
    normalized_email = request.email.lower().strip()

    user = db.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()

    if not user:
        # Constant-time mitigation against email enumeration
        verify_password("dummy_constant_time_pass", DUMMY_TIMING_HASH)
        logger.warning("Authentication failed: Account not found.")
        raise UnauthorizedException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password."
        )

    if not verify_password(request.password, user.hashed_password):
        logger.warning(f"Authentication failed: Password mismatch for user public_id={user.public_id}.")
        raise UnauthorizedException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password."
        )

    if not user.is_active:
        logger.warning(f"Authentication failed: Inactive account user public_id={user.public_id}.")
        raise UnauthorizedException(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password."
        )

    access_token = create_access_token(
        subject=user.public_id,
        email=user.email,
        role=user.role,
    )
    refresh_token = create_refresh_token(
        subject=user.public_id,
        email=user.email,
        role=user.role,
    )
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    logger.info(f"User authenticated successfully: public_id={user.public_id}")
    return user, access_token, refresh_token, expires_in


def refresh_access_token(db: Session, refresh_token_str: str) -> Tuple[str, str, int]:
    """
    Validates a JWT refresh token and issues a new access token and rotated refresh token:
    1. Validates signature, expiration, and ensures token type is 'refresh'.
    2. Verifies that the referenced user exists and is active.
    3. Issues a fresh access token and rotated refresh token.
    4. Returns (access_token, new_refresh_token, expires_in_seconds).
    """
    try:
        payload = decode_refresh_token(refresh_token_str)
    except jwt.PyJWTError as exc:
        logger.warning(f"Token refresh rejected: Invalid or expired token: {str(exc)}")
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Invalid or expired refresh token."
        )

    user_public_id = payload.get("sub")
    if not user_public_id:
        logger.warning("Token refresh rejected: Missing subject in token payload.")
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Invalid or expired refresh token."
        )

    user = db.execute(
        select(User).where(User.public_id == user_public_id)
    ).scalar_one_or_none()

    if not user or not user.is_active:
        logger.warning(f"Token refresh rejected: User '{user_public_id}' not found or inactive.")
        raise UnauthorizedException(
            code="INVALID_TOKEN",
            message="Invalid or expired refresh token."
        )

    new_access_token = create_access_token(
        subject=user.public_id,
        email=user.email,
        role=user.role,
    )
    new_refresh_token = create_refresh_token(
        subject=user.public_id,
        email=user.email,
        role=user.role,
    )
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    logger.info(f"Token successfully refreshed for user public_id={user.public_id}")
    return new_access_token, new_refresh_token, expires_in
