import pytest
from app.core.security import hash_password, verify_password


def test_password_can_be_hashed():
    """
    Verify that a plaintext password produces a non-empty string hash.
    """
    raw_password = "CorrectHorseBatteryStaple#2026"
    password_hash = hash_password(raw_password)
    
    assert isinstance(password_hash, str)
    assert len(password_hash) > 0


def test_hash_is_different_from_plaintext():
    """
    Verify that the password hash is completely different from the plaintext password.
    """
    raw_password = "SecurePassword123!"
    password_hash = hash_password(raw_password)
    
    assert password_hash != raw_password
    assert raw_password not in password_hash


def test_hash_format_is_argon2id():
    """
    Verify that the generated hash conforms to the Argon2id format with configured parameters.
    """
    raw_password = "TestPasswordArgon2id"
    password_hash = hash_password(raw_password)
    
    # Argon2id encoded string starts with $argon2id$
    assert password_hash.startswith("$argon2id$")
    # Verify memory cost parameter m=65536, time cost t=3, parallelism p=4
    assert "m=65536" in password_hash
    assert "t=3" in password_hash
    assert "p=4" in password_hash


def test_verify_password_with_correct_password():
    """
    Verify that verify_password returns True for the matching password.
    """
    raw_password = "CorrectPassword@2026"
    password_hash = hash_password(raw_password)
    
    assert verify_password(raw_password, password_hash) is True


def test_verify_password_with_incorrect_password():
    """
    Verify that verify_password returns False for an incorrect password.
    """
    raw_password = "ValidPassword123"
    wrong_password = "WrongPassword999"
    password_hash = hash_password(raw_password)
    
    assert verify_password(wrong_password, password_hash) is False


def test_hashes_for_same_password_are_unique():
    """
    Verify that hashing the same password twice generates distinct hashes due to random salting.
    """
    raw_password = "SamePasswordTwice!#42"
    hash_1 = hash_password(raw_password)
    hash_2 = hash_password(raw_password)
    
    assert hash_1 != hash_2
    assert verify_password(raw_password, hash_1) is True
    assert verify_password(raw_password, hash_2) is True


def test_empty_password_hashing_raises_value_error():
    """
    Verify that attempting to hash an empty password raises ValueError.
    """
    with pytest.raises(ValueError, match="Password cannot be empty"):
        hash_password("")


def test_invalid_type_password_hashing_raises_type_error():
    """
    Verify that attempting to hash a non-string input raises TypeError.
    """
    with pytest.raises(TypeError, match="Password must be a string"):
        hash_password(None)  # type: ignore

    with pytest.raises(TypeError, match="Password must be a string"):
        hash_password(123456)  # type: ignore


def test_verify_password_invalid_inputs():
    """
    Verify that verify_password gracefully returns False for empty or invalid inputs.
    """
    valid_hash = hash_password("valid_password")
    
    # Empty inputs
    assert verify_password("", valid_hash) is False
    assert verify_password("valid_password", "") is False
    assert verify_password("", "") is False
    
    # Non-string inputs
    assert verify_password(None, valid_hash) is False  # type: ignore
    assert verify_password("valid_password", None) is False  # type: ignore
    assert verify_password(12345, valid_hash) is False  # type: ignore
    
    # Corrupted / invalid hash strings
    assert verify_password("valid_password", "not_a_valid_argon2_hash") is False
    assert verify_password("valid_password", "$argon2id$v=19$m=65536,t=3,p=4$corrupted$invalid") is False


def test_security_verification_contract():
    """
    Verify the primary security contract:
    verify_password(correct, hash_password(correct)) == True
    verify_password(wrong, hash_password(correct)) == False
    """
    correct_password = "P@ssw0rd!Registry_SIH2026_CYB05"
    wrong_password = "P@ssw0rd!Registry_SIH2026_CYB05_Incorrect"
    
    stored_hash = hash_password(correct_password)
    
    assert verify_password(correct_password, stored_hash) is True
    assert verify_password(wrong_password, stored_hash) is False
