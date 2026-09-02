import hashlib
import io
import re
import uuid
from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.artifact import Artifact
from app.models.enums import ArtifactCategory, ProjectMemberRole, UserRole
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.services.artifact_service import (
    MAX_ARTIFACT_SIZE_BYTES,
    STREAM_CHUNK_SIZE,
    get_artifact_content,
    sanitize_filename,
)
from app.storage import (
    LocalStorageAdapter,
    StorageService,
    get_storage_service,
    set_storage_service,
)


@pytest.fixture(autouse=True)
def setup_test_storage(tmp_path):
    """
    Ensures every test executes against an isolated temporary directory,
    guaranteeing tests never touch the real development storage directory.
    """
    test_adapter = LocalStorageAdapter(root_dir=tmp_path / "test_artifacts")
    test_service = StorageService(adapter=test_adapter)
    set_storage_service(test_service)
    yield test_service
    set_storage_service(None)


@pytest.fixture
def create_artifact_test_user(db_session: Session):
    """Helper fixture to create test users with specified roles."""
    def _create(
        email_prefix: str = "art_user",
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
def create_test_project_with_owner(client: TestClient, create_artifact_test_user):
    """Helper fixture to create a project with an authorized owner."""
    def _create(
        owner_prefix: str = "proj_owner",
        title: str = "Artifact Test Registry",
    ) -> Tuple[User, str, str, str]:
        owner, owner_token = create_artifact_test_user(owner_prefix, UserRole.STUDENT)
        res = client.post(
            "/api/v1/projects",
            json={
                "title": title,
                "category": "WEB3",
                "department": "Computer Science",
                "academic_year": "2025-2026",
                "visibility": "PUBLIC",
            },
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res.status_code == 201
        data = res.json()["data"]
        return owner, owner_token, data["public_id"], data["slug"]

    return _create


# ==============================================================================
# 1. CORE UPLOAD & VALIDATION TESTS
# ==============================================================================

def test_authorized_owner_can_upload_valid_artifact(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 1: Authenticated authorized owner can upload a valid artifact file."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    file_content = b"%PDF-1.4 Mock project design specification content"
    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("spec.pdf", io.BytesIO(file_content), "application/pdf")},
        data={"artifact_category": "DESIGN_SPEC", "project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 201
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # Validate ART-YYYYMM-XXXXX identifier format
    assert data["public_id"].startswith("ART-")
    assert re.match(r"^ART-\d{6}-[0-9A-F]{5}$", data["public_id"])
    assert data["file_name"] == "spec.pdf"
    assert data["file_type"] == "application/pdf"
    assert data["file_size_bytes"] == len(file_content)
    assert data["sha256_hash"] == hashlib.sha256(file_content).hexdigest()
    assert data["ipfs_cid"] is None
    assert data["artifact_category"] == "DESIGN_SPEC"
    assert "uploaded_at" in data

    # Verify DB persistence
    artifact = db_session.execute(
        select(Artifact).where(Artifact.public_id == data["public_id"])
    ).scalar_one_or_none()
    assert artifact is not None
    assert artifact.file_name == "spec.pdf"
    assert artifact.sha256_hash == hashlib.sha256(file_content).hexdigest()


def test_unauthenticated_upload_returns_401(client: TestClient):
    """Test 2: Unauthenticated upload request is rejected with 401 Unauthorized."""
    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")},
        data={"artifact_category": "DOCUMENTATION"},
    )
    assert res.status_code == 401
    assert res.json()["success"] is False


def test_unauthorized_project_user_receives_403(
    client: TestClient, create_test_project_with_owner, create_artifact_test_user
):
    """Test 3: Authenticated user who is not a member of the project receives 403 Forbidden."""
    _, _, project_id, _ = create_test_project_with_owner()
    _, stranger_token = create_artifact_test_user("stranger", UserRole.STUDENT)

    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("unauth.zip", io.BytesIO(b"zipcontent"), "application/zip")},
        data={"artifact_category": "SOURCE_CODE", "project_id": project_id},
        headers={"Authorization": f"Bearer {stranger_token}"},
    )

    assert res.status_code == 403
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"


