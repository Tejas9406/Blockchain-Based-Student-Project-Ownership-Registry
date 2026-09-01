import secrets
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, ConflictException
from app.core.logging import logger
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserRegisterRequest
from app.utils.identifiers import generate_user_public_id


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
