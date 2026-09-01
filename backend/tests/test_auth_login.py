from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    decode_refresh_token,
)


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    """Helper fixture to register a test user."""
    payload = {
        "email": "login.test@nit.edu",
        "password": "CorrectPassword#2026",
        "full_name": "Login Test User",
        "institution_id": "NIT-2023-CS-100",
        "institution_name": "National Institute of Technology",
        "department": "Computer Science & Engineering",
        "role": "STUDENT",
        "wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    return payload


def test_successful_login_returns_token_and_user(client: TestClient, registered_user: dict):
    """
    Test 1 & 2: Successful login with valid credentials returns HTTP 200, access token, refresh token, and user summary.
    """
    login_payload = {
        "email": registered_user["email"],
        "password": registered_user["password"]
    }

    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "meta" in data
    assert "timestamp" in data["meta"]
    assert "request_id" in data["meta"]

    token_data = data["data"]
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] == 3600
    assert "user" in token_data

    # Verify refresh token is valid
    decoded_refresh = decode_refresh_token(token_data["refresh_token"])
    assert decoded_refresh["type"] == "refresh"
    assert decoded_refresh["email"] == registered_user["email"]

    user_info = token_data["user"]
    assert user_info["email"] == registered_user["email"]
    assert user_info["full_name"] == registered_user["full_name"]
    assert user_info["role"] == "STUDENT"
    assert user_info["institution_id"] == registered_user["institution_id"]
    assert user_info["department"] == registered_user["department"]
    assert user_info["public_id"].startswith("USR-")


def test_jwt_token_validity_and_claims(client: TestClient, registered_user: dict):
    """
    Test 3, 4, 5, 6: Access token is a cryptographically valid JWT with expected claims.
    """
    login_payload = {
        "email": registered_user["email"],
        "password": registered_user["password"]
    }

    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200

    access_token = response.json()["data"]["access_token"]
    user_public_id = response.json()["data"]["user"]["public_id"]

    # Decode and verify token using the server's configured secret & algorithm
    decoded = decode_access_token(access_token)

    # Verify standard claims
    assert decoded["sub"] == user_public_id
    assert decoded["email"] == registered_user["email"]
    assert decoded["role"] == "STUDENT"
    assert decoded["type"] == "access"
    assert "iat" in decoded
    assert "exp" in decoded

    # Expiration should be ~3600 seconds in the future
    assert decoded["exp"] > decoded["iat"]
    duration = decoded["exp"] - decoded["iat"]
    assert duration == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Ensure no disallowed/sensitive claims are embedded
    allowed_claims = {"sub", "email", "role", "type", "iat", "exp"}
    assert set(decoded.keys()) == allowed_claims


def test_login_with_wrong_password_fails(client: TestClient, registered_user: dict):
    """
    Test 7: Login attempt with an incorrect password returns HTTP 401 Unauthorized.
    """
    login_payload = {
        "email": registered_user["email"],
        "password": "WrongPassword999!"
    }

    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
    assert data["error"]["message"] == "Invalid email or password."


def test_login_with_unknown_email_fails(client: TestClient):
    """
    Test 8: Login attempt with a non-existent email returns HTTP 401 Unauthorized.
    """
    login_payload = {
        "email": "nonexistent.user@nit.edu",
        "password": "AnyPassword#123"
    }

    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"
    assert data["error"]["message"] == "Invalid email or password."


def test_anti_enumeration_identical_failure_response(client: TestClient, registered_user: dict):
    """
    Test 9: Unknown email and incorrect password yield identical status code, error code, and message.
    """
    wrong_pwd_res = client.post("/api/v1/auth/login", json={
        "email": registered_user["email"],
        "password": "IncorrectPassword#999"
    })
    unknown_email_res = client.post("/api/v1/auth/login", json={
        "email": "completely.unknown.email@nit.edu",
        "password": "IncorrectPassword#999"
    })

    assert wrong_pwd_res.status_code == unknown_email_res.status_code == 401
    assert wrong_pwd_res.json()["error"]["code"] == unknown_email_res.json()["error"]["code"] == "INVALID_CREDENTIALS"
    assert wrong_pwd_res.json()["error"]["message"] == unknown_email_res.json()["error"]["message"] == "Invalid email or password."


def test_sensitive_data_not_exposed_in_login_response(client: TestClient, registered_user: dict):
    """
    Test 10, 11, 12: Password, password_hash, internal UUID, and JWT secret are never in the response.
    """
    login_payload = {
        "email": registered_user["email"],
        "password": registered_user["password"]
    }

    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200

    response_text = response.text
    assert registered_user["password"] not in response_text
    assert "$argon2id$" not in response_text
    assert "password_hash" not in response_text
    assert "hashed_password" not in response_text
    assert settings.JWT_SECRET_KEY not in response_text


def test_missing_credentials_returns_422(client: TestClient):
    """
    Test 13: Missing email or password returns HTTP 422 Unprocessable Entity.
    """
    # Missing password
    res1 = client.post("/api/v1/auth/login", json={"email": "test@nit.edu"})
    assert res1.status_code == 422
    assert res1.json()["error"]["code"] == "VALIDATION_ERROR"

    # Missing email
    res2 = client.post("/api/v1/auth/login", json={"password": "Password123#"})
    assert res2.status_code == 422
    assert res2.json()["error"]["code"] == "VALIDATION_ERROR"


def test_malformed_email_rejected_with_422(client: TestClient):
    """
    Test 14: Malformed email string is rejected with HTTP 422.
    """
    res = client.post("/api/v1/auth/login", json={
        "email": "not-an-email",
        "password": "Password123#"
    })
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_expired_token_is_rejected():
    """
    Test 11.1 (JWT Security): Expired token raises ExpiredSignatureError on decode.
    """
    # Generate token that expired 10 minutes ago
    expired_token = create_access_token(
        subject="USR-202609-EXPIRED",
        email="expired@nit.edu",
        role="STUDENT",
        expires_delta=timedelta(minutes=-10)
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_invalid_signature_is_rejected():
    """
    Test 11.2 (JWT Security): Token signed with a different key is rejected with InvalidSignatureError.
    """
    # Forge token using a different secret
    forged_token = jwt.encode(
        {
            "sub": "USR-202609-ATTACK",
            "email": "attacker@nit.edu",
            "role": "ADMIN",
            "type": "access",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        },
        "wrong_fake_secret_key_1234567890",
        algorithm="HS256"
    )

    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(forged_token)


def test_openapi_documentation_includes_login(client: TestClient):
    """
    Test 14 (OpenAPI): POST /api/v1/auth/login appears in OpenAPI documentation.
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "/api/v1/auth/login" in schema["paths"]

    login_path = schema["paths"]["/api/v1/auth/login"]
    assert "post" in login_path
    post_op = login_path["post"]
    assert post_op["summary"] == "User Login"
    assert "200" in post_op["responses"]
    assert "401" in post_op["responses"]
    assert "422" in post_op["responses"]