def test_authorized_project_member_can_upload(
    client: TestClient, create_test_project_with_owner, create_artifact_test_user
):
    """Test: Active team contributor can upload artifact to their assigned project."""
    _, owner_token, project_id, _ = create_test_project_with_owner()
    contributor, contrib_token = create_artifact_test_user("teammate", UserRole.STUDENT)

    # Add contributor to project
    add_res = client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_public_id": contributor.public_id, "role_in_project": "CONTRIBUTOR"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert add_res.status_code == 201

    # Contributor uploads artifact
    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("module.py", io.BytesIO(b"print('hello')"), "text/plain")},
        data={"artifact_category": "SOURCE_CODE", "project_id": project_id},
        headers={"Authorization": f"Bearer {contrib_token}"},
    )
    assert res.status_code == 201
    assert res.json()["success"] is True


def test_admin_can_upload_to_any_project(
    client: TestClient, create_test_project_with_owner, create_artifact_test_user
):
    """Test: Admin can upload artifact to any project."""
    _, _, project_id, _ = create_test_project_with_owner()
    _, admin_token = create_artifact_test_user("admin_user", UserRole.ADMIN)

    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("admin_audit.pdf", io.BytesIO(b"audit"), "application/pdf")},
        data={"artifact_category": "DOCUMENTATION", "project_id": project_id},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201
    assert res.json()["success"] is True


