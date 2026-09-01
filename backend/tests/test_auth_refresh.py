from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.models.user import User


@pytest.fixture
def auth_tokens(client: TestClient) -> dict:
    """Helper fixture to register and login a test user, returning access and refresh tokens."""
    user_payload = {
        "email": "refresh.tester@nit.edu",
        "password": "CorrectPassword#2026",
        "full_name": "Refresh Tester",
        "institution_id": "NIT-2023-CS-200",
        "institution_name": "National Institute of Technology",
        "department": "Computer Science & Engineering",
        "role": "STUDENT",
        "wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    }
    reg_res = client.post("/api/v1/auth/register", json=user_payload)
    assert reg_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", json={
        "email": user_payload["email"],
        "password": user_payload["password"]
    })
    assert login_res.status_code == 200

    return {
        "user_payload": user_payload,
        "public_id": login_res.json()["data"]["user"]["public_id"],
        "access_token": login_res.json()["data"]["access_token"],
        "refresh_token": login_res.json()["data"]["refresh_token"],
    }


def test_valid_refresh_token_returns_new_access_and_refresh_tokens(client: TestClient, auth_tokens: dict):
    """
    Test 1, 9, 10: Valid refresh token returns HTTP 200, newly minted access token with fresh exp, and rotated refresh token.
    """
    refresh_payload = {
        "refresh_token": auth_tokens["refresh_token"]
    }

    response = client.post("/api/v1/auth/refresh", json=refresh_payload)
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

    new_access_token = token_data["access_token"]
    new_refresh_token = token_data["refresh_token"]

    # Decode and verify the new access token
    decoded_access = decode_access_token(new_access_token)
    assert decoded_access["sub"] == auth_tokens["public_id"]
    assert decoded_access["email"] == auth_tokens["user_payload"]["email"]
    assert decoded_access["role"] == "STUDENT"
    assert decoded_access["type"] == "access"
    assert decoded_access["exp"] > decoded_access["iat"]

    # Decode and verify the rotated refresh token
    decoded_refresh = decode_refresh_token(new_refresh_token)
    assert decoded_refresh["sub"] == auth_tokens["public_id"]
    assert decoded_refresh["email"] == auth_tokens["user_payload"]["email"]
    assert decoded_refresh["role"] == "STUDENT"
    assert decoded_refresh["type"] == "refresh"
    assert "jti" in decoded_refresh


def test_token_type_distinction(auth_tokens: dict):
    """
    Test 2: Access tokens and refresh tokens have distinct 'type' claims.
    """
    decoded_access = decode_access_token(auth_tokens["access_token"])
    decoded_refresh = decode_refresh_token(auth_tokens["refresh_token"])

    assert decoded_access["type"] == "access"
    assert decoded_refresh["type"] == "refresh"


def test_access_token_cannot_be_used_at_refresh_endpoint(client: TestClient, auth_tokens: dict):
    """
    Test 3 & Security Test: Access token presented at /refresh is rejected with HTTP 401 INVALID_TOKEN.
    """
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": auth_tokens["access_token"]  # Misuse access token as refresh token
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_expired_refresh_token_is_rejected(client: TestClient, auth_tokens: dict):
    """
    Test 4: Expired refresh token is rejected with HTTP 401 INVALID_TOKEN.
    """
    expired_refresh_token = create_refresh_token(
        subject=auth_tokens["public_id"],
        email=auth_tokens["user_payload"]["email"],
        role="STUDENT",
        expires_delta=timedelta(seconds=-1)
    )

    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": expired_refresh_token
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_malformed_refresh_token_is_rejected(client: TestClient):
    """
    Test 5: Malformed token string is rejected with HTTP 401 INVALID_TOKEN.
    """
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": "not.a.valid.jwt.token"
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_tampered_refresh_token_is_rejected(client: TestClient, auth_tokens: dict):
    """
    Test 6: Tampered JWT payload/signature is rejected with HTTP 401 INVALID_TOKEN.
    """
    valid_token = auth_tokens["refresh_token"]
    tampered_token = valid_token[:-4] + "XXXX"

    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": tampered_token
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_wrong_signing_key_is_rejected(client: TestClient, auth_tokens: dict):
    """
    Test 7: Token signed with a foreign secret is rejected with HTTP 401 INVALID_TOKEN.
    """
    forged_token = jwt.encode(
        {
            "sub": auth_tokens["public_id"],
            "email": auth_tokens["user_payload"]["email"],
            "role": "STUDENT",
            "type": "refresh",
            "jti": "fake_jti_123456",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(days=7)).timestamp())
        },
        "attacker_unauthorized_key_99999_32bytes",
        algorithm="HS256"
    )

    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": forged_token
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_nonexistent_user_refresh_is_rejected(client: TestClient):
    """
    Test 8: Refresh token with a valid signature but non-existent user public_id is rejected.
    """
    orphan_token = create_refresh_token(
        subject="USR-202609-00000",
        email="ghost@nit.edu",
        role="STUDENT"
    )

    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": orphan_token
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_inactive_user_refresh_is_rejected(client: TestClient, auth_tokens: dict, db_session: Session):
    """
    Test 8.2: Deactivated user account cannot refresh access tokens.
    """
    # Deactivate user in database
    user = db_session.execute(
        select(User).where(User.public_id == auth_tokens["public_id"])
    ).scalar_one()
    user.is_active = False
    db_session.commit()

    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"]
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_sensitive_data_not_exposed_in_refresh_response(client: TestClient, auth_tokens: dict):
    """
    Test 11 & 12: Password, password_hash, and JWT secret are never exposed in response.
    """
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"]
    })
    assert response.status_code == 200

    response_text = response.text
    assert auth_tokens["user_payload"]["password"] not in response_text
    assert "$argon2id$" not in response_text
    assert "password_hash" not in response_text
    assert "hashed_password" not in response_text
    assert settings.JWT_SECRET_KEY not in response_text


def test_missing_or_empty_refresh_token_payload(client: TestClient):
    """
    Test 14 & 15: Missing or empty refresh_token field returns HTTP 422.
    """
    # Missing payload field
    res1 = client.post("/api/v1/auth/refresh", json={})
    assert res1.status_code == 422
    assert res1.json()["error"]["code"] == "VALIDATION_ERROR"

    # Empty string
    res2 = client.post("/api/v1/auth/refresh", json={"refresh_token": ""})
    assert res2.status_code == 422
    assert res2.json()["error"]["code"] == "VALIDATION_ERROR"


def test_token_rotation_allows_continuous_refresh(client: TestClient, auth_tokens: dict):
    """
    Test 16: The newly rotated refresh token can be used for subsequent token refreshes.
    """
    # 1st Refresh
    res1 = client.post("/api/v1/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"]
    })
    assert res1.status_code == 200
    rotated_refresh_token = res1.json()["data"]["refresh_token"]

    # 2nd Refresh using the rotated refresh token
    res2 = client.post("/api/v1/auth/refresh", json={
        "refresh_token": rotated_refresh_token
    })
    assert res2.status_code == 200
    assert "access_token" in res2.json()["data"]


def test_openapi_documentation_includes_refresh(client: TestClient):
    """
    Test 17: POST /api/v1/auth/refresh appears in OpenAPI documentation.
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "/api/v1/auth/refresh" in schema["paths"]

    refresh_path = schema["paths"]["/api/v1/auth/refresh"]
    assert "post" in refresh_path
    post_op = refresh_path["post"]
    assert post_op["summary"] == "Refresh Access Token"
    assert "200" in post_op["responses"]
    assert "401" in post_op["responses"]
    assert "422" in post_op["responses"]
