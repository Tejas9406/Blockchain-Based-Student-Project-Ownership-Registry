from typing import Generator
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
import pytest
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    require_admin,
    require_faculty,
    require_role,
    require_student,
    require_verifier,
)
from app.core.exceptions import AppException
from app.core.security import create_access_token, hash_password
from app.database.session import get_db
from app.main import app as production_app, app_exception_handler
from app.models.user import User
from app.schemas.common import ApiMeta, ApiResponse, get_utc_now_iso
from app.schemas.user import UserRole, UserSummaryResponse


# Define dedicated test-only router with RBAC protections for testing
rbac_test_router = APIRouter(prefix="/test-rbac", tags=["Test RBAC"])


class DummyActionPayload(BaseModel):
    action: str = "submit"
    role: str = "STUDENT"


@rbac_test_router.get("/student-only", response_model=ApiResponse[UserSummaryResponse])
def student_only_endpoint(current_user: User = Depends(require_student)):
    return ApiResponse(
        success=True,
        data=UserSummaryResponse.model_validate(current_user),
        meta=ApiMeta(timestamp=get_utc_now_iso())
    )


@rbac_test_router.get("/faculty-only", response_model=ApiResponse[UserSummaryResponse])
def faculty_only_endpoint(current_user: User = Depends(require_faculty)):
    return ApiResponse(
        success=True,
        data=UserSummaryResponse.model_validate(current_user),
        meta=ApiMeta(timestamp=get_utc_now_iso())
    )


@rbac_test_router.get("/admin-only", response_model=ApiResponse[UserSummaryResponse])
def admin_only_endpoint(current_user: User = Depends(require_admin)):
    return ApiResponse(
        success=True,
        data=UserSummaryResponse.model_validate(current_user),
        meta=ApiMeta(timestamp=get_utc_now_iso())
    )


@rbac_test_router.post("/admin-only-action", response_model=ApiResponse[UserSummaryResponse])
def admin_only_post_endpoint(
    payload: DummyActionPayload,
    current_user: User = Depends(require_admin)
):
    return ApiResponse(
        success=True,
        data=UserSummaryResponse.model_validate(current_user),
        meta=ApiMeta(timestamp=get_utc_now_iso())
    )


@rbac_test_router.get("/verifier-only", response_model=ApiResponse[UserSummaryResponse])
def verifier_only_endpoint(current_user: User = Depends(require_verifier)):
    return ApiResponse(
        success=True,
        data=UserSummaryResponse.model_validate(current_user),
        meta=ApiMeta(timestamp=get_utc_now_iso())
    )


@rbac_test_router.get("/admin-or-faculty", response_model=ApiResponse[UserSummaryResponse])
def admin_or_faculty_endpoint(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.FACULTY))
):
    return ApiResponse(
        success=True,
        data=UserSummaryResponse.model_validate(current_user),
        meta=ApiMeta(timestamp=get_utc_now_iso())
    )


@pytest.fixture(scope="module")
def rbac_app():
    """App fixture with mounted test RBAC router for isolated testing."""
    production_app.include_router(rbac_test_router)
    yield production_app