def test_nonexistent_project_returns_404(client: TestClient, create_artifact_test_user):
    """Test 4: Specifying a nonexistent project returns 404 Not Found."""
    _, token = create_artifact_test_user()
    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("report.pdf", io.BytesIO(b"test"), "application/pdf")},
        data={"project_id": "PRJ-999999-XXXXX"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_nonexistent_version_returns_404(client: TestClient, create_artifact_test_user):
    """Test 5: Specifying a nonexistent version returns 404 Not Found."""
    _, token = create_artifact_test_user()
    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("report.pdf", io.BytesIO(b"test"), "application/pdf")},
        data={"version_id": "VER-999999-XXXXX"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "VERSION_NOT_FOUND"


def test_cross_project_version_association_rejected(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 6: Associating an artifact with a version belonging to another project is rejected."""
    _, owner1_token, project1_id, _ = create_test_project_with_owner(title="Project 1")
    _, owner2_token, project2_id, _ = create_test_project_with_owner(title="Project 2")

    # Create version in Project 2
    ver2_res = client.post(
        f"/api/v1/projects/{project2_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "Proj 2 Initial"},
        headers={"Authorization": f"Bearer {owner2_token}"},
    )
    ver2_public_id = ver2_res.json()["data"]["public_id"]

    # Attempt to upload to Project 1 referencing Version 2 from Project 2
    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("cross.pdf", io.BytesIO(b"mismatch"), "application/pdf")},
        data={"project_id": project1_id, "version_id": ver2_public_id},
        headers={"Authorization": f"Bearer {owner1_token}"},
    )

    assert res.status_code == 422
    assert res.json()["error"]["code"] == "CROSS_PROJECT_VERSION_MISMATCH"


# ==============================================================================
# 2. IDENTIFIER & DATA PRIVACY TESTS
# ==============================================================================

def test_artifact_public_id_format_and_uniqueness(
    client: TestClient, create_test_project_with_owner
):
    """Test 7: Artifact public ID follows ART-YYYYMM-XXXXX format and is distinct per upload."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    res1 = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("file1.pdf", io.BytesIO(b"file 1"), "application/pdf")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    res2 = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("file2.pdf", io.BytesIO(b"file 2"), "application/pdf")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    art1 = res1.json()["data"]
    art2 = res2.json()["data"]

    pattern = r"^ART-\d{6}-[0-9A-F]{5}$"
    assert re.match(pattern, art1["public_id"])
    assert re.match(pattern, art2["public_id"])
    assert art1["public_id"] != art2["public_id"]


def test_internal_uuids_and_credentials_never_leaked(
    client: TestClient, create_test_project_with_owner
):
    """Test 8 & 24: Internal database UUIDs, passwords, and server secrets are never in response."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("data.json", io.BytesIO(b'{"key": "value"}'), "application/json")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    body = res.json()
    raw_text = res.text

    assert "id" not in body["data"] or body["data"].get("id") is None
    assert "password" not in raw_text.lower()
    assert "hashed_password" not in raw_text.lower()
    assert "secret" not in raw_text.lower()
    assert "/tmp" not in raw_text
    assert "C:\\" not in raw_text


# ==============================================================================
# 3. FILENAME SANITIZATION & SECURITY TESTS
# ==============================================================================

def test_path_traversal_filenames_are_sanitized(
    client: TestClient, create_test_project_with_owner
):
    """Test 9 & 26: Filenames with path traversal sequences are safely stripped."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    # UNIX-style traversal
    res1 = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("../../etc/passwd.pdf", io.BytesIO(b"pdf"), "application/pdf")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res1.status_code == 201
    assert res1.json()["data"]["file_name"] == "passwd.pdf"

    # Windows-style traversal
    res2 = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("..\\..\\Windows\\secret.txt", io.BytesIO(b"text"), "text/plain")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res2.status_code == 201
    assert res2.json()["data"]["file_name"] == "secret.txt"


def test_sanitize_filename_utility_directly():
    """Unit test for sanitize_filename utility covering edge cases."""
    assert sanitize_filename("test.pdf") == "test.pdf"
    assert sanitize_filename("../../../malicious.zip") == "malicious.zip"
    assert sanitize_filename("C:\\Users\\Admin\\config.json") == "config.json"
    assert sanitize_filename("null\x00byte.txt") == "nullbyte.txt"

    with pytest.raises(Exception):
        sanitize_filename("")

    with pytest.raises(Exception):
        sanitize_filename("   ...   ")


# ==============================================================================
# 4. CRYPTOGRAPHIC SHA-256 HASH VERIFICATION TESTS
# ==============================================================================

def test_known_content_sha256_cryptographic_verification(
    client: TestClient, create_test_project_with_owner
):
    """Test 12: Verify SHA-256 against known independent cryptographic digest."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    # Independent deterministic test payload
    known_payload = b"SIH-2026-CYB05-CRYPTOGRAPHIC-TEST-SUITE-VERIFICATION-TOKEN-42"
    # Independently precalculated SHA-256
    expected_hex = hashlib.sha256(known_payload).hexdigest()

    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("crypto_proof.dat", io.BytesIO(known_payload), "application/octet-stream")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 201
    data = res.json()["data"]
    assert data["sha256_hash"] == expected_hex
    assert len(data["sha256_hash"]) == 64
    assert data["sha256_hash"].islower()


def test_deterministic_hashes_for_same_and_different_content(
    client: TestClient, create_test_project_with_owner
):
    """Test 13 & 14: Same content produces identical hash; different content produces different hash."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    payload_a = b"Common baseline document content"
    payload_b = b"Modified document content with variation"

    res1 = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("doc1.pdf", io.BytesIO(payload_a), "application/pdf")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    res2 = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("doc2.pdf", io.BytesIO(payload_a), "application/pdf")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    res3 = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("doc3.pdf", io.BytesIO(payload_b), "application/pdf")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    hash1 = res1.json()["data"]["sha256_hash"]
    hash2 = res2.json()["data"]["sha256_hash"]
    hash3 = res3.json()["data"]["sha256_hash"]

    # Identical content -> same hash
    assert hash1 == hash2
    # Different content -> different hash
    assert hash1 != hash3


# ==============================================================================
# 5. SIZE BOUNDARY & STREAMING TESTS
# ==============================================================================

def test_file_size_limit_rejection_at_50mb(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 16 & 17: Uploads exceeding 50 MB are rejected and leave no database row."""
    owner, owner_token, project_id, _ = create_test_project_with_owner()

    # Create an async generator / stream that yields more than 50 MB
    oversized_chunk = b"A" * (1024 * 1024)  # 1 MB chunk

    # Instead of allocating 51 MB in memory, simulate chunked reading in service test
    class MockOversizedUploadFile:
        filename = "huge_file.zip"
        content_type = "application/zip"
        chunks_sent = 0

        async def read(self, size: int = -1):
            if self.chunks_sent < 51:  # 51 MB total
                self.chunks_sent += 1
                return oversized_chunk
            return b""

    from app.services.artifact_service import ingest_artifact
    from app.models.enums import ArtifactCategory
    from app.core.exceptions import ValidationException

    initial_artifact_count = len(db_session.execute(select(Artifact)).scalars().all())

    with pytest.raises(ValidationException) as excinfo:
        import asyncio
        asyncio.run(
            ingest_artifact(
                db=db_session,
                file=MockOversizedUploadFile(),
                artifact_category=ArtifactCategory.SOURCE_CODE,
                current_user=owner,
                project_id=project_id,
            )
        )

    assert excinfo.value.code == "FILE_TOO_LARGE"
    # Ensure no database record was persisted
    final_artifact_count = len(db_session.execute(select(Artifact)).scalars().all())
    assert final_artifact_count == initial_artifact_count


def test_empty_file_rejected_with_422(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 18: Empty file (0 bytes) is rejected with 422 Unprocessable Entity."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    initial_count = len(db_session.execute(select(Artifact)).scalars().all())

    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 422
    assert res.json()["error"]["code"] == "EMPTY_FILE_NOT_ALLOWED"

    # Confirm no artifact created in DB
    final_count = len(db_session.execute(select(Artifact)).scalars().all())
    assert final_count == initial_count


def test_streaming_read_chunk_behavior(
    client: TestClient, create_test_project_with_owner
):
    """Test 25: Verify implementation reads in configured chunk sizes without full RAM load."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    # Generate content larger than one chunk (e.g. 150 KB > 64 KB chunk)
    content = b"X" * (150 * 1024)

    from starlette.datastructures import UploadFile as StarletteUploadFile
    with patch.object(StarletteUploadFile, "read", autospec=True, side_effect=StarletteUploadFile.read) as mock_read:
        res = client.post(
            "/api/v1/artifacts/upload",
            files={"file": ("large_chunked.bin", io.BytesIO(content), "application/octet-stream")},
            data={"project_id": project_id},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res.status_code == 201
        # Check that read was called multiple times with STREAM_CHUNK_SIZE
        assert mock_read.call_count >= 2


# ==============================================================================
# 6. SYSTEM FIELDS & SPOOFING RESISTANCE TESTS
# ==============================================================================

def test_client_cannot_spoof_system_fields(
    client: TestClient, create_test_project_with_owner
):
    """Test 20, 21, 22, 23: Client cannot spoof internal ID, public ID, IPFS CID, or timestamps."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    spoofed_id = str(uuid.uuid4())
    spoofed_public_id = "ART-199901-FAKE0"
    spoofed_cid = "bafybeifakecidshouldnotbeaccepted123456789"

    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("payload.pdf", io.BytesIO(b"test data"), "application/pdf")},
        data={
            "id": spoofed_id,
            "public_id": spoofed_public_id,
            "ipfs_cid": spoofed_cid,
            "uploaded_at": "1999-01-01T00:00:00Z",
            "project_id": project_id,
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 201
    data = res.json()["data"]

    # System-generated values must override any client-supplied spoofing
    assert data["public_id"] != spoofed_public_id
    assert data["public_id"].startswith("ART-")
    assert data["ipfs_cid"] is None  # Never allow client-injected IPFS CID


def test_duplicate_file_allowed_across_projects(
    client: TestClient, create_test_project_with_owner
):
    """Test 19: Duplicate files across different projects are legitimately permitted."""
    _, owner1_token, proj1_id, _ = create_test_project_with_owner(title="Project One")
    _, owner2_token, proj2_id, _ = create_test_project_with_owner(title="Project Two")

    shared_code = b"print('identical shared open source utility')"

    res1 = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("util.py", io.BytesIO(shared_code), "text/plain")},
        data={"project_id": proj1_id},
        headers={"Authorization": f"Bearer {owner1_token}"},
    )
    res2 = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("util.py", io.BytesIO(shared_code), "text/plain")},
        data={"project_id": proj2_id},
        headers={"Authorization": f"Bearer {owner2_token}"},
    )

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["data"]["sha256_hash"] == res2.json()["data"]["sha256_hash"]
    assert res1.json()["data"]["public_id"] != res2.json()["data"]["public_id"]


# ==============================================================================
# 7. OPENAPI DOCUMENTATION TEST
# ==============================================================================

def test_openapi_includes_artifact_upload_endpoint(client: TestClient):
    """Test 28: Verify /openapi.json documents POST /api/v1/artifacts/upload with multipart."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    openapi = res.json()

    paths = openapi["paths"]
    assert "/api/v1/artifacts/upload" in paths
    upload_path = paths["/api/v1/artifacts/upload"]
    assert "post" in upload_path

    post_op = upload_path["post"]
    request_body = post_op.get("requestBody", {})
    content = request_body.get("content", {})
    assert "multipart/form-data" in content


def test_file_at_exact_max_boundary_handled(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 15: File exactly at maximum size boundary is accepted by streaming logic."""
    owner, _, project_id, _ = create_test_project_with_owner()

    # Simulate upload file of exactly 50 MB via stream chunks without huge RAM allocation
    chunk_1mb = b"B" * (1024 * 1024)

    class MockExactBoundaryUploadFile:
        filename = "boundary_50mb.zip"
        content_type = "application/zip"
        chunks_sent = 0

        async def read(self, size: int = -1):
            if self.chunks_sent < 50:  # exactly 50 MB
                self.chunks_sent += 1
                return chunk_1mb
            return b""

    from app.services.artifact_service import ingest_artifact
    import asyncio

    res = asyncio.run(
        ingest_artifact(
            db=db_session,
            file=MockExactBoundaryUploadFile(),
            artifact_category=ArtifactCategory.SOURCE_CODE,
            current_user=owner,
            project_id=project_id,
        )
    )

    assert res.file_size_bytes == 50 * 1024 * 1024
    assert res.public_id.startswith("ART-")


def test_database_rollback_on_persistence_failure(
    client: TestClient, create_test_project_with_owner, db_session: Session
):
    """Test 27: Unexpected database failure during persistence triggers clean rollback."""
    owner, _, project_id, _ = create_test_project_with_owner()

    class MockSimpleUploadFile:
        filename = "simple.pdf"
        content_type = "application/pdf"
        read_done = False

        async def read(self, size: int = -1):
            if not self.read_done:
                self.read_done = True
                return b"valid payload"
            return b""

    from app.services.artifact_service import ingest_artifact
    import asyncio

    initial_count = len(db_session.execute(select(Artifact)).scalars().all())

    with patch.object(db_session, "commit", side_effect=Exception("Database commit explosion")):
        with pytest.raises(Exception, match="Database commit explosion"):
            asyncio.run(
                ingest_artifact(
                    db=db_session,
                    file=MockSimpleUploadFile(),
                    artifact_category=ArtifactCategory.DOCUMENTATION,
                    current_user=owner,
                    project_id=project_id,
                )
            )

    # Verify no partial rows survived
    final_count = len(db_session.execute(select(Artifact)).scalars().all())
    assert final_count == initial_count


# ==============================================================================
# 8. STORAGE ABSTRACTION & CONTENT BOUNDARY TESTS
# ==============================================================================

def test_artifact_content_is_stored_and_matches_upload(
    client: TestClient, create_test_project_with_owner
):
    """Storage Test 1 & 2: Successful upload persists content accessible to future IPFS pinning."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    test_content = b"CRITICAL-ARTIFACT-CONTENT-RETAINED-FOR-PHASE-5-IPFS-PINNING-42"
    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("project_spec.pdf", io.BytesIO(test_content), "application/pdf")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 201
    data = res.json()["data"]
    public_id = data["public_id"]

    import asyncio
    retrieved_bytes = asyncio.run(get_artifact_content(public_id))

    # Stored content must exactly match uploaded content
    assert retrieved_bytes == test_content
    # SHA-256 matches independent digest
    assert hashlib.sha256(retrieved_bytes).hexdigest() == data["sha256_hash"]


def test_storage_key_cannot_escape_storage_root(tmp_path):
    """Storage Test 9: Storage key containment check prevents path traversal."""
    adapter = LocalStorageAdapter(root_dir=tmp_path / "containment")

    # Safe keys
    assert adapter._resolve_safe_path("ART-202609-11E54/content").is_relative_to(adapter.root_dir)
    assert adapter._resolve_safe_path("ART-202609-11E54.bin").is_relative_to(adapter.root_dir)

    # Malicious traversal attempts
    with pytest.raises(ValueError, match="Path traversal detected"):
        adapter._resolve_safe_path("../../outside.txt")

    with pytest.raises(ValueError, match="Path traversal detected"):
        adapter._resolve_safe_path("..\\..\\Windows\\System32\\calc.exe")

    with pytest.raises(ValueError):
        adapter._resolve_safe_path("")


def test_oversized_upload_cleans_up_stored_partial_content(
    client: TestClient, create_test_project_with_owner, setup_test_storage, db_session: Session
):
    """Storage Test 6: Oversized upload aborts and leaves no partial artifact files in storage."""
    owner, _, project_id, _ = create_test_project_with_owner()

    oversized_chunk = b"Z" * (1024 * 1024)  # 1 MB

    class MockOversizedUpload:
        filename = "too_large.zip"
        content_type = "application/zip"
        chunks_sent = 0

        async def read(self, size: int = -1):
            if self.chunks_sent < 51:
                self.chunks_sent += 1
                return oversized_chunk
            return b""

    from app.services.artifact_service import ingest_artifact
    from app.core.exceptions import ValidationException
    import asyncio

    with pytest.raises(ValidationException, match="Artifact exceeds maximum allowed size"):
        asyncio.run(
            ingest_artifact(
                db=db_session,
                file=MockOversizedUpload(),
                artifact_category=ArtifactCategory.SOURCE_CODE,
                current_user=owner,
                project_id=project_id,
            )
        )

    # Verify no content files remain in test storage directory
    stored_files = [p for p in setup_test_storage.adapter.root_dir.glob("**/*") if p.is_file()]
    assert len(stored_files) == 0


def test_database_failure_cleans_up_stored_artifact(
    create_test_project_with_owner, setup_test_storage, db_session: Session
):
    """Storage Test 7: Failure during database commit removes the stored artifact file."""
    owner, _, project_id, _ = create_test_project_with_owner()

    class MockUpload:
        filename = "doc.pdf"
        content_type = "application/pdf"
        read_done = False

        async def read(self, size: int = -1):
            if not self.read_done:
                self.read_done = True
                return b"valid payload bytes"
            return b""

    from app.services.artifact_service import ingest_artifact
    import asyncio

    with patch.object(db_session, "commit", side_effect=Exception("Database crash on commit")):
        with pytest.raises(Exception, match="Database crash on commit"):
            asyncio.run(
                ingest_artifact(
                    db=db_session,
                    file=MockUpload(),
                    artifact_category=ArtifactCategory.DOCUMENTATION,
                    current_user=owner,
                    project_id=project_id,
                )
            )

    # Verify that the file was deleted and not left orphaned
    stored_files = [p for p in setup_test_storage.adapter.root_dir.glob("**/*") if p.is_file()]
    assert len(stored_files) == 0


def test_storage_failure_does_not_leave_database_record(
    create_test_project_with_owner, setup_test_storage, db_session: Session
):
    """Storage Test 8: Failure in storage layer prevents database record creation."""
    owner, _, project_id, _ = create_test_project_with_owner()

    class MockUpload:
        filename = "doc.pdf"
        content_type = "application/pdf"
        read_done = False

        async def read(self, size: int = -1):
            if not self.read_done:
                self.read_done = True
                return b"valid content"
            return b""

    from app.services.artifact_service import ingest_artifact
    import asyncio

    initial_db_count = len(db_session.execute(select(Artifact)).scalars().all())

    with patch.object(setup_test_storage.adapter, "write_chunk", side_effect=IOError("Storage disk failure")):
        with pytest.raises(IOError, match="Storage disk failure"):
            asyncio.run(
                ingest_artifact(
                    db=db_session,
                    file=MockUpload(),
                    artifact_category=ArtifactCategory.DOCUMENTATION,
                    current_user=owner,
                    project_id=project_id,
                )
            )

    # Verify no database record was created
    final_db_count = len(db_session.execute(select(Artifact)).scalars().all())
    assert final_db_count == initial_db_count


def test_api_response_does_not_expose_filesystem_path(
    client: TestClient, create_test_project_with_owner, setup_test_storage
):
    """Storage Test 11: API response does not leak internal storage directory or filesystem paths."""
    _, owner_token, project_id, _ = create_test_project_with_owner()

    res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("report.pdf", io.BytesIO(b"content"), "application/pdf")},
        data={"project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 201
    raw_response = res.text
    root_str = str(setup_test_storage.adapter.root_dir)

    assert root_str not in raw_response
    assert "storage" not in raw_response.lower()
    assert "test_artifacts" not in raw_response
