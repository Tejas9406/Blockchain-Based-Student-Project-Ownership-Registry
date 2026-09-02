import hashlib
import io
import uuid
from datetime import datetime, timezone
from typing import Tuple
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.blockchain_provider import (
    BlockchainVerificationProvider,
    OnChainVerificationResult,
    set_blockchain_provider,
)
from app.core.exceptions import BlockchainException, ValidationException
from app.core.security import create_access_token, hash_password
from app.models.artifact import Artifact
from app.models.blockchain_record import BlockchainRecord
from app.models.enums import (
    AnchoringStatus,
    ArtifactCategory,
    DisputeStatus,
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


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def create_verification_user(db_session: Session):
    """Fixture to create test users."""
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
            institution_id="National Institute of Technology",
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
def setup_registered_project(db_session: Session, create_verification_user):
    """
    Creates a project, an owner, a registered project version with an artifact,
    and returns authoritative data for verification tests.
    """
    owner, owner_token = create_verification_user(email_prefix="owner")
    unique_suffix = uuid.uuid4().hex[:5].upper()
    proj_id = f"PRJ-202609-{unique_suffix}"
    reg_id = f"REG-2026-{unique_suffix}"

    project = Project(
        public_id=proj_id,
        title="Decentralized IPFS Academic Registry",
        slug=f"decentralized-ipfs-{unique_suffix.lower()}",
        abstract="Academic credential ownership verification on blockchain.",
        category="Blockchain & Web3",
        department="Computer Science & Engineering",
        academic_year="2025-2026",
        current_lifecycle_stage=ProjectVersionStage.DESIGN,
        visibility=ProjectVisibility.PUBLIC,
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(project)
    db_session.flush()

    member = ProjectMember(
        project_id=project.id,
        user_id=owner.id,
        role_in_project=ProjectMemberRole.LEAD,
        is_owner=True,
    )
    db_session.add(member)

    # Independent SHA-256 calculation for artifact
    file_bytes = b"authoritative student project paper content 2026"
    independent_file_hash = hashlib.sha256(file_bytes).hexdigest().lower()

    # Independent composite hash
    composite_hash = hashlib.sha256(b"composite_manifest_payload_v1").hexdigest().lower()

    version = ProjectVersion(
        public_id=f"VER-202609-{unique_suffix}",
        registration_id=reg_id,
        project_id=project.id,
        version_index=1,
        version_tag="v1.0",
        title="Version 1.0 Initial Design",
        lifecycle_stage=ProjectVersionStage.DESIGN,
        dispute_status=DisputeStatus.NONE,
        anchoring_status=AnchoringStatus.PENDING,
        composite_sha256=composite_hash,
        ipfs_root_cid="bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m",
    )
    db_session.add(version)
    db_session.flush()

    artifact = Artifact(
        public_id=f"ART-202609-{unique_suffix}",
        version_id=version.id,
        file_name="spec_document.pdf",
        file_type="application/pdf",
        file_size_bytes=len(file_bytes),
        sha256_hash=independent_file_hash,
        artifact_category=ArtifactCategory.DOCUMENTATION,
    )
    db_session.add(artifact)
    db_session.commit()
    db_session.refresh(project)
    db_session.refresh(version)
    db_session.refresh(artifact)

    return {
        "owner": owner,
        "project": project,
        "version": version,
        "artifact": artifact,
        "registration_id": reg_id,
        "composite_hash": composite_hash,
        "file_bytes": file_bytes,
        "file_hash": independent_file_hash,
    }


# ==============================================================================
# 1. REGISTRATION ID VERIFICATION TESTS
# ==============================================================================

def test_verify_valid_registration_id_unanchored(client: TestClient, setup_registered_project):
    """Test 1: Valid registration ID returns project and version details without auth, indicating pending anchor."""
    reg_id = setup_registered_project["registration_id"]
    res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")

    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert data["is_valid"] is True
    assert data["registration_id"] == reg_id
    assert data["verification_method"] == "REGISTRATION_ID"
    assert data["project"]["public_id"] == setup_registered_project["project"].public_id
    assert data["project"]["title"] == "Decentralized IPFS Academic Registry"
    assert data["version"]["version_tag"] == "v1.0"
    assert data["version"]["lifecycle_stage"] == "DESIGN"
    assert data["blockchain_proof"] is None
    assert "awaiting blockchain anchoring" in data["message"]


def test_verify_invalid_registration_id_format(client: TestClient):
    """Test 2: Malformed registration ID format returns 422 Unprocessable Entity."""
    # Bad formats: missing prefix, too short, too long
    for bad_id in ["REG-2026-001", "INVALID", "REG-202-A8F92", "REG-2026-A8F92999"]:
        res = client.get(f"/api/v1/verification/verify-registration/{bad_id}")
        assert res.status_code == 422
        body = res.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INVALID_REGISTRATION_ID_FORMAT"


def test_verify_registration_id_not_found(client: TestClient):
    """Test 3: Non-existent registration ID returns 404 Not Found."""
    res = client.get("/api/v1/verification/verify-registration/REG-2026-99999")
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "REGISTRATION_NOT_FOUND"


def test_verify_anchored_registration_with_blockchain_record(
    client: TestClient, db_session: Session, setup_registered_project
):
    """Test 4 & 5: Anchored version with BlockchainRecord returns authoritative on-chain proof."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]

    # Attach BlockchainRecord
    now = datetime.now(timezone.utc)
    record = BlockchainRecord(
        public_id=f"BLK-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=version.id,
        transaction_hash="0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
        block_number=142981,
        smart_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        anchored_hash=f"0x{setup_registered_project['composite_hash']}",
        ipfs_cid_anchored=version.ipfs_root_cid,
        submitter_wallet="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        author_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        network_name="hardhat",
        chain_id=31337,
        anchored_timestamp=now,
    )
    version.anchoring_status = "ANCHORED"
    db_session.add(record)
    db_session.commit()

    res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["is_valid"] is True
    assert data["blockchain_proof"] is not None
    proof = data["blockchain_proof"]
    assert proof["transaction_hash"] == "0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb"
    assert proof["block_number"] == 142981
    assert proof["smart_contract_address"] == "0x5FbDB2315678afecb367f032d93F642f64180aa3"
    assert proof["author_wallet"] == "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    assert proof["dispute_status"] == "NONE"
    assert proof["match_confirmed"] is True


def test_verify_disputed_registration_marks_invalid(
    client: TestClient, db_session: Session, setup_registered_project
):
    """Test 7: Registration under active dispute marks is_valid=False and reports dispute state."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]

    version.dispute_status = DisputeStatus.UNDER_REVIEW
    db_session.commit()

    res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is False
    assert "dispute" in data["message"].lower()


def test_public_verification_does_not_require_auth(client: TestClient, setup_registered_project):
    """Test 8: Verification endpoints do not require Authorization header."""
    reg_id = setup_registered_project["registration_id"]
    res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
    assert res.status_code == 200


def test_no_internal_uuids_or_sensitive_fields_in_response(
    client: TestClient, setup_registered_project
):
    """Test 9 & 10: Responses strictly avoid leaking internal UUIDs, passwords, and tokens."""
    reg_id = setup_registered_project["registration_id"]
    res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
    raw_text = res.text

    assert str(setup_registered_project["project"].id) not in raw_text
    assert str(setup_registered_project["version"].id) not in raw_text
    assert "password" not in raw_text.lower()
    assert "secret" not in raw_text.lower()
    assert "token" not in raw_text.lower()


# ==============================================================================
# 2. HASH VERIFICATION TESTS
# ==============================================================================

def test_verify_hash_composite_match_success(client: TestClient, setup_registered_project):
    """Hash Test 1: Valid composite version SHA-256 returns verified status."""
    composite_hash = setup_registered_project["composite_hash"]
    res = client.post(
        "/api/v1/verification/verify-hash",
        json={"sha256_hash": composite_hash},
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is True
    assert data["matched_hash"] == composite_hash
    assert data["project"]["public_id"] == setup_registered_project["project"].public_id
    assert data["version"]["version_tag"] == "v1.0"


def test_verify_hash_artifact_file_match_success(client: TestClient, setup_registered_project):
    """Hash Test 1b: Valid individual artifact SHA-256 returns verified status."""
    file_hash = setup_registered_project["file_hash"]
    res = client.post(
        "/api/v1/verification/verify-hash",
        json={"sha256_hash": file_hash},
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is True
    assert data["matched_hash"] == file_hash
    assert data["matched_file_name"] == "spec_document.pdf"
    assert data["project"]["public_id"] == setup_registered_project["project"].public_id


def test_verify_hash_case_insensitivity(client: TestClient, setup_registered_project):
    """Hash Test 5: Uppercase SHA-256 input is normalized and verified correctly."""
    upper_hash = setup_registered_project["composite_hash"].upper()
    res = client.post(
        "/api/v1/verification/verify-hash",
        json={"sha256_hash": upper_hash},
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is True
    assert data["matched_hash"] == upper_hash.lower()


def test_verify_hash_unknown_returns_not_verified(client: TestClient):
    """Hash Test 2 & 6: Unknown SHA-256 hash returns 200 OK with is_valid=False."""
    unknown_hash = "a" * 64
    res = client.post(
        "/api/v1/verification/verify-hash",
        json={"sha256_hash": unknown_hash},
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is False
    assert data["matched_hash"] == unknown_hash
    assert "does not match" in data["message"]


def test_verify_hash_invalid_length_returns_422(client: TestClient):
    """Hash Test 3: Hashes shorter or longer than 64 characters return 422."""
    for bad_hash in ["abc123", "a" * 63, "a" * 65]:
        res = client.post(
            "/api/v1/verification/verify-hash",
            json={"sha256_hash": bad_hash},
        )
        assert res.status_code == 422
        assert res.json()["error"]["code"] == "INVALID_HASH_FORMAT"


def test_verify_hash_invalid_hex_characters_returns_422(client: TestClient):
    """Hash Test 4: Non-hexadecimal characters return 422."""
    bad_hash = "g" * 64
    res = client.post(
        "/api/v1/verification/verify-hash",
        json={"sha256_hash": bad_hash},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "INVALID_HASH_FORMAT"


def test_verify_hash_with_registration_id_scope(client: TestClient, setup_registered_project):
    """Hash Test 7: Valid hash matching the specified registration ID succeeds."""
    res = client.post(
        "/api/v1/verification/verify-hash",
        json={
            "sha256_hash": setup_registered_project["composite_hash"],
            "registration_id": setup_registered_project["registration_id"],
        },
    )
    assert res.status_code == 200
    assert res.json()["data"]["is_valid"] is True


def test_verify_hash_with_mismatched_registration_id(client: TestClient, setup_registered_project):
    """Hash Test 7b: Valid hash for project A with registration ID of project B returns is_valid=False."""
    res = client.post(
        "/api/v1/verification/verify-hash",
        json={
            "sha256_hash": setup_registered_project["composite_hash"],
            "registration_id": "REG-2026-XXXXX",
        },
    )
    assert res.status_code == 200
    assert res.json()["data"]["is_valid"] is False


def test_blockchain_provider_mock_injection(client: TestClient, setup_registered_project):
    """Hash Test 8: Custom BlockchainVerificationProvider mock can be injected."""
    class MockProvider(BlockchainVerificationProvider):
        async def verify_project_version(self, registration_id, expected_hash=None):
            return OnChainVerificationResult(
                is_valid=True,
                registration_id=registration_id,
                anchored_timestamp=datetime.now(timezone.utc),
                smart_contract_address="0xMockAddress",
                author_wallet="0xMockAuthor",
                transaction_hash="0xMockTx",
                block_number=99999,
                match_confirmed=True,
            )

    set_blockchain_provider(MockProvider())
    try:
        res = client.get(
            f"/api/v1/verification/verify-registration/{setup_registered_project['registration_id']}"
        )
        assert res.status_code == 200
        proof = res.json()["data"]["blockchain_proof"]
        assert proof["smart_contract_address"] == "0xMockAddress"
        assert proof["block_number"] == 99999
    finally:
        set_blockchain_provider(None)


# ==============================================================================
# 3. FILE VERIFICATION TESTS
# ==============================================================================

def test_verify_file_exact_match_success(client: TestClient, setup_registered_project):
    """File Test 1: Uploading an identical registered file returns is_valid=True."""
    res = client.post(
        "/api/v1/verification/verify-file",
        files={"file": ("spec_document.pdf", io.BytesIO(setup_registered_project["file_bytes"]), "application/pdf")},
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is True
    assert data["verification_method"] == "FILE"
    assert data["matched_file_name"] == "spec_document.pdf"
    assert data["project"]["public_id"] == setup_registered_project["project"].public_id


def test_verify_file_modified_content_returns_not_verified(
    client: TestClient, setup_registered_project
):
    """File Test 2: Uploading a modified file with single altered byte returns is_valid=False."""
    modified_bytes = setup_registered_project["file_bytes"] + b"tampered"
    res = client.post(
        "/api/v1/verification/verify-file",
        files={"file": ("spec_document.pdf", io.BytesIO(modified_bytes), "application/pdf")},
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is False
    assert "does not match" in data["message"]


def test_verify_file_unrelated_content_returns_not_verified(client: TestClient):
    """File Test 3: Completely unrelated file returns is_valid=False."""
    unrelated_bytes = b"random unrelated content xyz 987"
    res = client.post(
        "/api/v1/verification/verify-file",
        files={"file": ("unrelated.txt", io.BytesIO(unrelated_bytes), "text/plain")},
    )

    assert res.status_code == 200
    assert res.json()["data"]["is_valid"] is False


def test_verify_file_empty_rejected_with_422(client: TestClient):
    """File Test 4: Empty 0-byte file is rejected with 422 Unprocessable Entity."""
    res = client.post(
        "/api/v1/verification/verify-file",
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
    )

    assert res.status_code == 422
    assert res.json()["error"]["code"] == "EMPTY_FILE_NOT_ALLOWED"


def test_verify_file_large_valid_file(client: TestClient, db_session: Session, setup_registered_project):
    """File Test 5 & 6: Verification of a large 2 MB file succeeds in streaming chunks."""
    version = setup_registered_project["version"]
    large_bytes = b"A" * (2 * 1024 * 1024)
    # Calculate independent hash
    large_hash = hashlib.sha256(large_bytes).hexdigest().lower()

    # Register artifact
    art = Artifact(
        public_id=f"ART-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=version.id,
        file_name="large_data.bin",
        file_type="application/octet-stream",
        file_size_bytes=len(large_bytes),
        sha256_hash=large_hash,
        artifact_category=ArtifactCategory.OTHER,
    )
    db_session.add(art)
    db_session.commit()

    res = client.post(
        "/api/v1/verification/verify-file",
        files={"file": ("large_data.bin", io.BytesIO(large_bytes), "application/octet-stream")},
    )

    assert res.status_code == 200
    assert res.json()["data"]["is_valid"] is True
    assert res.json()["data"]["matched_hash"] == large_hash


def test_verify_file_oversized_rejected_with_422(
    client: TestClient, db_session: Session, setup_registered_project
):
    """File Test 7: Files exceeding 50 MB are rejected with 422."""
    class MockOversizedFile:
        filename = "huge.bin"
        content_type = "application/octet-stream"
        chunks_sent = 0

        async def read(self, size: int = -1):
            if self.chunks_sent < 51:
                self.chunks_sent += 1
                return b"X" * (1024 * 1024)
            return b""

    from app.services.verification_service import verify_by_file
    from app.core.exceptions import ValidationException
    import asyncio

    with pytest.raises(ValidationException, match="File exceeds maximum allowed size"):
        asyncio.run(
            verify_by_file(
                db=db_session,
                file=MockOversizedFile(),
            )
        )


def test_file_verification_creates_zero_database_records(
    client: TestClient, db_session: Session, setup_registered_project
):
    """File Test 9: File verification is strictly read-only and never writes to database."""
    initial_artifact_count = len(db_session.execute(select(Artifact)).scalars().all())
    initial_version_count = len(db_session.execute(select(ProjectVersion)).scalars().all())

    client.post(
        "/api/v1/verification/verify-file",
        files={"file": ("query.pdf", io.BytesIO(setup_registered_project["file_bytes"]), "application/pdf")},
    )

    final_artifact_count = len(db_session.execute(select(Artifact)).scalars().all())
    final_version_count = len(db_session.execute(select(ProjectVersion)).scalars().all())

    assert final_artifact_count == initial_artifact_count
    assert final_version_count == initial_version_count


def test_openapi_documentation_includes_all_three_endpoints(client: TestClient):
    """OpenAPI Test: Confirms all three verification endpoints are documented in schema."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json()["paths"]

    assert "/api/v1/verification/verify-registration/{registration_id}" in paths
    assert "/api/v1/verification/verify-hash" in paths
    assert "/api/v1/verification/verify-file" in paths

    # Check verify-file consumes multipart/form-data
    post_file = paths["api/v1/verification/verify-file"]["post"] if "api/v1/verification/verify-file" in paths else paths["/api/v1/verification/verify-file"]["post"]
    assert "multipart/form-data" in post_file["requestBody"]["content"]


# ==============================================================================
# STEP 7: BLOCKCHAIN VERIFICATION INTEGRATION COMPREHENSIVE TESTS
# ==============================================================================

def test_step7_01_successful_registration_verification(client: TestClient, db_session: Session, setup_registered_project):
    """Test 1: Successful registration verification with matching on-chain data."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]
    now = datetime.now(timezone.utc)

    # Attach BlockchainRecord
    record = BlockchainRecord(
        public_id=f"BLK-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=version.id,
        transaction_hash="0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
        block_number=142981,
        smart_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        anchored_hash=f"0x{comp_hash}",
        ipfs_cid_anchored=version.ipfs_root_cid,
        submitter_wallet="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        author_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        network_name="hardhat",
        chain_id=31337,
        anchored_timestamp=now,
    )
    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.add(record)
    db_session.commit()

    class MockProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": f"0x{comp_hash}",
                "ipfs_root_cid": version.ipfs_root_cid,
                "version_index": 1,
                "lifecycle_stage": "DESIGN",
                "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "co_authors": [],
                "anchored_timestamp": now,
                "block_number": 142981,
                "dispute_state": "NONE",
                "exists": True,
            }

        async def verify_project_version(self, registration_id, expected_hash=None):
            return OnChainVerificationResult(
                is_valid=True,
                registration_id=registration_id,
                anchored_timestamp=now,
                ipfs_root_cid=version.ipfs_root_cid,
                author_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                dispute_status="NONE",
                transaction_hash="0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
                block_number=142981,
                smart_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
                match_confirmed=True,
            )

    set_blockchain_provider(MockProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_valid"] is True
        assert data["blockchain_proof"]["match_confirmed"] is True
        assert data["blockchain_proof"]["author_wallet"] == "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
        assert data["blockchain_proof"]["block_number"] == 142981
    finally:
        set_blockchain_provider(None)


def test_step7_02_registration_not_found(client: TestClient):
    """Test 2: Non-existent registration ID returns 404 NOT_FOUND."""
    res = client.get("/api/v1/verification/verify-registration/REG-2026-NONEX")
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "REGISTRATION_NOT_FOUND"


def test_step7_03_composite_hash_match(client: TestClient, db_session: Session, setup_registered_project):
    """Test 3: On-chain composite hash matches trusted DB version hash."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]
    now = datetime.now(timezone.utc)

    class HashMatchProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": f"0x{comp_hash}",
                "ipfs_root_cid": version.ipfs_root_cid,
                "version_index": 1,
                "lifecycle_stage": "DESIGN",
                "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "co_authors": [],
                "anchored_timestamp": now,
                "block_number": 100,
                "dispute_state": "NONE",
                "exists": True,
            }

    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.commit()

    set_blockchain_provider(HashMatchProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_valid"] is True
        assert data["blockchain_proof"]["match_confirmed"] is True
    finally:
        set_blockchain_provider(None)


def test_step7_04_composite_hash_mismatch(client: TestClient, db_session: Session, setup_registered_project):
    """Test 4: On-chain composite hash mismatch is caught and reported."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    tampered_hash = "0x" + "a" * 64

    class HashMismatchProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": tampered_hash,
                "ipfs_root_cid": version.ipfs_root_cid,
                "version_index": 1,
                "lifecycle_stage": "DESIGN",
                "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "co_authors": [],
                "anchored_timestamp": datetime.now(timezone.utc),
                "block_number": 100,
                "dispute_state": "NONE",
                "exists": True,
            }

    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.commit()

    set_blockchain_provider(HashMismatchProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_valid"] is False
        assert data["blockchain_proof"]["match_confirmed"] is False
        assert "hash mismatch" in data["message"].lower()
    finally:
        set_blockchain_provider(None)


def test_step7_05_ipfs_cid_match(client: TestClient, db_session: Session, setup_registered_project):
    """Test 5: On-chain IPFS root CID matches trusted DB CID."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]

    class CIDMatchProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": f"0x{comp_hash}",
                "ipfs_root_cid": version.ipfs_root_cid,
                "version_index": 1,
                "lifecycle_stage": "DESIGN",
                "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "co_authors": [],
                "anchored_timestamp": datetime.now(timezone.utc),
                "block_number": 100,
                "dispute_state": "NONE",
                "exists": True,
            }

    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.commit()

    set_blockchain_provider(CIDMatchProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        assert res.json()["data"]["is_valid"] is True
    finally:
        set_blockchain_provider(None)


def test_step7_06_ipfs_cid_mismatch(client: TestClient, db_session: Session, setup_registered_project):
    """Test 6: On-chain IPFS root CID mismatch is caught and reported."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]

    class CIDMismatchProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": f"0x{comp_hash}",
                "ipfs_root_cid": "bafybeialteredcid00000000000000000000000000000000000000000",
                "version_index": 1,
                "lifecycle_stage": "DESIGN",
                "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "co_authors": [],
                "anchored_timestamp": datetime.now(timezone.utc),
                "block_number": 100,
                "dispute_state": "NONE",
                "exists": True,
            }

    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.commit()

    set_blockchain_provider(CIDMismatchProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_valid"] is False
        assert data["blockchain_proof"]["match_confirmed"] is False
        assert "ipfs root cid mismatch" in data["message"].lower()
    finally:
        set_blockchain_provider(None)


def test_step7_07_version_index_mismatch(client: TestClient, db_session: Session, setup_registered_project):
    """Test 7: On-chain version index mismatch is caught and reported."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]

    class VersionIndexMismatchProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": f"0x{comp_hash}",
                "ipfs_root_cid": version.ipfs_root_cid,
                "version_index": 99,  # Expected 1
                "lifecycle_stage": "DESIGN",
                "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "co_authors": [],
                "anchored_timestamp": datetime.now(timezone.utc),
                "block_number": 100,
                "dispute_state": "NONE",
                "exists": True,
            }

    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.commit()

    set_blockchain_provider(VersionIndexMismatchProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_valid"] is False
        assert "version index mismatch" in data["message"].lower()
    finally:
        set_blockchain_provider(None)


def test_step7_08_lifecycle_stage_mismatch(client: TestClient, db_session: Session, setup_registered_project):
    """Test 8: On-chain lifecycle stage mismatch is caught and reported."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]

    class StageMismatchProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": f"0x{comp_hash}",
                "ipfs_root_cid": version.ipfs_root_cid,
                "version_index": 1,
                "lifecycle_stage": "FINAL",  # Expected DESIGN
                "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "co_authors": [],
                "anchored_timestamp": datetime.now(timezone.utc),
                "block_number": 100,
                "dispute_state": "NONE",
                "exists": True,
            }

    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.commit()

    set_blockchain_provider(StageMismatchProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_valid"] is False
        assert "lifecycle stage mismatch" in data["message"].lower()
    finally:
        set_blockchain_provider(None)


def test_step7_09_author_mismatch(client: TestClient, db_session: Session, setup_registered_project):
    """Test 9: On-chain author wallet mismatch is caught and reported."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]

    # Record with expected author
    record = BlockchainRecord(
        public_id=f"BLK-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=version.id,
        transaction_hash="0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
        block_number=142981,
        smart_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        anchored_hash=f"0x{comp_hash}",
        ipfs_cid_anchored=version.ipfs_root_cid,
        submitter_wallet="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        author_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        network_name="hardhat",
        chain_id=31337,
        anchored_timestamp=datetime.now(timezone.utc),
    )
    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.add(record)
    db_session.commit()

    class AuthorMismatchProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": f"0x{comp_hash}",
                "ipfs_root_cid": version.ipfs_root_cid,
                "version_index": 1,
                "lifecycle_stage": "DESIGN",
                "author": "0x90F79bf6EB2c4f870365E785982E1f101E93b906",  # Discrepancy
                "co_authors": [],
                "anchored_timestamp": datetime.now(timezone.utc),
                "block_number": 142981,
                "dispute_state": "NONE",
                "exists": True,
            }

    set_blockchain_provider(AuthorMismatchProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_valid"] is False
        assert "author wallet mismatch" in data["message"].lower()
    finally:
        set_blockchain_provider(None)


def test_step7_10_co_author_mismatch(client: TestClient, db_session: Session, setup_registered_project, create_verification_user):
    """Test 10: On-chain contributor/co-author mismatch is caught and reported."""
    version = setup_registered_project["version"]
    project = setup_registered_project["project"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]

    # Add a contributor team member to project
    contrib, _ = create_verification_user(email_prefix="contrib")
    contrib.wallet_address = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
    db_session.commit()

    member = ProjectMember(
        project_id=project.id,
        user_id=contrib.id,
        role_in_project=ProjectMemberRole.CONTRIBUTOR,
        is_owner=False,
    )
    db_session.add(member)
    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.commit()

    # On-chain returns different co-authors
    class CoAuthorMismatchProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": f"0x{comp_hash}",
                "ipfs_root_cid": version.ipfs_root_cid,
                "version_index": 1,
                "lifecycle_stage": "DESIGN",
                "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "co_authors": ["0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"],  # Discrepancy
                "anchored_timestamp": datetime.now(timezone.utc),
                "block_number": 142981,
                "dispute_state": "NONE",
                "exists": True,
            }

    set_blockchain_provider(CoAuthorMismatchProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_valid"] is False
        assert "co-author" in data["message"].lower()
    finally:
        set_blockchain_provider(None)


def test_step7_11_invalid_registration_id_formats(client: TestClient):
    """Test 11: Comprehensive malformed registration ID formats rejected with 422."""
    malformed_ids = [
        "BAD-ID",
        "REG-202",
        "REG-2026",
        "REG-2026-",
        "REG-2026-TOOLONG123",
        "reg-2026-lower",
        "REG-2026-!@#$%",
        "REG-ABCD-12345",
    ]
    for bad_id in malformed_ids:
        res = client.get(f"/api/v1/verification/verify-registration/{bad_id}")
        assert res.status_code == 422
        assert res.json()["error"]["code"] == "INVALID_REGISTRATION_ID_FORMAT"


def test_step7_12_rpc_failure_handling(client: TestClient, db_session: Session, setup_registered_project):
    """Test 12: RPC failure does not report ownership invalid; returns controlled 502 error."""
    reg_id = setup_registered_project["registration_id"]

    class RpcErrorProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            raise BlockchainException(
                code="BLOCKCHAIN_CONNECTION_ERROR",
                message="Unable to connect to Ethereum RPC node.",
                status_code=502,
            )

    set_blockchain_provider(RpcErrorProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 502
        assert res.json()["error"]["code"] == "BLOCKCHAIN_CONNECTION_ERROR"
    finally:
        set_blockchain_provider(None)


def test_step7_13_blockchain_timeout_handling(client: TestClient, db_session: Session, setup_registered_project):
    """Test 13: Blockchain timeout raises controlled BLOCKCHAIN_TIMEOUT exception."""
    reg_id = setup_registered_project["registration_id"]

    class TimeoutProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            raise BlockchainException(
                code="BLOCKCHAIN_TIMEOUT",
                message="Smart contract call timed out after 30s.",
                status_code=504,
            )

    set_blockchain_provider(TimeoutProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 504
        assert res.json()["error"]["code"] == "BLOCKCHAIN_TIMEOUT"
    finally:
        set_blockchain_provider(None)


def test_step7_14_contract_read_failure_handling(client: TestClient, db_session: Session, setup_registered_project):
    """Test 14: Contract execution revert/failure returns controlled 502 error."""
    reg_id = setup_registered_project["registration_id"]

    class ContractErrProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            raise BlockchainException(
                code="BLOCKCHAIN_CONTRACT_ERROR",
                message="Smart contract call failed unexpectedly.",
                status_code=502,
            )

    set_blockchain_provider(ContractErrProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 502
        assert res.json()["error"]["code"] == "BLOCKCHAIN_CONTRACT_ERROR"
    finally:
        set_blockchain_provider(None)


def test_step7_15_cross_project_verification_attempt(
    client: TestClient, db_session: Session, setup_registered_project, create_verification_user
):
    """Test 15: Cross-project verification attempt (hash from Project A scoped to Project B) fails."""
    # Project A
    comp_hash_a = setup_registered_project["composite_hash"]

    # Project B
    owner_b, _ = create_verification_user(email_prefix="owner_b")
    unique_b = uuid.uuid4().hex[:5].upper()
    proj_b = Project(
        public_id=f"PRJ-202609-{unique_b}",
        title="Project B",
        slug=f"project-b-{unique_b.lower()}",
        abstract="Abstract B",
        category="AI",
        department="EE",
        academic_year="2025-2026",
        current_lifecycle_stage=ProjectVersionStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(proj_b)
    db_session.flush()

    ver_b = ProjectVersion(
        public_id=f"VER-202609-{unique_b}",
        registration_id=f"REG-2026-{unique_b}",
        project_id=proj_b.id,
        version_index=1,
        version_tag="v1.0",
        title="Ver B",
        lifecycle_stage=ProjectVersionStage.IDEA,
        composite_sha256=hashlib.sha256(b"project_b_unique_hash").hexdigest(),
        anchoring_status=AnchoringStatus.PENDING,
    )
    db_session.add(ver_b)
    db_session.commit()

    # Query with Project A hash but scoped to Project B registration ID
    res = client.post(
        "/api/v1/verification/verify-hash",
        json={
            "sha256_hash": comp_hash_a,
            "registration_id": f"REG-2026-{unique_b}",
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is False
    assert "does not match" in data["message"].lower() or "different" in data["message"].lower()


def test_step7_16_client_wallet_injection_attempt(
    client: TestClient, db_session: Session, setup_registered_project
):
    """Test 16: Verification API never trusts client-supplied wallet headers/params."""
    reg_id = setup_registered_project["registration_id"]

    # Supply an unauthorized client wallet claim in headers
    res = client.get(
        f"/api/v1/verification/verify-registration/{reg_id}",
        headers={"X-Author-Wallet": "0xEvilAttackerWallet11111111111111111111111"},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    # Verify authoritative author is preserved and evil wallet is not reflected
    if data["blockchain_proof"]:
        assert "0xEvil" not in data["blockchain_proof"]["author_wallet"]


def test_step7_17_client_hash_injection_attempt(
    client: TestClient, db_session: Session, setup_registered_project
):
    """Test 17: Submitting an arbitrary hash for a registered project is detected and rejected."""
    reg_id = setup_registered_project["registration_id"]
    arbitrary_fake_hash = "f" * 64

    res = client.post(
        "/api/v1/verification/verify-hash",
        json={
            "sha256_hash": arbitrary_fake_hash,
            "registration_id": reg_id,
        },
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is False
    assert "does not match" in data["message"].lower()


def test_step7_18_verification_after_successful_anchoring(
    client: TestClient, db_session: Session, setup_registered_project
):
    """Test 18: Successfully anchored project version produces fully verified response."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]

    record = BlockchainRecord(
        public_id=f"BLK-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=version.id,
        transaction_hash="0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
        block_number=142981,
        smart_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        anchored_hash=f"0x{comp_hash}",
        ipfs_cid_anchored=version.ipfs_root_cid,
        submitter_wallet="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        author_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        network_name="hardhat",
        chain_id=31337,
        anchored_timestamp=datetime.now(timezone.utc),
    )
    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.add(record)
    db_session.commit()

    res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is True
    assert data["anchoring_status"] == "ANCHORED"
    assert data["blockchain_proof"]["match_confirmed"] is True


def test_step7_19_verification_after_failed_anchoring(
    client: TestClient, db_session: Session, setup_registered_project
):
    """Test 19: State Rule: FAILED anchoring is NEVER reported as a verified proof."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]

    version.anchoring_status = AnchoringStatus.FAILED
    db_session.commit()

    # 1. By registration ID
    res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["is_valid"] is False
    assert data["blockchain_proof"] is None
    assert "anchoring failed" in data["message"].lower()

    # 2. By hash
    res_hash = client.post(
        "/api/v1/verification/verify-hash",
        json={"sha256_hash": comp_hash},
    )
    assert res_hash.status_code == 200
    data_hash = res_hash.json()["data"]
    assert data_hash["is_valid"] is False
    assert data_hash["blockchain_proof"] is None
    assert "anchoring failed" in data_hash["message"].lower()


def test_step7_20_verification_consistency_with_blockchain_record(
    client: TestClient, db_session: Session, setup_registered_project
):
    """Test 20: BlockchainRecord discrepancy against on-chain data marks match_confirmed=False."""
    version = setup_registered_project["version"]
    reg_id = setup_registered_project["registration_id"]
    comp_hash = setup_registered_project["composite_hash"]

    record = BlockchainRecord(
        public_id=f"BLK-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=version.id,
        transaction_hash="0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
        block_number=142981,
        smart_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        anchored_hash=f"0x{comp_hash}",
        ipfs_cid_anchored=version.ipfs_root_cid,
        submitter_wallet="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        author_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        network_name="hardhat",
        chain_id=31337,
        anchored_timestamp=datetime.now(timezone.utc),
    )
    version.anchoring_status = AnchoringStatus.ANCHORED
    db_session.add(record)
    db_session.commit()

    # On-chain block number is different from DB record
    class DiscrepantBlockProvider(BlockchainVerificationProvider):
        async def get_project_version(self, registration_id: str):
            return {
                "record_id": 1,
                "registration_id": reg_id,
                "composite_hash": f"0x{comp_hash}",
                "ipfs_root_cid": version.ipfs_root_cid,
                "version_index": 1,
                "lifecycle_stage": "DESIGN",
                "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "co_authors": [],
                "anchored_timestamp": datetime.now(timezone.utc),
                "block_number": 999999,  # Mismatch against record.block_number 142981
                "dispute_state": "NONE",
                "exists": True,
            }

    set_blockchain_provider(DiscrepantBlockProvider())
    try:
        res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["is_valid"] is False
        assert data["blockchain_proof"]["match_confirmed"] is False
        assert "blockchain record mismatch" in data["message"].lower()
    finally:
        set_blockchain_provider(None)


@pytest.mark.asyncio
async def test_step7_21_verify_ipfs_artifact_content_validation():
    """Test 21: verify_ipfs_artifact_content validates content hash, CID format, and rejects tampering."""
    from unittest.mock import AsyncMock, MagicMock
    from app.services.verification_service import verify_ipfs_artifact_content
    from app.storage.ipfs_adapter import IPFSStorageAdapter

    test_content = b"sample artifact content for IPFS testing"
    correct_hash = hashlib.sha256(test_content).hexdigest()
    valid_cid = "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"

    mock_ipfs = MagicMock(spec=IPFSStorageAdapter)
    mock_ipfs.cat = AsyncMock(return_value=test_content)

    # 1. Matching content
    assert await verify_ipfs_artifact_content(valid_cid, correct_hash, ipfs_adapter=mock_ipfs) is True

    # 2. Tampered hash
    wrong_hash = hashlib.sha256(b"tampered content").hexdigest()
    assert await verify_ipfs_artifact_content(valid_cid, wrong_hash, ipfs_adapter=mock_ipfs) is False

    # 3. Invalid CID format raises ValidationException
    with pytest.raises(ValidationException, match="Invalid IPFS CID format"):
        await verify_ipfs_artifact_content("invalid-cid-string", correct_hash, ipfs_adapter=mock_ipfs)
