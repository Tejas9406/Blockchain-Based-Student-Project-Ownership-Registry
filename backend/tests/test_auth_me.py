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
)
from app.models.user import User


@pytest.fixture
def auth_user(client: TestClient) -> dict:
    """Helper fixture to register and login a user, returning user data and tokens."""
    payload = {
        "email": "me.tester@nit.edu",
        "password": "Password#2026Secure",
        "full_name": "Me Endpoint Tester",
        "institution_id": "NIT-2023-CS-300",
        "institution_name": "National Institute of Technology",
        "department": "Computer Science & Engineering",
        "role": "STUDENT",
        "wallet_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    }
    reg_res = client.post("/api/v1/auth/register", json=payload)
    assert reg_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", json={
        "email": payload["email"],
        "password": payload["password"]
    })
    assert login_res.status_code == 200

    return {
        "user_payload": payload,
        "public_id": login_res.json()["data"]["user"]["public_id"],
        "access_token": login_res.json()["data"]["access_token"],
        "refresh_token": login_res.json()["data"]["refresh_token"],
    }


def test_get_me_successful(client: TestClient, auth_user: dict):
    """
    Test 1, 2, 15, 16, 17: Valid access token returns 200 OK and current user profile in universal envelope.
    """
    headers = {
        "Authorization": f"Bearer {auth_user['access_token']}"
    }

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "meta" in data
    assert "timestamp" in data["meta"]
    assert "request_id" in data["meta"]

    user_info = data["data"]
    assert user_info["public_id"] == auth_user["public_id"]
    assert user_info["email"] == auth_user["user_payload"]["email"]
    assert user_info["full_name"] == auth_user["user_payload"]["full_name"]
    assert user_info["role"] == "STUDENT"
    assert user_info["institution_id"] == auth_user["user_payload"]["institution_id"]
    assert user_info["department"] == auth_user["user_payload"]["department"]


def test_missing_authorization_header_returns_401(client: TestClient):
    """
    Test 3: Request without Authorization header returns HTTP 401 Unauthorized.
    """
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_malformed_authorization_header_returns_401(client: TestClient, auth_user: dict):
    """
    Test 4: Malformed Authorization headers return HTTP 401 Unauthorized.
    """
    # Missing 'Bearer ' prefix
    res1 = client.get("/api/v1/auth/me", headers={"Authorization": auth_user["access_token"]})
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "INVALID_TOKEN"

    # Unsupported scheme (Basic)
    res2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Basic {auth_user['access_token']}"})
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "INVALID_TOKEN"

    # Empty token string
    res3 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer "})
    assert res3.status_code == 401
    assert res3.json()["error"]["code"] == "INVALID_TOKEN"


def test_invalid_jwt_returns_401(client: TestClient):
    """
    Test 5: Completely invalid JWT token returns HTTP 401 Unauthorized.
    """
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_expired_jwt_returns_401(client: TestClient, auth_user: dict):
    """
    Test 6: Expired JWT access token returns HTTP 401 Unauthorized.
    """
    expired_token = create_access_token(
        subject=auth_user["public_id"],
        email=auth_user["user_payload"]["email"],
        role="STUDENT",
        expires_delta=timedelta(seconds=-10)
    )

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_tampered_jwt_returns_401(client: TestClient, auth_user: dict):
    """
    Test 7: Tampered JWT signature returns HTTP 401 Unauthorized.
    """
    tampered_token = auth_user["access_token"][:-4] + "ZZZZ"
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_refresh_token_used_at_me_returns_401(client: TestClient, auth_user: dict):
    """
    Test 8 & Security Test: Using a refresh token (type='refresh') at /me is rejected.
    """
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_user['refresh_token']}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_nonexistent_user_token_returns_401(client: TestClient):
    """
    Test 9: Valid token signature referencing a non-existent user returns HTTP 401.
    """
    orphan_token = create_access_token(
        subject="USR-202609-NONEXISTENT",
        email="ghost@nit.edu",
        role="STUDENT"
    )

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {orphan_token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_inactive_user_token_returns_401(client: TestClient, auth_user: dict, db_session: Session):
    """
    Test 10: Inactive user account is rejected even with a valid access token.
    """
    user = db_session.execute(
        select(User).where(User.public_id == auth_user["public_id"])
    ).scalar_one()
    user.is_active = False
    db_session.commit()

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_user['access_token']}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_sensitive_data_not_exposed_in_me_response(client: TestClient, auth_user: dict, db_session: Session):
    """
    Test 11, 12, 13, 14: Internal UUID, passwords, password hashes, refresh tokens, and secrets are never in /me.
    """
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_user['access_token']}"})
    assert response.status_code == 200

    db_user = db_session.execute(
        select(User).where(User.public_id == auth_user["public_id"])
    ).scalar_one()

    internal_uuid = str(db_user.id)
    response_text = response.text

    assert internal_uuid not in response_text
    assert "password" not in response.json()["data"]
    assert "hashed_password" not in response_text
    assert "$argon2id$" not in response_text
    assert auth_user["refresh_token"] not in response_text
    assert settings.JWT_SECRET_KEY not in response_text


def test_identity_cannot_be_spoofed_via_query_or_body(client: TestClient, auth_user: dict, db_session: Session):
    """
    Test 9 (Security): Request cannot spoof identity using query parameters or headers.
    """
    # Create another victim user
    victim_payload = {
        "email": "victim@nit.edu",
        "password": "Password#2026Victim",
        "full_name": "Victim User",
        "institution_id": "NIT-2023-CS-301",
        "department": "Computer Science & Engineering"
    }
    client.post("/api/v1/auth/register", json=victim_payload)
    victim = db_session.execute(select(User).where(User.email == "victim@nit.edu")).scalar_one()

    # Attacker calls /me with attacker's token, but attempts to spoof victim ID in params
    headers = {
        "Authorization": f"Bearer {auth_user['access_token']}",
        "X-User-ID": victim.public_id
    }
    params = {
        "user_id": victim.public_id,
        "email": victim.email
    }

    response = client.get("/api/v1/auth/me", headers=headers, params=params)
    assert response.status_code == 200
    # Must strictly return attacker's profile from the JWT, never the spoofed victim
    assert response.json()["data"]["public_id"] == auth_user["public_id"]
    assert response.json()["data"]["email"] == auth_user["user_payload"]["email"]


def test_openapi_documentation_includes_me(client: TestClient):
    """
    Test 18: GET /api/v1/auth/me appears in OpenAPI documentation.
    """
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "/api/v1/auth/me" in schema["paths"]

    me_path = schema["paths"]["/api/v1/auth/me"]
    assert "get" in me_path
    get_op = me_path["get"]
    assert get_op["summary"] == "Get Current User Profile"
    assert "200" in get_op["responses"]
    assert "401" in get_op["responses"]
