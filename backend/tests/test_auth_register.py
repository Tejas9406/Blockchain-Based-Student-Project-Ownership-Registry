from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


def test_successful_user_registration(client: TestClient, db_session: Session):
    """
    Test 1 & 9 & 10: Successful registration returns HTTP 201, standardized envelope,
    generated public_id in USR-YYYYMM-XXXXX format, and does NOT expose internal UUID.
    """
    payload = {
        "email": "tejas.sharma@nit.edu",
        "password": "SecurePassword#2026",
        "full_name": "Tejas Sharma",
        "institution_id": "NIT-2023-CS-041",
        "institution_name": "National Institute of Technology",
        "department": "Computer Science & Engineering",
        "role": "STUDENT",
        "wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "meta" in data
    assert "timestamp" in data["meta"]
    assert "request_id" in data["meta"]

    user_data = data["data"]
    assert user_data["email"] == "tejas.sharma@nit.edu"
    assert user_data["full_name"] == "Tejas Sharma"
    assert user_data["institution_id"] == "NIT-2023-CS-041"
    assert user_data["institution_name"] == "National Institute of Technology"
    assert user_data["department"] == "Computer Science & Engineering"
    assert user_data["role"] == "STUDENT"
    assert user_data["wallet_address"] == "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    assert user_data["is_verified"] is False
    assert "created_at" in user_data

    # Verify public_id format (USR-YYYYMM-XXXXX)
    public_id = user_data["public_id"]
    assert public_id.startswith("USR-")
    parts = public_id.split("-")
    assert len(parts) == 3
    assert len(parts[1]) == 6  # YYYYMM
    assert len(parts[2]) == 5  # XXXXX hex


def test_internal_uuid_not_exposed_in_response(client: TestClient, db_session: Session):
    """
    Test 10: The internal database UUID is not exposed as public_id or anywhere in response.
    """
    payload = {
        "email": "uuid.check@nit.edu",
        "password": "Password123#",
        "full_name": "UUID Check User",
        "institution_id": "NIT-2023-CS-099",
        "department": "Computer Science & Engineering"
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    db_user = db_session.execute(
        select(User).where(User.email == "uuid.check@nit.edu")
    ).scalar_one()

    internal_uuid_str = str(db_user.id)
    response_text = response.text

    assert internal_uuid_str not in response_text
    assert "id" not in response.json()["data"]
    assert response.json()["data"]["public_id"] != internal_uuid_str


def test_password_stored_as_argon2id_hash(client: TestClient, db_session: Session):
    """
    Test 2 & Security Test: Password is saved in database as a valid Argon2id hash.
    """
    raw_password = "MySuperSecretPassword@2026!"
    payload = {
        "email": "aman.verma@nit.edu",
        "password": raw_password,
        "full_name": "Aman Verma",
        "institution_id": "NIT-2023-CS-042",
        "department": "Computer Science & Engineering"
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    # Query the user directly from database to inspect the stored hash
    db_user = db_session.execute(
        select(User).where(User.email == "aman.verma@nit.edu")
    ).scalar_one()

    assert db_user.hashed_password.startswith("$argon2id$")
    assert "m=65536" in db_user.hashed_password
    assert "t=3" in db_user.hashed_password
    assert "p=4" in db_user.hashed_password
    assert db_user.hashed_password != raw_password
    assert verify_password(raw_password, db_user.hashed_password) is True


def test_password_and_hash_not_returned_in_response(client: TestClient):
    """
    Test 3 & 4 & Security Test: Neither plaintext password nor password_hash is returned.
    """
    raw_password = "DoNotLeakThisPassword#123"
    payload = {
        "email": "sneha.patel@nit.edu",
        "password": raw_password,
        "full_name": "Sneha Patel",
        "institution_id": "NIT-2023-CS-043",
        "department": "Computer Science & Engineering"
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    user_data = data["data"]
    assert "password" not in user_data
    assert "hashed_password" not in user_data
    assert "password_hash" not in user_data
    assert raw_password not in response.text
    assert "$argon2id$" not in response.text


def test_duplicate_email_registration_returns_409(client: TestClient):
    """
    Test 5: Registering with an existing email returns HTTP 409 Conflict in standard error envelope.
    """
    payload = {
        "email": "duplicate.test@nit.edu",
        "password": "Password123#",
        "full_name": "Original User",
        "institution_id": "NIT-2023-CS-044",
        "department": "Computer Science & Engineering"
    }

    # First registration succeeds
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with identical email (different case to test normalization)
    payload_dup = payload.copy()
    payload_dup["email"] = "DUPLICATE.TEST@NIT.EDU"
    payload_dup["full_name"] = "Duplicate User"

    res2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert res2.status_code == 409

    data = res2.json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMAIL_ALREADY_EXISTS"
    assert "already exists" in data["error"]["message"].lower()
    assert "meta" in data
    assert "timestamp" in data["meta"]


def test_invalid_email_format_returns_422(client: TestClient):
    """
    Test 6: Invalid email format is rejected by Pydantic with HTTP 422.
    """
    payload = {
        "email": "not-a-valid-email",
        "password": "ValidPassword#123",
        "full_name": "Invalid Email User",
        "institution_id": "NIT-2023-CS-045",
        "department": "Computer Science & Engineering"
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_empty_or_short_password_returns_422(client: TestClient):
    """
    Test 7: Empty or under-length password is rejected with HTTP 422.
    """
    payload_empty = {
        "email": "empty.pwd@nit.edu",
        "password": "",
        "full_name": "Empty Pwd User",
        "institution_id": "NIT-2023-CS-046",
        "department": "Computer Science & Engineering"
    }
    res_empty = client.post("/api/v1/auth/register", json=payload_empty)
    assert res_empty.status_code == 422

    payload_short = payload_empty.copy()
    payload_short["password"] = "short"
    res_short = client.post("/api/v1/auth/register", json=payload_short)
    assert res_short.status_code == 422


def test_missing_required_fields_returns_422(client: TestClient):
    """
    Test 8: Missing required registration fields returns HTTP 422.
    """
    # Missing department and institution_id
    payload = {
        "email": "missing.fields@nit.edu",
        "password": "ValidPassword#123",
        "full_name": "Incomplete User"
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_role_escalation_is_prevented(client: TestClient):
    """
    Security Test: Public registration cannot escalate roles to ADMIN or FACULTY.
    """
    payload = {
        "email": "hacker@nit.edu",
        "password": "Password123#",
        "full_name": "Role Escalation Attempt",
        "institution_id": "NIT-2023-CS-047",
        "department": "Computer Science & Engineering",
        "role": "ADMIN"  # Attempt to register as ADMIN
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_same_password_generates_different_hashes(client: TestClient, db_session: Session):
    """
    Security Test: Two users registering with the same plaintext password have different hashes.
    """
    shared_password = "SharedCommonPassword#2026"
    
    user1_payload = {
        "email": "user1@nit.edu",
        "password": shared_password,
        "full_name": "User One",
        "institution_id": "NIT-2023-CS-048",
        "department": "Computer Science & Engineering"
    }
    user2_payload = {
        "email": "user2@nit.edu",
        "password": shared_password,
        "full_name": "User Two",
        "institution_id": "NIT-2023-CS-049",
        "department": "Computer Science & Engineering"
    }

    res1 = client.post("/api/v1/auth/register", json=user1_payload)
    res2 = client.post("/api/v1/auth/register", json=user2_payload)

    assert res1.status_code == 201
    assert res2.status_code == 201

    u1 = db_session.execute(select(User).where(User.email == "user1@nit.edu")).scalar_one()
    u2 = db_session.execute(select(User).where(User.email == "user2@nit.edu")).scalar_one()

    assert u1.hashed_password != u2.hashed_password
    assert verify_password(shared_password, u1.hashed_password) is True
    assert verify_password(shared_password, u2.hashed_password) is True


def test_database_rollback_on_failed_creation(client: TestClient, db_session: Session):
    """
    Test 11: When a database error occurs during creation, the transaction is rolled back.
    """
    payload = {
        "email": "rollback.test@nit.edu",
        "password": "Password123#",
        "full_name": "Rollback User",
        "institution_id": "NIT-2023-CS-050",
        "department": "Computer Science & Engineering"
    }

    with patch.object(Session, "commit", side_effect=Exception("Simulated commit failure")):
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "REGISTRATION_FAILED"

    # Verify no partial user was committed
    user_in_db = db_session.execute(
        select(User).where(User.email == "rollback.test@nit.edu")
    ).scalar_one_or_none()
    assert user_in_db is None


def test_openapi_documentation_includes_registration(client: TestClient):
    """
    Test 15: OpenAPI schema includes POST /api/v1/auth/register with documented request/response.
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "/api/v1/auth/register" in schema["paths"]
    
    register_path = schema["paths"]["/api/v1/auth/register"]
    assert "post" in register_path
    post_op = register_path["post"]
    assert post_op["summary"] == "Register New User Account"
    assert "201" in post_op["responses"]
    assert "409" in post_op["responses"]
    assert "422" in post_op["responses"]
