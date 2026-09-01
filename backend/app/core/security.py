"""
Password Security & Cryptographic Hashing Module + JWT Token Generation.

Implements:
- Argon2id password hashing and verification (DATABASE_DESIGN.md Section 3, INTEGRATION_CONTRACT.md Section 5.1)
- JWT access and refresh token generation and decoding (API_CONTRACT.md Section 4, INTEGRATION_CONTRACT.md Section 5.1)

Argon2id configuration parameters:
- Algorithm: Argon2id (Type.ID)
- Memory cost (m): 65536 KiB (64 MiB)
- Time cost (t): 3 iterations
- Parallelism (p): 4 threads
- Salt length: 16 bytes
- Hash length: 32 bytes
"""

from datetime import datetime, timedelta, timezone
import secrets
from typing import Any, Dict, Optional
import argon2
from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
import jwt

from app.core.config import settings

# Initialize Argon2id PasswordHasher with project-specified secure parameters
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using Argon2id.

    Args:
        password: The plaintext password string to hash.

    Returns:
        The Argon2id password hash string.

    Raises:
        TypeError: If password is not a string.
        ValueError: If password is empty.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")
    if not password:
        raise ValueError("Password cannot be empty.")

    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored Argon2id password hash.

    Args:
        password: The plaintext password string to verify.
        password_hash: The stored Argon2id password hash.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    if not isinstance(password, str) or not isinstance(password_hash, str):
        return False
    if not password or not password_hash:
        return False

    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception:
        return False


def create_access_token(
    subject: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a cryptographically signed JWT access token.
    Claims strictly limited to: sub, email, role, type, iat, exp.
    Never includes password, password_hash, or sensitive internals.

    Args:
        subject: Subject identifier (user public_id: USR-YYYYMM-XXXXX).
        email: User's normalized email address.
        role: User role (e.g. STUDENT).
        expires_delta: Optional custom expiration duration.

    Returns:
        Encoded JWT access token string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": subject,
        "email": email,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token signature, algorithm, and standard claims.

    Args:
        token: The encoded JWT access token string.

    Returns:
        The decoded payload dictionary.

    Raises:
        jwt.PyJWTError: If signature, algorithm, or claims are invalid or expired.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "email", "role", "type", "iat", "exp"]}
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Token type must be 'access'.")
    return payload


def create_refresh_token(
    subject: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a cryptographically signed JWT refresh token.
    Claims strictly limited to: sub, email, role, type ('refresh'), jti, iat, exp.
    Default expiration: 7 days.

    Args:
        subject: Subject identifier (user public_id: USR-YYYYMM-XXXXX).
        email: User's normalized email address.
        role: User role (e.g. STUDENT).
        expires_delta: Optional custom expiration duration.

    Returns:
        Encoded JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: Dict[str, Any] = {
        "sub": subject,
        "email": email,
        "role": role,
        "type": "refresh",
        "jti": secrets.token_hex(16),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_refresh_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT refresh token signature, algorithm, and claims.
    Strictly verifies that token type claim is 'refresh'.

    Args:
        token: The encoded JWT refresh token string.

    Returns:
        The decoded payload dictionary.

    Raises:
        jwt.PyJWTError: If signature, algorithm, or claims are invalid or expired.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "email", "role", "type", "iat", "exp"]}
    )
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Token type must be 'refresh'.")
    return payload
