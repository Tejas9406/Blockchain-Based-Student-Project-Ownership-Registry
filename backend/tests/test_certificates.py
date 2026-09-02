import uuid
from datetime import datetime, timezone
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BlockchainException
from app.core.security import create_access_token, hash_password
from app.models.artifact import Artifact
from app.models.blockchain_record import BlockchainRecord
from app.models.dispute import Dispute
from app.models.enums import (
    AnchoringStatus,
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
from app.schemas.verification import (
    VerificationBlockchainProof,
    VerificationProjectSummary,
    VerificationResponseData,
    VerificationVersionSummary,
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def create_test_user(db_session: Session):
    """Factory fixture to create test users with specific roles and auth tokens."""
    def _create(
        email_prefix: str = "user",
        role: UserRole = UserRole.STUDENT,
        department: str = "Computer Science",
    ) -> Tuple[User, str]:
        uid = uuid.uuid4().hex[:6]
        user = User(
            public_id=f"USR-202609-{uid[:5].upper()}",
            email=f"{email_prefix}_{uid}@sih2026.edu",
            hashed_password=hash_password("SecurePass123!"),
            full_name=f"Student {email_prefix.capitalize()}",
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
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            email=user.email,
        )
        return user, token

    return _create


@pytest.fixture
def anchored_project(db_session: Session, create_test_user):
    """Sets up an anchored project with version, member, and blockchain record."""
    owner, owner_token = create_test_user(email_prefix="owner", role=UserRole.STUDENT)
    suffix = uuid.uuid4().hex[:5].upper()
    proj_public_id = f"PRJ-202609-{suffix}"
    reg_id = f"REG-2026-{suffix}"

    project = Project(
        public_id=proj_public_id,
        title="Decentralized Identity & Ownership Protocol",
        slug=f"decentralized-identity-{suffix.lower()}",
        abstract="Self-sovereign project ownership for students.",
        category="Cybersecurity & Blockchain",
        department="Computer Science",
        academic_year="2025-2026",
        current_lifecycle_stage=ProjectVersionStage.FINAL,
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

    composite_hash = "a" * 64
    ipfs_cid = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"

    version = ProjectVersion(
        public_id=f"VER-202609-{suffix}",
        project_id=project.id,
        version_tag="v1.0",
        version_index=1,
        lifecycle_stage=ProjectVersionStage.FINAL,
        title="Final Milestone Implementation",
        description="Complete project milestone.",
        composite_sha256=composite_hash,
        ipfs_root_cid=ipfs_cid,
        anchoring_status=AnchoringStatus.ANCHORED,
        registration_id=reg_id,
        dispute_status=DisputeStatus.NONE,
    )
    db_session.add(version)
    db_session.flush()

    record = BlockchainRecord(
        public_id=f"BCR-202609-{suffix}",
        version_id=version.id,
        transaction_hash="0x" + "1" * 64,
        block_number=100,
        block_hash="0x" + "2" * 64,
        onchain_record_id=1,
        smart_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        anchored_hash="0x" + composite_hash,
        ipfs_cid_anchored=ipfs_cid,
        submitter_wallet="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        author_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        network_name="hardhat",
        chain_id=31337,
        anchored_timestamp=datetime(2026, 8, 31, 18, 50, 0, tzinfo=timezone.utc),
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(project)
    db_session.refresh(version)
    db_session.refresh(record)

    return {
        "owner": owner,
        "owner_token": owner_token,
        "project": project,
        "version": version,
        "record": record,
        "registration_id": reg_id,
        "composite_hash": composite_hash,
        "ipfs_cid": ipfs_cid,
    }


def _mock_successful_verification(reg_id: str, comp_hash: str, cid: str, dispute_status: str = "NONE") -> VerificationResponseData:
    """Helper creating a successful VerificationResponseData object."""
    return VerificationResponseData(
        is_valid=(dispute_status in ("NONE", "REJECTED")),
        registration_id=reg_id,
        verification_method="REGISTRATION_ID",
        anchoring_status="ANCHORED",
        project=VerificationProjectSummary(
            public_id="PRJ-202609-TEST1",
            title="Decentralized Identity & Ownership Protocol",
            department="Computer Science",
            institution_name="National Institute of Technology",
        ),
        version=VerificationVersionSummary(
            version_tag="v1.0",
            lifecycle_stage="FINAL",
            composite_sha256=comp_hash,
            ipfs_root_cid=cid,
        ),
        blockchain_proof=VerificationBlockchainProof(
            transaction_hash="0x" + "1" * 64,
            block_number=100,
            block_timestamp=datetime(2026, 8, 31, 18, 50, 0, tzinfo=timezone.utc),
            smart_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
            author_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
            dispute_status=dispute_status,
            match_confirmed=True,
        ),
        message="Cryptographic proof confirmed on-chain.",
    )


# ==============================================================================
# TESTS (24 Comprehensive Scenarios)
# ==============================================================================

def test_01_successful_certificate_generation(client: TestClient, anchored_project):
    """Scenario 1: Successful PDF certificate generation for an anchored project version."""
    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert f'filename="ownership-certificate-{reg_id}.pdf"' in resp.headers["content-disposition"]
    assert resp.content.startswith(b"%PDF-1.4")
    assert b"%%EOF" in resp.content


def test_02_invalid_registration_id_format(client: TestClient):
    """Scenario 2: Malformed registration ID format returns 422 INVALID_REGISTRATION_ID_FORMAT."""
    for malformed_id in ["INVALID-ID", "REG-2026-", "REG-26-A8F92", "REG-2026-A8F92D-EXTRA"]:
        resp = client.get(f"/api/v1/certificates/{malformed_id}/download")
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "INVALID_REGISTRATION_ID_FORMAT"


def test_03_nonexistent_version(client: TestClient):
    """Scenario 3: Certificate request for nonexistent registration ID returns 404."""
    resp = client.get("/api/v1/certificates/REG-2026-99999/download")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "REGISTRATION_NOT_FOUND"


def test_04_version_not_anchored_draft(client: TestClient, db_session: Session, anchored_project):
    """Scenario 4: Certificate request for unanchored (DRAFT) version is rejected with 400."""
    version = anchored_project["version"]
    version.anchoring_status = AnchoringStatus.DRAFT
    db_session.commit()

    reg_id = anchored_project["registration_id"]
    resp = client.get(f"/api/v1/certificates/{reg_id}/download")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VERSION_NOT_ANCHORED"


def test_05_failed_version(client: TestClient, db_session: Session, anchored_project):
    """Scenario 5: Certificate request for FAILED version is rejected with 400."""
    version = anchored_project["version"]
    version.anchoring_status = AnchoringStatus.FAILED
    db_session.commit()

    reg_id = anchored_project["registration_id"]
    resp = client.get(f"/api/v1/certificates/{reg_id}/download")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VERSION_NOT_ANCHORED"


def test_06_missing_blockchain_record(client: TestClient, db_session: Session, anchored_project):
    """Scenario 6: Anchored version missing a BlockchainRecord is rejected with 400."""
    record = anchored_project["record"]
    db_session.delete(record)
    db_session.commit()

    reg_id = anchored_project["registration_id"]
    resp = client.get(f"/api/v1/certificates/{reg_id}/download")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "BLOCKCHAIN_RECORD_NOT_FOUND"


def test_07_blockchain_verification_failure(client: TestClient, anchored_project):
    """Scenario 7: Blockchain verification failure prevents certificate generation."""
    reg_id = anchored_project["registration_id"]

    with patch(
        "app.services.certificate_service.verify_by_registration_id",
        AsyncMock(side_effect=BlockchainException(code="BLOCKCHAIN_TIMEOUT", message="Timed out", status_code=504)),
    ):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 504


def test_08_hash_mismatch(client: TestClient, anchored_project):
    """Scenario 8: Cryptographic hash mismatch between DB and chain rejects certificate."""
    reg_id = anchored_project["registration_id"]
    mismatch_ver = _mock_successful_verification(reg_id, "b" * 64, anchored_project["ipfs_cid"])
    mismatch_ver.blockchain_proof.match_confirmed = False
    mismatch_ver.message = "Cryptographic hash mismatch: on-chain composite hash does not match."

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mismatch_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CRYPTOGRAPHIC_MISMATCH"


def test_09_cid_mismatch(client: TestClient, anchored_project):
    """Scenario 9: IPFS root CID mismatch between DB and chain rejects certificate."""
    reg_id = anchored_project["registration_id"]
    mismatch_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], "bafybeimismatched")
    mismatch_ver.blockchain_proof.match_confirmed = False
    mismatch_ver.message = "IPFS CID mismatch: on-chain root CID does not match."

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mismatch_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CRYPTOGRAPHIC_MISMATCH"


def test_10_active_dispute_open(client: TestClient, db_session: Session, anchored_project):
    """Scenario 10: Active dispute (OPEN) rejects certificate generation with 409 Conflict."""
    reg_id = anchored_project["registration_id"]
    version = anchored_project["version"]
    version.dispute_status = DisputeStatus.OPEN
    db_session.commit()

    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"], dispute_status="OPEN")
    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ACTIVE_DISPUTE_EXISTS"


def test_11_rejected_dispute_permits_certificate(client: TestClient, db_session: Session, anchored_project):
    """Scenario 11: When a dispute is REJECTED (dismissed), certificate generation succeeds."""
    reg_id = anchored_project["registration_id"]
    version = anchored_project["version"]
    version.dispute_status = DisputeStatus.REJECTED
    db_session.commit()

    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"], dispute_status="REJECTED")
    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF-1.4")
    assert b"DISPUTE DISMISSED" in resp.content


def test_12_resolved_dispute_rejects_certificate(client: TestClient, db_session: Session, anchored_project):
    """Scenario 12: When dispute is RESOLVED (upheld against version), certificate generation is blocked with 409."""
    reg_id = anchored_project["registration_id"]
    version = anchored_project["version"]
    version.dispute_status = DisputeStatus.RESOLVED
    db_session.commit()

    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"], dispute_status="RESOLVED")
    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "DISPUTED_VERSION_CANNOT_GENERATE_CERTIFICATE"


def test_13_metadata_endpoint_public_access(client: TestClient, anchored_project):
    """Scenario 13: Metadata endpoint /certificates/{id} is public and returns valid structure."""
    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["registration_id"] == reg_id
    assert data["project_title"] == "Decentralized Identity & Ownership Protocol"
    assert data["version_tag"] == "v1.0"
    assert data["transaction_hash"] == "0x" + "1" * 64
    assert data["verification_url"].endswith(f"/verify/{reg_id}")
    assert data["pdf_download_url"].endswith(f"/certificates/{reg_id}/download")


def test_14_registration_id_exact_five_char_suffix_enforced(client: TestClient):
    """Scenario 14: Registration IDs with suffix != 5 chars (e.g. 4 or 6 chars) are rejected with 422."""
    # 4 characters suffix: rejected
    resp_short = client.get("/api/v1/certificates/REG-2026-ABCD/download")
    assert resp_short.status_code == 422
    assert resp_short.json()["error"]["code"] == "INVALID_REGISTRATION_ID_FORMAT"

    # 6 characters suffix: rejected
    resp_long = client.get("/api/v1/certificates/REG-2026-ABCDEF/download")
    assert resp_long.status_code == 422
    assert resp_long.json()["error"]["code"] == "INVALID_REGISTRATION_ID_FORMAT"


def test_15_long_project_name_wrapped_safely(client: TestClient, db_session: Session, anchored_project):
    """Scenario 15: Extremely long project titles are safely wrapped without overflowing or crashing."""
    project = anchored_project["project"]
    project.title = "A" * 50 + " Autonomous Distributed Decentralized Blockchain Protocol with High-Throughput Smart Contracts " * 2
    db_session.commit()

    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF-1.4")
    assert b"%%EOF" in resp.content


def test_16_multiple_authors_rendered(client: TestClient, db_session: Session, anchored_project, create_test_user):
    """Scenario 16: Multiple authors and team members are safely rendered in certificate."""
    project = anchored_project["project"]
    for i in range(3):
        u, _ = create_test_user(email_prefix=f"collab{i}")
        m = ProjectMember(
            project_id=project.id,
            user_id=u.id,
            role_in_project=ProjectMemberRole.CONTRIBUTOR,
            is_owner=False,
        )
        db_session.add(m)
    db_session.commit()

    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF-1.4")
    assert b"Student Collab0" in resp.content


def test_17_malicious_characters_in_project_name(client: TestClient, db_session: Session, anchored_project):
    """Scenario 17: Special and malicious characters in text are escaped safely for PDF Type 1 fonts."""
    project = anchored_project["project"]
    project.title = "Project <script>alert('XSS')</script> & (Parens) \\ Backslash \"Quotes\""
    db_session.commit()

    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF-1.4")
    assert b"%%EOF" in resp.content


def test_18_certificate_pdf_binary_is_valid(client: TestClient, anchored_project):
    """Scenario 18: Validates PDF 1.4 internal structure (Header, Objects, Catalog, Pages, xref, trailer, startxref)."""
    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    content = resp.content
    assert content.startswith(b"%PDF-1.4")
    assert b"1 0 obj" in content
    assert b"/Type /Catalog" in content
    assert b"xref" in content
    assert b"trailer" in content
    assert b"startxref" in content
    assert b"%%EOF" in content


def test_19_correct_content_type(client: TestClient, anchored_project):
    """Scenario 19: Content-Type is strictly application/pdf."""
    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.headers["content-type"] == "application/pdf"


def test_20_safe_content_disposition_filename(client: TestClient, anchored_project):
    """Scenario 20: Safe, standardized Content-Disposition filename based only on registration ID."""
    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    expected_filename = f'ownership-certificate-{reg_id}.pdf'
    assert resp.headers["content-disposition"] == f'inline; filename="{expected_filename}"'


def test_21_no_internal_uuid_leakage(client: TestClient, anchored_project):
    """Scenario 21: Ensures internal database UUIDs are never exposed in the generated certificate PDF."""
    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    proj_uuid = str(anchored_project["project"].id).encode()
    ver_uuid = str(anchored_project["version"].id).encode()
    owner_uuid = str(anchored_project["owner"].id).encode()

    assert proj_uuid not in resp.content
    assert ver_uuid not in resp.content
    assert owner_uuid not in resp.content


def test_22_no_database_mutation_during_generation(client: TestClient, db_session: Session, anchored_project):
    """Scenario 22: Certificate generation causes zero database mutations."""
    users_before = len(db_session.execute(select(User)).scalars().all())
    projects_before = len(db_session.execute(select(Project)).scalars().all())
    versions_before = len(db_session.execute(select(ProjectVersion)).scalars().all())
    records_before = len(db_session.execute(select(BlockchainRecord)).scalars().all())
    disputes_before = len(db_session.execute(select(Dispute)).scalars().all())
    artifacts_before = len(db_session.execute(select(Artifact)).scalars().all())

    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp.status_code == 200

    users_after = len(db_session.execute(select(User)).scalars().all())
    projects_after = len(db_session.execute(select(Project)).scalars().all())
    versions_after = len(db_session.execute(select(ProjectVersion)).scalars().all())
    records_after = len(db_session.execute(select(BlockchainRecord)).scalars().all())
    disputes_after = len(db_session.execute(select(Dispute)).scalars().all())
    artifacts_after = len(db_session.execute(select(Artifact)).scalars().all())

    assert users_before == users_after
    assert projects_before == projects_after
    assert versions_before == versions_after
    assert records_before == records_after
    assert disputes_before == disputes_after
    assert artifacts_before == artifacts_after


def test_23_blockchain_proof_data_matches_certificate(client: TestClient, anchored_project):
    """Scenario 23: On-chain transaction hash, block number, and composite hash are embedded in certificate."""
    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp = client.get(f"/api/v1/certificates/{reg_id}/download")

    content = resp.content
    assert anchored_project["record"].transaction_hash.encode() in content
    assert str(anchored_project["record"].block_number).encode() in content
    assert anchored_project["composite_hash"].encode() in content


def test_24_repeated_generation_idempotence(client: TestClient, anchored_project):
    """Scenario 24: Repeated calls produce identical, deterministic, valid certificates without error."""
    reg_id = anchored_project["registration_id"]
    mock_ver = _mock_successful_verification(reg_id, anchored_project["composite_hash"], anchored_project["ipfs_cid"])

    with patch("app.services.certificate_service.verify_by_registration_id", AsyncMock(return_value=mock_ver)):
        resp1 = client.get(f"/api/v1/certificates/{reg_id}/download")
        resp2 = client.get(f"/api/v1/certificates/{reg_id}/download")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.content == resp2.content
