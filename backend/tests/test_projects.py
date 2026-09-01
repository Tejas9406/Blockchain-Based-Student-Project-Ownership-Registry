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
def create_test_user(db_session: Session):
    """Helper fixture to create test users with specified roles."""
    def _create(
        email_prefix: str = "user",
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


# ==============================================================================
# 1. Project Creation Tests (POST /api/v1/projects)
# ==============================================================================


def test_student_can_create_project(client: TestClient, create_test_user):
    """Test 1: Authenticated student can create project and receive valid ProjectSummary."""
    user, token = create_test_user("student1", UserRole.STUDENT)

    payload = {
        "title": "Decentralized IPFS Academic Registry",
        "abstract": "A decentralized framework for academic project validation.",
        "category": "WEB3",
        "department": "Computer Science & Engineering",
        "academic_year": "2025-2026",
        "visibility": "PUBLIC",
    }

    response = client.post(
        "/api/v1/projects",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    project_data = data["data"]

    # Verify public ID & slug
    assert project_data["public_id"].startswith("PRJ-")
    assert project_data["slug"] == "decentralized-ipfs-academic-registry"
    assert project_data["title"] == payload["title"]
    assert project_data["abstract"] == payload["abstract"]
    assert project_data["category"] == "WEB3"
    assert project_data["current_lifecycle_stage"] == "IDEA"
    assert project_data["status"] == "ACTIVE"
    assert project_data["visibility"] == "PUBLIC"

    # Verify owner summary
    assert project_data["owner"]["public_id"] == user.public_id
    assert project_data["owner"]["full_name"] == user.full_name

    # Verify meta
    assert "timestamp" in data["meta"]
    assert "request_id" in data["meta"]


def test_faculty_can_create_project(client: TestClient, create_test_user):
    """Test 2: Authenticated faculty member can create project."""
    user, token = create_test_user("faculty1", UserRole.FACULTY)

    payload = {
        "title": "AI Powered Quantum Cryptography",
        "abstract": "Investigation of post-quantum cryptographic primitives.",
        "category": "CYBERSECURITY",
        "department": "Information Technology",
        "academic_year": "2025-2026",
        "visibility": "INSTITUTIONAL",
    }

    response = client.post(
        "/api/v1/projects",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    project_data = response.json()["data"]
    assert project_data["visibility"] == "INSTITUTIONAL"
    assert project_data["owner"]["public_id"] == user.public_id


def test_unauthenticated_project_creation_fails(client: TestClient):
    """Test 3: Unauthenticated request returns 401 Unauthorized."""
    payload = {
        "title": "Unauthorized Project Creation",
        "category": "AI",
        "department": "Computer Science",
        "academic_year": "2025-2026",
    }

    response = client.post("/api/v1/projects", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"


def test_unauthorized_role_project_creation_fails(client: TestClient, create_test_user):
    """Test 4: User with VERIFIER role cannot create projects (403 Forbidden)."""
    user, token = create_test_user("verifier1", UserRole.VERIFIER)

    payload = {
        "title": "Verifier Attempting Creation",
        "category": "AI",
        "department": "Computer Science",
        "academic_year": "2025-2026",
    }

    response = client.post(
        "/api/v1/projects",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"


def test_project_persisted_in_database(client: TestClient, create_test_user, db_session: Session):
    """Test 5: Project and LEAD ProjectMember are correctly persisted in PostgreSQL."""
    user, token = create_test_user("student_db", UserRole.STUDENT)

    payload = {
        "title": "Database Persistence Verification Project",
        "abstract": "Checking database tables and foreign keys.",
        "category": "IOT",
        "department": "Electronics",
        "academic_year": "2025-2026",
        "visibility": "PUBLIC",
    }

    response = client.post(
        "/api/v1/projects",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    pub_id = response.json()["data"]["public_id"]

    # Verify Project in DB
    db_project = db_session.execute(
        select(Project).where(Project.public_id == pub_id)
    ).scalar_one_or_none()

    assert db_project is not None
    assert isinstance(db_project.id, uuid.UUID)
    assert db_project.public_id != str(db_project.id)
    assert db_project.status == ProjectStatus.ACTIVE
    assert db_project.current_lifecycle_stage == ProjectVersionStage.IDEA

    # Verify ProjectMember in DB
    db_member = db_session.execute(
        select(ProjectMember).where(ProjectMember.project_id == db_project.id)
    ).scalar_one_or_none()

    assert db_member is not None
    assert db_member.user_id == user.id
    assert db_member.role_in_project == ProjectMemberRole.LEAD
    assert db_member.is_owner is True
    assert db_member.contribution_percentage == Decimal("100.00")


def test_slug_collision_handling(client: TestClient, create_test_user):
    """Test 6: Multiple projects with identical titles receive unique slugs."""
    _, token1 = create_test_user("stud_slug1", UserRole.STUDENT)
    _, token2 = create_test_user("stud_slug2", UserRole.STUDENT)

    payload = {
        "title": "Smart Solar Energy Management",
        "category": "ENERGY",
        "department": "Electrical Engineering",
        "academic_year": "2025-2026",
    }

    res1 = client.post("/api/v1/projects", json=payload, headers={"Authorization": f"Bearer {token1}"})
    assert res1.status_code == 201
    slug1 = res1.json()["data"]["slug"]
    assert slug1 == "smart-solar-energy-management"

    res2 = client.post("/api/v1/projects", json=payload, headers={"Authorization": f"Bearer {token2}"})
    assert res2.status_code == 201
    slug2 = res2.json()["data"]["slug"]
    assert slug2 == "smart-solar-energy-management-2"

    res3 = client.post("/api/v1/projects", json=payload, headers={"Authorization": f"Bearer {token1}"})
    assert res3.status_code == 201
    slug3 = res3.json()["data"]["slug"]
    assert slug3 == "smart-solar-energy-management-3"

    assert len({slug1, slug2, slug3}) == 3


def test_invalid_project_payload_returns_422(client: TestClient, create_test_user):
    """Test 7: Validation constraints reject malformed payloads."""
    _, token = create_test_user("stud_invalid", UserRole.STUDENT)

    # Empty title
    res_empty_title = client.post(
        "/api/v1/projects",
        json={"title": "   ", "category": "AI", "department": "CS", "academic_year": "2025-2026"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_empty_title.status_code == 422
    assert res_empty_title.json()["error"]["code"] == "VALIDATION_ERROR"

    # Too short title (< 3 chars)
    res_short_title = client.post(
        "/api/v1/projects",
        json={"title": "AB", "category": "AI", "department": "CS", "academic_year": "2025-2026"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_short_title.status_code == 422

    # Missing category
    res_missing_cat = client.post(
        "/api/v1/projects",
        json={"title": "Valid Title Here", "department": "CS", "academic_year": "2025-2026"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_missing_cat.status_code == 422


def test_client_cannot_inject_sensitive_fields(client: TestClient, create_test_user):
    """Test 8: Client-injected status, stage, or ownership fields are ignored or rejected."""
    user, token = create_test_user("stud_tamper", UserRole.STUDENT)

    payload = {
        "title": "Security Tamper Resistance Project",
        "category": "SECURITY",
        "department": "Computer Science",
        "academic_year": "2025-2026",
        "status": "UNDER_DISPUTE",  # Maliciously attempt to set status
        "current_lifecycle_stage": "FINAL",  # Maliciously attempt to bypass stages
        "public_id": "PRJ-SPOOFED-99999",  # Attempt to spoof public ID
        "id": str(uuid.uuid4()),  # Attempt to set internal UUID
    }

    response = client.post(
        "/api/v1/projects",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]

    assert data["status"] == "ACTIVE"
    assert data["current_lifecycle_stage"] == "IDEA"
    assert data["public_id"] != "PRJ-SPOOFED-99999"
    assert "id" not in data


# ==============================================================================
# 2. Project List & Search Tests (GET /api/v1/projects)
# ==============================================================================


def test_list_projects_pagination(client: TestClient, create_test_user):
    """Test 9: Paginated project listing returns correct metadata."""
    _, token = create_test_user("list_user", UserRole.STUDENT)

    # Create 5 projects
    for i in range(5):
        client.post(
            "/api/v1/projects",
            json={
                "title": f"Batch Project Listing Item {i} {uuid.uuid4().hex[:4]}",
                "category": "AI",
                "department": "Computer Science",
                "academic_year": "2025-2026",
                "visibility": "PUBLIC",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    # Request page 1 with page_size 2
    res = client.get("/api/v1/projects?page=1&page_size=2")
    assert res.status_code == 200
    body = res.json()

    assert body["success"] is True
    assert len(body["data"]) == 2
    meta = body["meta"]
    assert meta["page"] == 1
    assert meta["page_size"] == 2
    assert meta["total_items"] >= 5
    assert meta["total_pages"] >= 3
    assert meta["has_next"] is True
    assert meta["has_prev"] is False


def test_list_projects_filters(client: TestClient, create_test_user):
    """Test 10: Filtering by category, department, and search keywords."""
    _, token = create_test_user("filter_user", UserRole.STUDENT)

    tag = uuid.uuid4().hex[:6]
    client.post(
        "/api/v1/projects",
        json={
            "title": f"Bioinformatics Protein Folding {tag}",
            "abstract": "Deep learning models for structural biology.",
            "category": "BIOINFORMATICS",
            "department": "Biotechnology",
            "academic_year": "2025-2026",
            "visibility": "PUBLIC",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    client.post(
        "/api/v1/projects",
        json={
            "title": f"Quantum Teleportation Simulator {tag}",
            "abstract": "Quantum circuit simulation framework.",
            "category": "PHYSICS",
            "department": "Applied Physics",
            "academic_year": "2025-2026",
            "visibility": "PUBLIC",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # 1. Filter by category
    res_cat = client.get("/api/v1/projects?category=BIOINFORMATICS")
    assert res_cat.status_code == 200
    for p in res_cat.json()["data"]:
        assert p["category"] == "BIOINFORMATICS"

    # 2. Filter by department
    res_dept = client.get("/api/v1/projects?department=Applied Physics")
    assert res_dept.status_code == 200
    for p in res_dept.json()["data"]:
        assert p["department"] == "Applied Physics"

    # 3. Search query across title and abstract
    res_search = client.get(f"/api/v1/projects?search={tag}")
    assert res_search.status_code == 200
    assert len(res_search.json()["data"]) == 2

    res_search_specific = client.get("/api/v1/projects?search=Protein")
    assert res_search_specific.status_code == 200
    assert any("Protein" in p["title"] for p in res_search_specific.json()["data"])


def test_list_projects_visibility_isolation(client: TestClient, create_test_user):
    """Test 11: Private projects are hidden from unauthenticated users and other students."""
    owner, owner_token = create_test_user("owner_user", UserRole.STUDENT)
    other, other_token = create_test_user("other_user", UserRole.STUDENT)

    tag = uuid.uuid4().hex[:8]
    res_priv = client.post(
        "/api/v1/projects",
        json={
            "title": f"Top Secret Stealth Project {tag}",
            "category": "DEFENSE",
            "department": "Computer Science",
            "academic_year": "2025-2026",
            "visibility": "PRIVATE",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_priv.status_code == 201

    # Unauthenticated user should NOT see private project
    res_public = client.get(f"/api/v1/projects?search={tag}")
    assert len(res_public.json()["data"]) == 0

    # Other student should NOT see private project
    res_other = client.get(f"/api/v1/projects?search={tag}", headers={"Authorization": f"Bearer {other_token}"})
    assert len(res_other.json()["data"]) == 0

    # Owner SHOULD see their private project
    res_owner = client.get(f"/api/v1/projects?search={tag}", headers={"Authorization": f"Bearer {owner_token}"})
    assert len(res_owner.json()["data"]) == 1
    assert res_owner.json()["data"][0]["visibility"] == "PRIVATE"


# ==============================================================================
# 3. Project Detail Tests (GET /api/v1/projects/{project_identifier})
# ==============================================================================


def test_get_project_by_public_id(client: TestClient, create_test_user):
    """Test 12: Project details retrieved successfully by public ID (PRJ-...)."""
    user, token = create_test_user("detail_user1", UserRole.STUDENT)

    create_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Autonomous Drone Navigation",
            "abstract": "Visual SLAM for indoor quadcopter navigation.",
            "category": "ROBOTICS",
            "department": "Robotics Engineering",
            "academic_year": "2025-2026",
            "visibility": "PUBLIC",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    public_id = create_res.json()["data"]["public_id"]

    # Retrieve by public_id
    detail_res = client.get(f"/api/v1/projects/{public_id}")
    assert detail_res.status_code == 200
    data = detail_res.json()["data"]
    assert data["public_id"] == public_id
    assert data["title"] == "Autonomous Drone Navigation"
    assert data["owner"]["public_id"] == user.public_id


def test_get_project_by_slug(client: TestClient, create_test_user):
    """Test 13: Project details retrieved successfully by URL slug."""
    user, token = create_test_user("detail_user2", UserRole.STUDENT)

    create_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Edge Computing IoT Smart Grid",
            "category": "IOT",
            "department": "Electrical Engineering",
            "academic_year": "2025-2026",
            "visibility": "PUBLIC",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    slug = create_res.json()["data"]["slug"]

    # Retrieve by slug
    detail_res = client.get(f"/api/v1/projects/{slug}")
    assert detail_res.status_code == 200
    data = detail_res.json()["data"]
    assert data["slug"] == slug
    assert data["title"] == "Edge Computing IoT Smart Grid"


def test_get_nonexistent_project_returns_404(client: TestClient):
    """Test 14: Nonexistent public identifier returns 404 Not Found."""
    response = client.get("/api/v1/projects/PRJ-202609-NONEXISTENT")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PROJECT_NOT_FOUND"


def test_private_project_detail_access_control(client: TestClient, create_test_user):
    """Test 15: Private project detail returns 404 for unauthenticated and unauthorized callers."""
    owner, owner_token = create_test_user("priv_owner", UserRole.STUDENT)
    other, other_token = create_test_user("priv_other", UserRole.STUDENT)
    admin, admin_token = create_test_user("priv_admin", UserRole.ADMIN)

    res = client.post(
        "/api/v1/projects",
        json={
            "title": "Proprietary Defense Research",
            "category": "DEFENSE",
            "department": "Cybersecurity",
            "academic_year": "2025-2026",
            "visibility": "PRIVATE",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    pub_id = res.json()["data"]["public_id"]

    # 1. Unauthenticated -> 404
    assert client.get(f"/api/v1/projects/{pub_id}").status_code == 404

    # 2. Other student -> 404
    assert client.get(f"/api/v1/projects/{pub_id}", headers={"Authorization": f"Bearer {other_token}"}).status_code == 404

    # 3. Owner -> 200
    assert client.get(f"/api/v1/projects/{pub_id}", headers={"Authorization": f"Bearer {owner_token}"}).status_code == 200

    # 4. Admin -> 200
    assert client.get(f"/api/v1/projects/{pub_id}", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200


# ==============================================================================
# 4. Security & Privacy Tests
# ==============================================================================


def test_password_and_internal_ids_never_leaked(client: TestClient, create_test_user):
    """Test 16: Project responses never leak internal UUIDs or password hashes."""
    user, token = create_test_user("sec_user", UserRole.STUDENT)

    res = client.post(
        "/api/v1/projects",
        json={
            "title": "Privacy Leakage Test Project",
            "category": "SECURITY",
            "department": "Computer Science",
            "academic_year": "2025-2026",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body_str = res.text

    assert "password" not in body_str
    assert "argon2" not in body_str
    assert str(user.id) not in body_str


# ==============================================================================
# 5. OpenAPI Specification Tests
# ==============================================================================


def test_openapi_documentation_includes_projects(client: TestClient):
    """Test 17: Interactive OpenAPI schema includes all project routes and models."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()

    assert "/api/v1/projects" in spec["paths"]
    assert "post" in spec["paths"]["/api/v1/projects"]
    assert "get" in spec["paths"]["/api/v1/projects"]
    assert "/api/v1/projects/{project_identifier}" in spec["paths"]
    assert "get" in spec["paths"]["/api/v1/projects/{project_identifier}"]