@pytest.fixture
def rbac_users(db_session: Session) -> dict:
    """Fixture to create users with each of the 4 roles and return their access tokens."""
    roles = {
        "student": ("USR-202609-STU01", "student@nit.edu", "STUDENT"),
        "faculty": ("USR-202609-FAC01", "faculty@nit.edu", "FACULTY"),
        "admin": ("USR-202609-ADM01", "admin@nit.edu", "ADMIN"),
        "verifier": ("USR-202609-VER01", "verifier@nit.edu", "VERIFIER"),
    }
    user_tokens = {}

    for key, (pid, email, role) in roles.items():
        user = User(
            public_id=pid,
            email=email,
            hashed_password=hash_password("Password#2026Secure"),
            full_name=f"{key.capitalize()} User",
            institution_id=f"NIT-2023-{key.upper()}-01",
            department="Computer Science",
            role=role,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(
            subject=user.public_id,
            email=user.email,
            role=user.role
        )
        user_tokens[key] = {
            "user": user,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

    return user_tokens


def test_unauthenticated_request_returns_401(client: TestClient, rbac_app):
    """
    Test 1: Unauthenticated request to protected endpoint returns HTTP 401 Unauthorized.
    """
    response = client.get("/test-rbac/student-only")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_student_access_student_protected_operation(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 2: STUDENT accessing student-protected operation is allowed (200 OK).
    """
    res = client.get("/test-rbac/student-only", headers=rbac_users["student"]["headers"])
    assert res.status_code == 200
    assert res.json()["data"]["role"] == "STUDENT"


def test_faculty_access_faculty_protected_operation(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 3: FACULTY accessing faculty-protected operation is allowed (200 OK).
    """
    res = client.get("/test-rbac/faculty-only", headers=rbac_users["faculty"]["headers"])
    assert res.status_code == 200
    assert res.json()["data"]["role"] == "FACULTY"


def test_admin_access_admin_protected_operation(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 4: ADMIN accessing admin-protected operation is allowed (200 OK).
    """
    res = client.get("/test-rbac/admin-only", headers=rbac_users["admin"]["headers"])
    assert res.status_code == 200
    assert res.json()["data"]["role"] == "ADMIN"


def test_verifier_access_verifier_protected_operation(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 5: VERIFIER accessing verifier-protected operation is allowed (200 OK).
    """
    res = client.get("/test-rbac/verifier-only", headers=rbac_users["verifier"]["headers"])
    assert res.status_code == 200
    assert res.json()["data"]["role"] == "VERIFIER"


def test_student_accessing_admin_operation_returns_403(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 6: STUDENT accessing admin operation is rejected with HTTP 403 Forbidden.
    """
    res = client.get("/test-rbac/admin-only", headers=rbac_users["student"]["headers"])
    assert res.status_code == 403
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "FORBIDDEN"
    assert res.json()["error"]["message"] == "You do not have permission to perform this action."


def test_faculty_accessing_admin_operation_returns_403(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 7: FACULTY accessing admin operation is rejected with HTTP 403 Forbidden.
    """
    res = client.get("/test-rbac/admin-only", headers=rbac_users["faculty"]["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_verifier_accessing_admin_operation_returns_403(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 8: VERIFIER accessing admin operation is rejected with HTTP 403 Forbidden.
    """
    res = client.get("/test-rbac/admin-only", headers=rbac_users["verifier"]["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_student_accessing_faculty_operation_returns_403(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 9: STUDENT accessing faculty-only operation is rejected with HTTP 403 Forbidden.
    """
    res = client.get("/test-rbac/faculty-only", headers=rbac_users["student"]["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_admin_accessing_faculty_only_operation_returns_403(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 10: ADMIN accessing faculty-only operation is rejected with HTTP 403 Forbidden.
    """
    res = client.get("/test-rbac/faculty-only", headers=rbac_users["admin"]["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_multi_role_authorization_behavior(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 11: Multi-role endpoint (ADMIN or FACULTY) accepts both and rejects STUDENT and VERIFIER.
    """
    # ADMIN -> 200 OK
    res_admin = client.get("/test-rbac/admin-or-faculty", headers=rbac_users["admin"]["headers"])
    assert res_admin.status_code == 200

    # FACULTY -> 200 OK
    res_faculty = client.get("/test-rbac/admin-or-faculty", headers=rbac_users["faculty"]["headers"])
    assert res_faculty.status_code == 200

    # STUDENT -> 403 Forbidden
    res_student = client.get("/test-rbac/admin-or-faculty", headers=rbac_users["student"]["headers"])
    assert res_student.status_code == 403
    assert res_student.json()["error"]["code"] == "FORBIDDEN"

    # VERIFIER -> 403 Forbidden
    res_verifier = client.get("/test-rbac/admin-or-faculty", headers=rbac_users["verifier"]["headers"])
    assert res_verifier.status_code == 403
    assert res_verifier.json()["error"]["code"] == "FORBIDDEN"


def test_anti_spoofing_via_request_body(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 12: Authenticated STUDENT sending role=ADMIN in request body still receives 403.
    """
    headers = dict(rbac_users["student"]["headers"])
    res = client.post("/test-rbac/admin-only-action", headers=headers, json={"action": "delete_all", "role": "ADMIN"})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_anti_spoofing_via_query_parameter(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 13: Authenticated STUDENT sending ?role=ADMIN in query parameters still receives 403.
    """
    headers = dict(rbac_users["student"]["headers"])
    res = client.get("/test-rbac/admin-only?role=ADMIN", headers=headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_anti_spoofing_via_custom_header(client: TestClient, rbac_users: dict, rbac_app):
    """
    Test 14: Authenticated STUDENT sending X-Role: ADMIN in headers still receives 403.
    """
    headers = dict(rbac_users["student"]["headers"])
    headers["X-Role"] = "ADMIN"
    headers["X-User-Role"] = "ADMIN"
    res = client.get("/test-rbac/admin-only", headers=headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_invalid_jwt_remains_401(client: TestClient, rbac_app):
    """
    Test 15: Invalid/malformed JWT returns 401, not 403.
    """
    res = client.get("/test-rbac/admin-only", headers={"Authorization": "Bearer invalid.jwt"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_TOKEN"
