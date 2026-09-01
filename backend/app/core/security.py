"""
Password Security & Cryptographic Hashing Module.

Implements Argon2id password hashing and verification in accordance with:
- docs/architecture/INTEGRATION_CONTRACT.md (Section 5.1)
- docs/database/DATABASE_DESIGN.md (Section 3)

Argon2id configuration parameters:
- Algorithm: Argon2id (Type.ID)
- Memory cost (m): 65536 KiB (64 MiB)
- Time cost (t): 3 iterations
- Parallelism (p): 4 threads
- Salt length: 16 bytes
- Hash length: 32 bytes
"""

import argon2
from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

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
