import re
import uuid
from typing import Tuple
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.artifact import Artifact
from app.models.blockchain_record import BlockchainRecord
from app.models.enums import (
    ArtifactCategory,
    ProjectMemberRole,
    ProjectStatus,
    ProjectVersionStage,
    ProjectVisibility,
    UserRole,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_version import ProjectVersion
from app.models.user import User


@pytest.fixture
def create_version_test_user(db_session: Session):
    """Helper fixture to create test users with specified roles."""
    def _create(
        email_prefix: str = "ver_user",
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
def create_test_project_with_owner(client: TestClient, create_version_test_user):
    """Helper fixture to create a project with a lead/owner."""
    def _create(
        owner_prefix: str = "proj_owner",
        visibility: str = "PUBLIC",
        title: str = "Academic Blockchain Registry",
    ) -> Tuple[User, str, str, str]:
        owner, owner_token = create_version_test_user(owner_prefix, UserRole.STUDENT)
        res = client.post(
            "/api/v1/projects",
            json={
                "title": f"{title} {uuid.uuid4().hex[:4]}",
                "abstract": "Academic Registry verification milestone project.",
                "category": "CYBERSECURITY",
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
# 1. Create Version Tests (POST /api/v1/projects/{project_id}/versions)
# ==============================================================================


def test_authorized_owner_can_create_valid_version(client: TestClient, create_test_project_with_owner):
    """Test 1: Project owner can create a valid initial version snapshot."""
    owner, owner_token, project_id, _ = create_test_project_with_owner()

    response = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "DESIGN",
            "title": "System Architecture & Threat Model",
            "description": "Initial design specs and threat model.",
            "artifact_ids": [],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    data = body["data"]

    # Validate server-generated public ID and registration ID formats
    assert data["public_id"].startswith("VER-")
    assert re.match(r"^VER-\d{6}-[0-9A-F]{5}$", data["public_id"])
    assert data["registration_id"].startswith("REG-")
    assert re.match(r"^REG-[0-9]{4}-[A-Z0-9]{5}$", data["registration_id"])
    assert len(data["registration_id"].split("-")[2]) == 5

    # Validate version attributes
    assert data["version_index"] == 1
    assert data["version_tag"] == "v1.0"
    assert data["lifecycle_stage"] == "DESIGN"
    assert data["title"] == "System Architecture & Threat Model"
    assert data["description"] == "Initial design specs and threat model."
    assert data["anchoring_status"] == "PENDING"
    assert data["dispute_status"] == "NONE"
    assert data["composite_sha256"] is None
    assert data["ipfs_root_cid"] is None
    assert data["blockchain_record"] is None
    assert "created_at" in data

    # Ensure internal database UUID is not exposed
    assert "id" not in data
    assert "project_id" not in data


def test_admin_can_create_version_for_any_project(
    client: TestClient, create_test_project_with_owner, create_version_test_user
):
    """Test 2: Platform administrator can create a version milestone."""
    _, _, project_id, _ = create_test_project_with_owner()
    admin_user, admin_token = create_version_test_user("platform_admin", UserRole.ADMIN)

    response = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "IDEA",
            "title": "Admin Created Milestone",
            "description": "Milestone injected by institutional admin.",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["version_index"] == 1
    assert data["title"] == "Admin Created Milestone"


def test_unauthenticated_version_creation_fails(client: TestClient, create_test_project_with_owner):
    """Test 3: Unauthenticated request to create version returns 401."""
    _, _, project_id, _ = create_test_project_with_owner()

    response = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "DESIGN",
            "title": "Unauthorized Milestone",
        },
    )
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_unauthorized_student_received_403(
    client: TestClient, create_test_project_with_owner, create_version_test_user
):
    """Test 4: Authenticated student who does not own/lead the project receives 403."""
    _, _, project_id, _ = create_test_project_with_owner()
    other_student, other_token = create_version_test_user("other_student", UserRole.STUDENT)

    response = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "DESIGN",
            "title": "Attacker Milestone",
        },
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"


def test_contributor_without_lead_or_owner_receives_403(
    client: TestClient, create_test_project_with_owner, create_version_test_user
):
    """Test 5: Team member with CONTRIBUTOR role (not LEAD or owner) receives 403."""
    _, owner_token, project_id, _ = create_test_project_with_owner()
    contributor, contrib_token = create_version_test_user("team_contributor", UserRole.STUDENT)

    # Add contributor
    add_res = client.post(
        f"/api/v1/projects/{project_id}/members",
        json={
            "user_public_id": contributor.public_id,
            "role_in_project": "CONTRIBUTOR",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert add_res.status_code == 201

    # Contributor attempts version creation
    version_res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "DESIGN",
            "title": "Contributor Milestone",
        },
        headers={"Authorization": f"Bearer {contrib_token}"},
    )
    assert version_res.status_code == 403
    assert version_res.json()["error"]["code"] == "FORBIDDEN"


def test_nonexistent_project_returns_404(client: TestClient, create_version_test_user):
    """Test 6: Creating a version for a non-existent project returns 404."""
    _, token = create_version_test_user("student_user", UserRole.STUDENT)

    response = client.post(
        "/api/v1/projects/PRJ-202609-99999/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "DESIGN",
            "title": "Ghost Project Milestone",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_invalid_lifecycle_stage_returns_422(client: TestClient, create_test_project_with_owner):
    """Test 7: Invalid lifecycle stage string is rejected with 422."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    response = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "INVALID_STAGE_XYZ",
            "title": "Bad Stage Version",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 422


def test_empty_or_whitespace_fields_rejected_with_422(client: TestClient, create_test_project_with_owner):
    """Test 8: Whitespace-only title or version tag returns 422."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    res1 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "   ",
            "lifecycle_stage": "DESIGN",
            "title": "Valid Title",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res1.status_code == 422

    res2 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "DESIGN",
            "title": "   ",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res2.status_code == 422


def test_sequential_version_indexing_and_no_duplicates(
    client: TestClient, create_test_project_with_owner
):
    """Test 9: Successive versions automatically receive strictly sequential version indices."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    v1_res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "IDEA",
            "title": "Initial Idea",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert v1_res.status_code == 201
    assert v1_res.json()["data"]["version_index"] == 1

    v2_res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.1",
            "lifecycle_stage": "DESIGN",
            "title": "Design Specs",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert v2_res.status_code == 201
    assert v2_res.json()["data"]["version_index"] == 2


def test_registration_id_uniqueness_and_format(client: TestClient, create_test_project_with_owner):
    """Test 10: Registration IDs are unique and follow REG-YYYY-XXXXX."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    v1 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "Milestone 1"},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["data"]

    v2 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v2.0", "lifecycle_stage": "DESIGN", "title": "Milestone 2"},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["data"]

    assert v1["registration_id"] != v2["registration_id"]
    assert v1["registration_id"].startswith("REG-")
    assert v2["registration_id"].startswith("REG-")
    assert re.match(r"^REG-[0-9]{4}-[A-Z0-9]{5}$", v1["registration_id"])
    assert re.match(r"^REG-[0-9]{4}-[A-Z0-9]{5}$", v2["registration_id"])
    assert len(v1["registration_id"].split("-")[2]) == 5
    assert len(v2["registration_id"].split("-")[2]) == 5


def test_client_cannot_tamper_with_system_controlled_fields(
    client: TestClient, create_test_project_with_owner
):
    """Test 11: Client cannot spoof internal ID, registration ID, timestamps, or anchoring status."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    malicious_payload = {
        "id": str(uuid.uuid4()),
        "registration_id": "REG-1999-FAKE01",
        "version_tag": "v1.0",
        "lifecycle_stage": "DESIGN",
        "title": "Tampered Milestone",
        "anchoring_status": "ANCHORED",
        "dispute_status": "RESOLVED",
        "composite_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
        "blockchain_record": {"transaction_hash": "0x1234567890abcdef"},
        "created_at": "2020-01-01T00:00:00.000Z",
    }

    res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json=malicious_payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 201
    data = res.json()["data"]

    # Injected values MUST have been discarded
    assert data["registration_id"] != "REG-1999-FAKE01"
    assert data["anchoring_status"] == "PENDING"
    assert data["dispute_status"] == "NONE"
    assert data["composite_sha256"] is None
    assert data["blockchain_record"] is None
    assert not data["created_at"].startswith("2020-01-01")


def test_no_fake_blockchain_record_is_created(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 12: Creating a version does not create any fake BlockchainRecord row."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "Real Version"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res.status_code == 201
    data = res.json()["data"]

    # Verify directly in the database
    version_in_db = db_session.execute(
        select(ProjectVersion).where(ProjectVersion.public_id == data["public_id"])
    ).scalar_one()

    records_count = db_session.execute(
        select(BlockchainRecord).where(BlockchainRecord.version_id == version_in_db.id)
    ).scalars().all()

    assert len(records_count) == 0


def test_idempotency_key_replay_returns_200_ok(
    client: TestClient, create_test_project_with_owner
):
    """Test 13: Replaying a version creation request with the same Idempotency-Key returns 200 OK."""
    _, owner_token, project_id, _ = create_test_project_with_owner()
    idempotency_key = str(uuid.uuid4())

    # 1. First submission (201 Created)
    res1 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "First Submit"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert res1.status_code == 201
    data1 = res1.json()["data"]

    # 2. Replay with identical key (200 OK)
    res2 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "First Submit"},
        headers={
            "Authorization": f"Bearer {owner_token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()["data"]

    assert data1["public_id"] == data2["public_id"]
    assert data1["registration_id"] == data2["registration_id"]
    assert data1["version_index"] == data2["version_index"]


# ==============================================================================
# 2. Lifecycle Stage Transition Tests
# ==============================================================================


def test_valid_lifecycle_progression(client: TestClient, create_test_project_with_owner):
    """Test 14: Valid lifecycle transitions (IDEA -> DESIGN -> PROTOTYPE -> FINAL) all succeed."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    stages = ["IDEA", "DESIGN", "PROTOTYPE", "FINAL"]
    for idx, stage in enumerate(stages, start=1):
        res = client.post(
            f"/api/v1/projects/{project_id}/versions",
            json={
                "version_tag": f"v{idx}.0",
                "lifecycle_stage": stage,
                "title": f"Milestone for {stage}",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["lifecycle_stage"] == stage
        assert data["version_index"] == idx


def test_same_stage_iteration_succeeds(client: TestClient, create_test_project_with_owner):
    """Test 15: Iterations within the same lifecycle stage are permitted."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    res1 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "DESIGN", "title": "Design 1"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res1.status_code == 201

    res2 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.1", "lifecycle_stage": "DESIGN", "title": "Design 1 Revision"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res2.status_code == 201
    assert res2.json()["data"]["lifecycle_stage"] == "DESIGN"
    assert res2.json()["data"]["version_index"] == 2


def test_backward_lifecycle_transition_is_rejected(client: TestClient, create_test_project_with_owner):
    """Test 16: Backward transition (e.g. PROTOTYPE -> IDEA or DESIGN -> IDEA) is rejected with 422."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    # Create PROTOTYPE version
    r1 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "PROTOTYPE", "title": "Prototype v1"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r1.status_code == 201

    # Attempt backward jump to IDEA
    r2 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.1", "lifecycle_stage": "IDEA", "title": "Regressed Idea"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r2.status_code == 422
    body = r2.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_LIFECYCLE_TRANSITION"


def test_final_version_cannot_be_succeeded(client: TestClient, create_test_project_with_owner):
    """Test 17: Once a project reaches FINAL stage, no further versions can be added."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    r1 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "FINAL", "title": "Final Submission"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r1.status_code == 201

    # Attempt another version after FINAL
    r2 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.1", "lifecycle_stage": "FINAL", "title": "Attempted Extra Final"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r2.status_code == 422
    assert r2.json()["error"]["code"] == "FINAL_VERSION_IMMUTABLE"


def test_historical_version_data_remains_immutable(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 18: Historical version data is not modified when subsequent versions are added."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    res1 = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "Historical Idea"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    v1_data = res1.json()["data"]

    # Add second version
    client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v2.0", "lifecycle_stage": "DESIGN", "title": "Newer Milestone"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Re-verify v1 in database
    v1_in_db = db_session.execute(
        select(ProjectVersion).where(ProjectVersion.public_id == v1_data["public_id"])
    ).scalar_one()

    assert v1_in_db.title == "Historical Idea"
    assert v1_in_db.registration_id == v1_data["registration_id"]
    assert v1_in_db.version_index == 1
    assert v1_in_db.lifecycle_stage == ProjectVersionStage.IDEA


# ==============================================================================
# 3. Artifact Association Tests
# ==============================================================================


def test_referenced_artifact_association(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 19: Valid artifacts are attached to the newly created version snapshot."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    # Pre-create an initial version and an artifact
    v_init_res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v0.9", "lifecycle_stage": "IDEA", "title": "Setup Version"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    v_init_id = v_init_res.json()["data"]["public_id"]
    v_init = db_session.execute(
        select(ProjectVersion).where(ProjectVersion.public_id == v_init_id)
    ).scalar_one()

    artifact = Artifact(
        public_id=f"ART-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=v_init.id,
        file_name="architecture_spec.pdf",
        file_type="application/pdf",
        file_size_bytes=1048576,
        sha256_hash="a" * 64,
        ipfs_cid="bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m",
        artifact_category=ArtifactCategory.DESIGN_SPEC,
    )
    db_session.add(artifact)
    db_session.commit()

    # Now create next version referencing this artifact
    v2_res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "DESIGN",
            "title": "Design with Artifact",
            "artifact_ids": [artifact.public_id],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert v2_res.status_code == 201
    data = v2_res.json()["data"]
    assert len(data["artifacts"]) == 1
    assert data["artifacts"][0]["public_id"] == artifact.public_id
    assert data["artifacts"][0]["file_name"] == "architecture_spec.pdf"


def test_nonexistent_artifact_reference_returns_404(
    client: TestClient, create_test_project_with_owner
):
    """Test 20: Referencing an artifact public_id that does not exist returns 404."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    response = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "IDEA",
            "title": "Missing Artifact Version",
            "artifact_ids": ["ART-202609-NONEXIST"],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ARTIFACT_NOT_FOUND"


def test_cross_project_artifact_association_rejected(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 21: Attempting to associate an artifact belonging to another project is rejected."""
    _, owner_token1, project_id1, _ = create_test_project_with_owner(owner_prefix="owner_p1")
    _, owner_token2, project_id2, _ = create_test_project_with_owner(owner_prefix="owner_p2")

    # Create version in Project 1
    v1_res = client.post(
        f"/api/v1/projects/{project_id1}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "P1 Version"},
        headers={"Authorization": f"Bearer {owner_token1}"},
    )
    v1_id = v1_res.json()["data"]["public_id"]
    v1_orm = db_session.execute(
        select(ProjectVersion).where(ProjectVersion.public_id == v1_id)
    ).scalar_one()

    # Artifact linked to Project 1
    artifact_p1 = Artifact(
        public_id=f"ART-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=v1_orm.id,
        file_name="secret_p1.pdf",
        file_type="application/pdf",
        file_size_bytes=1000,
        sha256_hash="b" * 64,
        ipfs_cid="bafybeip1cid",
        artifact_category=ArtifactCategory.SOURCE_CODE,
    )
    db_session.add(artifact_p1)
    db_session.commit()

    # Project 2 tries to link Project 1's artifact
    cross_res = client.post(
        f"/api/v1/projects/{project_id2}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "IDEA",
            "title": "P2 Sneaky Version",
            "artifact_ids": [artifact_p1.public_id],
        },
        headers={"Authorization": f"Bearer {owner_token2}"},
    )
    assert cross_res.status_code == 422
    assert cross_res.json()["error"]["code"] == "INVALID_ARTIFACT_ASSOCIATION"


# ==============================================================================
# 4. List Versions Tests (GET /api/v1/projects/{project_id}/versions)
# ==============================================================================


def test_list_versions_returns_sequential_order(
    client: TestClient, create_test_project_with_owner
):
    """Test 22: GET versions returns all snapshots in strictly ascending version_index order."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    for idx, (tag, stage) in enumerate([("v1.0", "IDEA"), ("v2.0", "DESIGN"), ("v3.0", "PROTOTYPE")], 1):
        client.post(
            f"/api/v1/projects/{project_id}/versions",
            json={"version_tag": tag, "lifecycle_stage": stage, "title": f"Milestone {idx}"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )

    list_res = client.get(f"/api/v1/projects/{project_id}/versions")
    assert list_res.status_code == 200
    body = list_res.json()
    assert body["success"] is True
    versions = body["data"]

    assert len(versions) == 3
    assert [v["version_index"] for v in versions] == [1, 2, 3]
    assert [v["lifecycle_stage"] for v in versions] == ["IDEA", "DESIGN", "PROTOTYPE"]


def test_list_versions_empty_list_for_new_project(
    client: TestClient, create_test_project_with_owner
):
    """Test 23: A project with zero versions returns an empty list with 200 OK."""
    _, _, project_id, _ = create_test_project_with_owner()

    res = client.get(f"/api/v1/projects/{project_id}/versions")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"] == []


def test_list_versions_public_project_unauthenticated(
    client: TestClient, create_test_project_with_owner
):
    """Test 24: Unauthenticated caller can list versions for a public project."""
    _, owner_token, project_id, _ = create_test_project_with_owner(visibility="PUBLIC")

    client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "Open Idea"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    res = client.get(f"/api/v1/projects/{project_id}/versions")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1


def test_list_versions_private_project_access_control(
    client: TestClient, create_test_project_with_owner, create_version_test_user
):
    """Test 25: Private project version list enforces strict visibility controls."""
    owner, owner_token, project_id, _ = create_test_project_with_owner(visibility="PRIVATE")
    other_user, other_token = create_version_test_user("unrelated_student", UserRole.STUDENT)

    client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "Secret Idea"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # 1. Unauthenticated -> 404 (masks existence)
    res_anon = client.get(f"/api/v1/projects/{project_id}/versions")
    assert res_anon.status_code == 404

    # 2. Non-member authenticated -> 404
    res_other = client.get(
        f"/api/v1/projects/{project_id}/versions",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res_other.status_code == 404

    # 3. Owner -> 200 OK
    res_owner = client.get(
        f"/api/v1/projects/{project_id}/versions",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_owner.status_code == 200
    assert len(res_owner.json()["data"]) == 1


def test_list_versions_nonexistent_project_returns_404(client: TestClient):
    """Test 26: Listing versions for a non-existent project returns 404."""
    res = client.get("/api/v1/projects/PRJ-202609-00000/versions")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_internal_uuids_not_leaked_in_list_or_create(
    client: TestClient, create_test_project_with_owner
):
    """Test 27: Internal database UUIDs are never exposed in version responses."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "Check UUID Leaks"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    data = res.json()["data"]

    # UUID regex
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
    )

    for key, value in data.items():
        if isinstance(value, str):
            assert not uuid_pattern.match(value), f"Key '{key}' contains raw UUID: '{value}'"


# ==============================================================================
# 5. Security & OpenAPI Verification Tests
# ==============================================================================


def test_security_passwords_never_present_in_responses(
    client: TestClient, create_test_project_with_owner
):
    """Test 28: Passwords and password hashes never appear in response payloads."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    post_res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "Security Check"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert "password" not in post_res.text.lower()
    assert "argon2" not in post_res.text.lower()

    get_res = client.get(f"/api/v1/projects/{project_id}/versions")
    assert "password" not in get_res.text.lower()
    assert "argon2" not in get_res.text.lower()


def test_openapi_includes_version_endpoints(client: TestClient):
    """Test 29: OpenAPI specification documents POST and GET /projects/{project_id}/versions."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})

    version_path = "/api/v1/projects/{project_id}/versions"
    assert version_path in paths, f"Path '{version_path}' missing from OpenAPI routes"

    post_op = paths[version_path].get("post")
    assert post_op is not None
    assert post_op["summary"] == "Create Project Version Milestone"

    get_op = paths[version_path].get("get")
    assert get_op is not None
    assert get_op["summary"] == "List Project Versions"
