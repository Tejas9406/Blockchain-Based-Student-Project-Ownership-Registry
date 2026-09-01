import uuid
from decimal import Decimal
from typing import Tuple
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.enums import (
    ProjectMemberRole,
    ProjectStatus,
    ProjectVersionStage,
    ProjectVisibility,
    UserRole,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User


@pytest.fixture
def create_member_test_user(db_session: Session):
    """Helper fixture to create test users with specified roles."""
    def _create(
        email_prefix: str = "member_user",
        role: UserRole = UserRole.STUDENT,
        department: str = "Computer Science",
    ) -> Tuple[User, str]:
        unique_id = uuid.uuid4().hex[:6]
        user = User(
            public_id=f"USR-202609-{unique_id[:5].upper()}",
            email=f"{email_prefix}_{unique_id}@sih2026.edu",
            hashed_password=hash_password("SecurePass123!"),
            full_name=f"Test {email_prefix.capitalize()}",
            institution_id=f"INST-{unique_id.upper()}",
            department=department,
            role=role,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(
            subject=user.public_id,
            role=user.role.value if isinstance(user.role, UserRole) else str(user.role),
            email=user.email,
        )
        return user, token

    return _create


@pytest.fixture
def create_test_project(client: TestClient, create_member_test_user):
    """Helper fixture to create a project with a lead/owner."""
    def _create(
        owner_prefix: str = "proj_owner",
        visibility: str = "PUBLIC",
        title: str = "Autonomous Decentralized Mesh",
    ) -> Tuple[User, str, str, str]:
        owner, owner_token = create_member_test_user(owner_prefix, UserRole.STUDENT)
        res = client.post(
            "/api/v1/projects",
            json={
                "title": f"{title} {uuid.uuid4().hex[:4]}",
                "abstract": "Decentralized mesh networks test project.",
                "category": "NETWORKING",
                "department": "Computer Science",
                "academic_year": "2025-2026",
                "visibility": visibility,
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res.status_code == 201
        data = res.json()["data"]
        return owner, owner_token, data["public_id"], data["slug"]

    return _create


# ==============================================================================
# 1. List Members Tests (GET /api/v1/projects/{project_id}/members)
# ==============================================================================


def test_list_members_for_public_project(client: TestClient, create_test_project, create_member_test_user):
    """Test 1: Public project members can be listed without authentication."""
    owner, owner_token, public_id, _ = create_test_project(visibility="PUBLIC")
    contributor, _ = create_member_test_user("contrib1", UserRole.STUDENT)

    # Add contributor
    add_res = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={
            "user_public_id": contributor.public_id,
            "role_in_project": "CONTRIBUTOR",
            "contribution_percentage": 25.50,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert add_res.status_code == 201

    # Unauthenticated list request
    list_res = client.get(f"/api/v1/projects/{public_id}/members")
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["success"] is True
    members = body["data"]

    assert len(members) == 2
    # Verify owner is first and marked as owner
    assert members[0]["user"]["public_id"] == owner.public_id
    assert members[0]["is_owner"] is True
    assert members[0]["role_in_project"] == "LEAD"

    # Verify contributor
    assert members[1]["user"]["public_id"] == contributor.public_id
    assert members[1]["is_owner"] is False
    assert members[1]["role_in_project"] == "CONTRIBUTOR"
    assert members[1]["contribution_percentage"] == 25.50


def test_list_members_nonexistent_project_returns_404(client: TestClient):
    """Test 2: Listing members for nonexistent project returns 404."""
    res = client.get("/api/v1/projects/PRJ-202609-NONEXIST/members")
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "PROJECT_NOT_FOUND"


def test_list_members_private_project_access_control(client: TestClient, create_test_project, create_member_test_user):
    """Test 3: Private project members are hidden from unauthorized callers."""
    owner, owner_token, public_id, _ = create_test_project(visibility="PRIVATE")
    other_user, other_token = create_member_test_user("unauth_student", UserRole.STUDENT)
    admin, admin_token = create_member_test_user("sysadmin", UserRole.ADMIN)

    # 1. Unauthenticated caller -> 404
    assert client.get(f"/api/v1/projects/{public_id}/members").status_code == 404

    # 2. Other student -> 404
    assert client.get(
        f"/api/v1/projects/{public_id}/members",
        headers={"Authorization": f"Bearer {other_token}"}
    ).status_code == 404

    # 3. Project Owner -> 200
    res_owner = client.get(
        f"/api/v1/projects/{public_id}/members",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert res_owner.status_code == 200
    assert len(res_owner.json()["data"]) == 1

    # 4. Admin -> 200
    res_admin = client.get(
        f"/api/v1/projects/{public_id}/members",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200


# ==============================================================================
# 2. Add / Invite Member Tests (POST /api/v1/projects/{project_id}/members)
# ==============================================================================


def test_project_owner_can_add_student_contributor(client: TestClient, create_test_project, create_member_test_user):
    """Test 4: Project owner can add a valid student contributor by user_public_id."""
    owner, owner_token, public_id, _ = create_test_project()
    student, _ = create_member_test_user("student_c1", UserRole.STUDENT)

    res = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={
            "user_public_id": student.public_id,
            "role_in_project": "CONTRIBUTOR",
            "contribution_percentage": 30.00,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    member_data = body["data"]

    assert member_data["user"]["public_id"] == student.public_id
    assert member_data["user"]["email"] == student.email
    assert member_data["role_in_project"] == "CONTRIBUTOR"
    assert member_data["contribution_percentage"] == 30.00
    assert member_data["is_owner"] is False


def test_project_owner_can_add_faculty_mentor_by_email(client: TestClient, create_test_project, create_member_test_user):
    """Test 5: Project owner can add a faculty mentor by email address."""
    owner, owner_token, public_id, _ = create_test_project()
    faculty, _ = create_member_test_user("prof_mentor", UserRole.FACULTY)

    res = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={
            "email": faculty.email,
            "role_in_project": "FACULTY_MENTOR",
            "contribution_percentage": 0.00,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 201
    member_data = res.json()["data"]
    assert member_data["user"]["public_id"] == faculty.public_id
    assert member_data["role_in_project"] == "FACULTY_MENTOR"
    assert member_data["is_owner"] is False


def test_admin_can_add_member(client: TestClient, create_test_project, create_member_test_user):
    """Test 6: System Administrator is authorized to add members to any project."""
    _, _, public_id, _ = create_test_project()
    admin, admin_token = create_member_test_user("admin_user", UserRole.ADMIN)
    student, _ = create_member_test_user("student_by_admin", UserRole.STUDENT)

    res = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={
            "user_public_id": student.public_id,
            "role_in_project": "CONTRIBUTOR",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert res.status_code == 201
    assert res.json()["data"]["user"]["public_id"] == student.public_id


def test_unauthenticated_add_member_fails(client: TestClient, create_test_project, create_member_test_user):
    """Test 7: Unauthenticated request to add member returns 401 Unauthorized."""
    _, _, public_id, _ = create_test_project()
    student, _ = create_member_test_user("stud_unauth", UserRole.STUDENT)

    res = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": student.public_id},
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_TOKEN"


def test_non_owner_add_member_forbidden(client: TestClient, create_test_project, create_member_test_user):
    """Test 8: Non-owner user cannot add members (403 Forbidden)."""
    _, _, public_id, _ = create_test_project()
    unauth_student, unauth_token = create_member_test_user("unauth_student", UserRole.STUDENT)
    target_student, _ = create_member_test_user("target_student", UserRole.STUDENT)

    res = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": target_student.public_id},
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_add_member_to_nonexistent_project_fails(client: TestClient, create_member_test_user):
    """Test 9: Adding member to nonexistent project returns 404."""
    owner, owner_token = create_member_test_user("owner_ghost", UserRole.STUDENT)
    student, _ = create_member_test_user("stud_ghost", UserRole.STUDENT)

    res = client.post(
        "/api/v1/projects/PRJ-202609-NOTREAL/members",
        json={"user_public_id": student.public_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_add_nonexistent_user_fails(client: TestClient, create_test_project):
    """Test 10: Adding nonexistent user returns 404 USER_NOT_FOUND."""
    _, owner_token, public_id, _ = create_test_project()

    res = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": "USR-202609-NONEXISTENT"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "USER_NOT_FOUND"


def test_duplicate_membership_rejected_with_409(client: TestClient, create_test_project, create_member_test_user):
    """Test 11: Attempting to add an existing member returns 409 Conflict."""
    owner, owner_token, public_id, _ = create_test_project()
    student, _ = create_member_test_user("duplicate_stud", UserRole.STUDENT)

    # 1. First addition succeeds
    res1 = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": student.public_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res1.status_code == 201

    # 2. Second addition fails with 409
    res2 = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": student.public_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "MEMBER_ALREADY_EXISTS"

    # 3. Owner adding themselves also fails with 409
    res_self = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": owner.public_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_self.status_code == 409
    assert res_self.json()["error"]["code"] == "MEMBER_ALREADY_EXISTS"


def test_invalid_member_payload_rejected(client: TestClient, create_test_project, create_member_test_user):
    """Test 12: Missing identifiers, invalid role, or out-of-range percentage returns 422."""
    _, owner_token, public_id, _ = create_test_project()
    student, _ = create_member_test_user("valid_stud", UserRole.STUDENT)

    # 1. Missing both user_public_id and email
    res_no_id = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"role_in_project": "CONTRIBUTOR"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_no_id.status_code == 422

    # 2. Invalid role
    res_bad_role = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": student.public_id, "role_in_project": "SUPER_ADMIN"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_bad_role.status_code == 422

    # 3. Contribution percentage > 100
    res_high_pct = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": student.public_id, "contribution_percentage": 150.00},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_high_pct.status_code == 422

    # 4. Contribution percentage < 0
    res_neg_pct = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": student.public_id, "contribution_percentage": -10.00},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_neg_pct.status_code == 422


def test_ownership_preserved_on_member_addition(client: TestClient, create_test_project, create_member_test_user, db_session: Session):
    """Test 13: Project ownership remains strictly with creator and cannot be overwritten."""
    owner, owner_token, public_id, _ = create_test_project()
    student, _ = create_member_test_user("ownership_test_stud", UserRole.STUDENT)

    # Attempt to spoof owner or lead role
    res = client.post(
        f"/api/v1/projects/{public_id}/members",
        json={
            "user_public_id": student.public_id,
            "role_in_project": "LEAD",
            "is_owner": True,  # Client attempting to spoof ownership flag
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 201
    assert res.json()["data"]["is_owner"] is False

    # Check database directly
    db_project = db_session.execute(
        select(Project).where(Project.public_id == public_id)
    ).scalar_one()

    members = db_session.execute(
        select(ProjectMember).where(ProjectMember.project_id == db_project.id)
    ).scalars().all()

    assert len(members) == 2
    owner_members = [m for m in members if m.is_owner is True]
    assert len(owner_members) == 1
    assert owner_members[0].user_id == owner.id


# ==============================================================================
# 3. Security & Response Isolation Tests
# ==============================================================================


def test_no_sensitive_fields_leaked_in_member_responses(client: TestClient, create_test_project, create_member_test_user):
    """Test 14: Member responses strictly omit passwords, hashes, and internal UUIDs."""
    owner, owner_token, public_id, _ = create_test_project()
    student, _ = create_member_test_user("sec_member_stud", UserRole.STUDENT)

    client.post(
        f"/api/v1/projects/{public_id}/members",
        json={"user_public_id": student.public_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    list_res = client.get(f"/api/v1/projects/{public_id}/members")
    assert list_res.status_code == 200
    raw_text = list_res.text

    assert "password" not in raw_text
    assert "argon2" not in raw_text
    assert str(owner.id) not in raw_text
    assert str(student.id) not in raw_text


# ==============================================================================
# 4. OpenAPI Documentation Tests
# ==============================================================================


def test_openapi_includes_project_members_endpoints(client: TestClient):
    """Test 15: Interactive OpenAPI schema documents GET and POST project member endpoints."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    spec = res.json()

    assert "/api/v1/projects/{project_id}/members" in spec["paths"]
    path_item = spec["paths"]["/api/v1/projects/{project_id}/members"]
    assert "get" in path_item
    assert "post" in path_item
