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
from app.models.blockchain_record import BlockchainRecord
from app.models.dispute import Dispute
from app.models.enums import (
    AnchoringStatus,
    DisputeStatus,
    DisputeType,
    ProjectStatus,
    ProjectVersionStage,
    ProjectVisibility,
    UserRole,
)
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User


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
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            email=user.email,
        )
        return user, token

    return _create


@pytest.fixture
def anchored_project(db_session: Session, create_test_user):
    """Sets up an anchored project with version and blockchain record."""
    owner, owner_token = create_test_user(email_prefix="owner", role=UserRole.STUDENT)
    suffix = uuid.uuid4().hex[:5].upper()
    proj_public_id = f"PRJ-202609-{suffix}"
    reg_id = f"REG-2026-{suffix}"

    project = Project(
        public_id=proj_public_id,
        title="Decentralized Identity Protocol",
        slug=f"decentralized-identity-{suffix.lower()}",
        abstract="Self-sovereign identity for students.",
        category="Cybersecurity & Blockchain",
        department="Computer Science",
        academic_year="2025-2026",
        current_lifecycle_stage=ProjectVersionStage.FINAL,
        visibility=ProjectVisibility.PUBLIC,
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(project)
    db_session.flush()

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
        anchored_timestamp=datetime.now(timezone.utc),
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


# ==============================================================================
# TESTS (24 Comprehensive Scenarios)
# ==============================================================================

def test_01_successful_dispute_creation(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 1: Authenticated student raises dispute with valid registration ID."""
    claimant, token = create_test_user(email_prefix="claimant", role=UserRole.STUDENT)
    reg_id = anchored_project["registration_id"]

    mock_bc = MagicMock()
    mock_bc.raise_dispute = AsyncMock(return_value={
        "transaction_hash": "0x" + "d" * 64,
        "block_number": 105,
        "event_data": {"registrationId": reg_id, "evidenceCID": "bafybeievidence"},
    })

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "PLAGIARISM",
                "claim_description": "Respondent copied our methodology and evaluation benchmarks from arXiv:2401.12345.",
                "evidence_url": "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m",
            },
        )

    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["public_id"].startswith("DSP-")
    assert data["status"] == "OPEN"
    assert data["dispute_type"] == "PLAGIARISM"
    assert data["registration_id"] == reg_id
    assert data["transaction_hash"] == "0x" + "d" * 64
    assert data["claimant"]["public_id"] == claimant.public_id

    # Verify database state
    db_session.expire_all()
    version = db_session.execute(select(ProjectVersion).where(ProjectVersion.registration_id == reg_id)).scalar_one()
    assert version.dispute_status == DisputeStatus.OPEN
    project = db_session.execute(select(Project).where(Project.id == version.project_id)).scalar_one()
    assert project.status == ProjectStatus.UNDER_DISPUTE


def test_02_registration_not_found(client: TestClient, create_test_user):
    """Scenario 2: Filing dispute against nonexistent registration ID returns 404."""
    _, token = create_test_user(role=UserRole.STUDENT)
    resp = client.post(
        "/api/v1/disputes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "registration_id": "REG-2026-99999",
            "dispute_type": "PLAGIARISM",
            "claim_description": "Valid claim explanation exceeding minimum length requirements.",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "REGISTRATION_NOT_FOUND"


def test_03_version_not_anchored(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 3: Filing dispute against an unanchored version (DRAFT/PENDING) returns 400."""
    _, token = create_test_user(role=UserRole.STUDENT)
    version = anchored_project["version"]
    version.anchoring_status = AnchoringStatus.DRAFT
    db_session.commit()

    resp = client.post(
        "/api/v1/disputes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "registration_id": anchored_project["registration_id"],
            "dispute_type": "UNAUTHORIZED_USE",
            "claim_description": "Target project version is in draft state and cannot be disputed.",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VERSION_NOT_ANCHORED"


def test_04_unauthorized_dispute_creation(client: TestClient, anchored_project):
    """Scenario 4: Request without Authorization header returns 401."""
    resp = client.post(
        "/api/v1/disputes",
        json={
            "registration_id": anchored_project["registration_id"],
            "dispute_type": "PLAGIARISM",
            "claim_description": "Valid claim description without authorization token.",
        },
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_TOKEN"


def test_05_cross_project_dispute_attempt(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 5: Specifying registration ID with a mismatched project ID returns 400 CROSS_PROJECT_DISPUTE."""
    _, token = create_test_user(role=UserRole.STUDENT)
    # Create another project
    other_proj = Project(
        public_id="PRJ-202609-OTHER",
        title="Other Project",
        slug="other-project",
        category="Web",
        department="IT",
        academic_year="2025-2026",
    )
    db_session.add(other_proj)
    db_session.commit()

    resp = client.post(
        "/api/v1/disputes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "registration_id": anchored_project["registration_id"],
            "project_id": "PRJ-202609-OTHER",
            "dispute_type": "PLAGIARISM",
            "claim_description": "Attempting cross-project dispute injection.",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CROSS_PROJECT_DISPUTE"


def test_06_invalid_registration_id_format(client: TestClient, create_test_user):
    """Scenario 6: Malformed registration ID returns 422 validation error."""
    _, token = create_test_user(role=UserRole.STUDENT)
    resp = client.post(
        "/api/v1/disputes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "registration_id": "INVALID-REG-FORMAT",
            "dispute_type": "PLAGIARISM",
            "claim_description": "Claim description valid length string.",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_REGISTRATION_ID_FORMAT"


def test_07_empty_or_short_claim_description(client: TestClient, create_test_user, anchored_project):
    """Scenario 7: Claim description shorter than 10 characters returns 422 validation error."""
    _, token = create_test_user(role=UserRole.STUDENT)
    resp = client.post(
        "/api/v1/disputes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "registration_id": anchored_project["registration_id"],
            "dispute_type": "PLAGIARISM",
            "claim_description": "Too short",
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_08_duplicate_active_dispute_db(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 8: Raising a dispute when an active dispute already exists returns 409 CONFLICT."""
    claimant, token = create_test_user(role=UserRole.STUDENT)
    reg_id = anchored_project["registration_id"]
    project = anchored_project["project"]

    # Pre-create an active dispute in DB
    existing_dispute = Dispute(
        public_id="DSP-202609-EXIST",
        project_id=project.id,
        claimant_user_id=claimant.id,
        dispute_type=DisputeType.PLAGIARISM,
        claim_description="Prior ongoing claim.",
        status=DisputeStatus.OPEN,
    )
    db_session.add(existing_dispute)
    anchored_project["version"].dispute_status = DisputeStatus.OPEN
    db_session.commit()

    resp = client.post(
        "/api/v1/disputes",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "registration_id": reg_id,
            "dispute_type": "CITATION_FAILURE",
            "claim_description": "Second dispute filed while first is still active.",
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ACTIVE_DISPUTE_EXISTS"


def test_09_blockchain_transaction_details_captured(client: TestClient, create_test_user, anchored_project):
    """Scenario 9: Confirms on-chain transaction hash and block number are captured."""
    _, token = create_test_user(role=UserRole.STUDENT)
    reg_id = anchored_project["registration_id"]

    mock_bc = MagicMock()
    mock_bc.raise_dispute = AsyncMock(return_value={
        "transaction_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        "block_number": 204,
        "event_data": {"registrationId": reg_id, "evidenceCID": "bafybeievidence"},
    })

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "PLAGIARISM",
                "claim_description": "Verified on-chain anchoring of the dispute claim.",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["data"]["transaction_hash"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"


def test_10_blockchain_transaction_revert_activedisputeexists(client: TestClient, create_test_user, anchored_project):
    """Scenario 10: Contract revert ActiveDisputeExists maps cleanly to 409 CONFLICT."""
    _, token = create_test_user(role=UserRole.STUDENT)
    reg_id = anchored_project["registration_id"]

    mock_bc = MagicMock()
    mock_bc.raise_dispute = AsyncMock(side_effect=BlockchainException(
        code="ACTIVE_DISPUTE_EXISTS",
        message=f"An active dispute already exists for registration '{reg_id}'.",
        status_code=409,
    ))

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "PLAGIARISM",
                "claim_description": "Dispute that reverts on blockchain with ActiveDisputeExists.",
            },
        )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ACTIVE_DISPUTE_EXISTS"


def test_11_blockchain_timeout_handling(client: TestClient, create_test_user, anchored_project):
    """Scenario 11: Blockchain receipt timeout returns 504 GATEWAY_TIMEOUT."""
    _, token = create_test_user(role=UserRole.STUDENT)
    reg_id = anchored_project["registration_id"]

    mock_bc = MagicMock()
    mock_bc.raise_dispute = AsyncMock(side_effect=BlockchainException(
        code="BLOCKCHAIN_TIMEOUT",
        message="raiseDispute transaction timed out after 120 seconds.",
        status_code=504,
    ))

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "PLAGIARISM",
                "claim_description": "Dispute transaction that triggers blockchain timeout.",
            },
        )
    assert resp.status_code == 504
    assert resp.json()["error"]["code"] == "BLOCKCHAIN_TIMEOUT"


def test_12_rpc_failure_handling(client: TestClient, create_test_user, anchored_project):
    """Scenario 12: Web3 provider connection failure returns 502 BAD_GATEWAY."""
    _, token = create_test_user(role=UserRole.STUDENT)
    reg_id = anchored_project["registration_id"]

    mock_bc = MagicMock()
    mock_bc.raise_dispute = AsyncMock(side_effect=BlockchainException(
        code="BLOCKCHAIN_CONNECTION_ERROR",
        message="RPC connection refused at http://127.0.0.1:8545.",
        status_code=502,
    ))

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "PLAGIARISM",
                "claim_description": "Dispute call encountering dead RPC endpoint.",
            },
        )
    assert resp.status_code == 502
    assert resp.json()["error"]["code"] == "BLOCKCHAIN_CONNECTION_ERROR"


def test_13_event_decoding_graceful(client: TestClient, create_test_user, anchored_project):
    """Scenario 13: Receipt mined but event log processing empty gracefully succeeds."""
    _, token = create_test_user(role=UserRole.STUDENT)
    reg_id = anchored_project["registration_id"]

    mock_bc = MagicMock()
    mock_bc.raise_dispute = AsyncMock(return_value={
        "transaction_hash": "0x" + "f" * 64,
        "block_number": 115,
        "event_data": None,
    })

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "OTHER",
                "claim_description": "Testing missing event log handling in receipt.",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["data"]["transaction_hash"] == "0x" + "f" * 64


def test_14_database_failure_recovery_rollback(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 14: When blockchain fails, DB session is rolled back and no partial dispute record persists."""
    _, token = create_test_user(role=UserRole.STUDENT)
    reg_id = anchored_project["registration_id"]
    project_id = anchored_project["project"].id

    mock_bc = MagicMock()
    mock_bc.raise_dispute = AsyncMock(side_effect=BlockchainException(
        code="BLOCKCHAIN_TRANSACTION_FAILED",
        message="Simulated transaction revert.",
        status_code=502,
    ))

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "PLAGIARISM",
                "claim_description": "Dispute that will fail at blockchain level and require DB rollback.",
            },
        )
    assert resp.status_code == 502

    # Verify no partial dispute was committed in DB
    dispute_in_db = db_session.execute(
        select(Dispute).where(
            Dispute.claim_description == "Dispute that will fail at blockchain level and require DB rollback."
        )
    ).scalar_one_or_none()
    assert dispute_in_db is None


def test_15_duplicate_idempotency_request(client: TestClient, create_test_user, anchored_project):
    """Scenario 15: Repeated dispute submission against same target is rejected as active dispute."""
    _, token = create_test_user(role=UserRole.STUDENT)
    reg_id = anchored_project["registration_id"]

    mock_bc = MagicMock()
    mock_bc.raise_dispute = AsyncMock(return_value={
        "transaction_hash": "0x" + "1" * 64,
        "block_number": 101,
        "event_data": {"registrationId": reg_id, "evidenceCID": "bafybeievidence"},
    })

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp1 = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "PLAGIARISM",
                "claim_description": "First submission of the dispute claim.",
            },
        )
        assert resp1.status_code == 201

        # Second submission immediately follows
        resp2 = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "PLAGIARISM",
                "claim_description": "Second submission of the exact same dispute claim.",
            },
        )
        assert resp2.status_code == 409
        assert resp2.json()["error"]["code"] == "ACTIVE_DISPUTE_EXISTS"


def test_16_concurrent_dispute_creation_protection(client: TestClient, create_test_user, anchored_project):
    """Scenario 16: Multiple claimants cannot file concurrent disputes on same project."""
    _, token1 = create_test_user(email_prefix="claimant1", role=UserRole.STUDENT)
    _, token2 = create_test_user(email_prefix="claimant2", role=UserRole.FACULTY)
    reg_id = anchored_project["registration_id"]

    mock_bc = MagicMock()
    mock_bc.raise_dispute = AsyncMock(return_value={
        "transaction_hash": "0x" + "2" * 64,
        "block_number": 102,
        "event_data": {"registrationId": reg_id, "evidenceCID": "bafybeievidence"},
    })

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp1 = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "PLAGIARISM",
                "claim_description": "Claimant 1 files first dispute claim.",
            },
        )
        assert resp1.status_code == 201

        resp2 = client.post(
            "/api/v1/disputes",
            headers={"Authorization": f"Bearer {token2}"},
            json={
                "registration_id": reg_id,
                "dispute_type": "CITATION_FAILURE",
                "claim_description": "Claimant 2 files concurrent dispute claim.",
            },
        )
        assert resp2.status_code == 409
        assert resp2.json()["error"]["code"] == "ACTIVE_DISPUTE_EXISTS"


def test_17_successful_dispute_resolution_admin(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 17: Admin successfully adjudicates active dispute (RESOLVED or REJECTED)."""
    _, admin_token = create_test_user(email_prefix="admin", role=UserRole.ADMIN)
    reg_id = anchored_project["registration_id"]
    project = anchored_project["project"]
    version = anchored_project["version"]

    claimant, _ = create_test_user(email_prefix="claimant")
    dispute = Dispute(
        public_id="DSP-202609-ADJUD",
        project_id=project.id,
        claimant_user_id=claimant.id,
        dispute_type=DisputeType.PLAGIARISM,
        claim_description="Valid claim under review.",
        status=DisputeStatus.OPEN,
    )
    db_session.add(dispute)
    version.dispute_status = DisputeStatus.OPEN
    project.status = ProjectStatus.UNDER_DISPUTE
    db_session.commit()

    mock_bc = MagicMock()
    mock_bc.resolve_dispute = AsyncMock(return_value={
        "transaction_hash": "0x" + "e" * 64,
        "block_number": 110,
        "event_data": {"registrationId": reg_id, "status": 4},  # REJECTED
    })

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.patch(
            f"/api/v1/admin/disputes/{dispute.public_id}/adjudicate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "resolution_status": "REJECTED",
                "resolution_notes": "Claimant failed to demonstrate prior art; on-chain timestamp confirms respondent precedence.",
            },
        )

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "REJECTED"
    assert data["resolution_notes"] == "Claimant failed to demonstrate prior art; on-chain timestamp confirms respondent precedence."
    assert data["resolution_transaction_hash"] == "0x" + "e" * 64

    # DB state verified
    db_session.expire_all()
    re_dispute = db_session.execute(select(Dispute).where(Dispute.id == dispute.id)).scalar_one()
    assert re_dispute.status == DisputeStatus.REJECTED
    re_version = db_session.execute(select(ProjectVersion).where(ProjectVersion.id == version.id)).scalar_one()
    assert re_version.dispute_status == DisputeStatus.REJECTED
    re_project = db_session.execute(select(Project).where(Project.id == project.id)).scalar_one()
    assert re_project.status == ProjectStatus.ACTIVE  # Project cleared after dispute rejection!


def test_18_unauthorized_dispute_resolution(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 18: Student or Faculty attempting to adjudicate dispute receives 403 FORBIDDEN."""
    _, student_token = create_test_user(email_prefix="student", role=UserRole.STUDENT)
    project = anchored_project["project"]
    claimant, _ = create_test_user(email_prefix="claimant")

    dispute = Dispute(
        public_id="DSP-202609-NOAUTH",
        project_id=project.id,
        claimant_user_id=claimant.id,
        dispute_type=DisputeType.PLAGIARISM,
        claim_description="Dispute for unauthorized adjudication test.",
        status=DisputeStatus.OPEN,
    )
    db_session.add(dispute)
    db_session.commit()

    resp = client.patch(
        f"/api/v1/admin/disputes/{dispute.public_id}/adjudicate",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "resolution_status": "REJECTED",
            "resolution_notes": "Student trying to act as admin.",
        },
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_19_resolve_already_resolved_dispute(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 19: Attempting to re-adjudicate an already RESOLVED or REJECTED dispute returns 409 CONFLICT."""
    _, admin_token = create_test_user(role=UserRole.ADMIN)
    project = anchored_project["project"]
    claimant, _ = create_test_user(email_prefix="claimant")

    dispute = Dispute(
        public_id="DSP-202609-ALREADY",
        project_id=project.id,
        claimant_user_id=claimant.id,
        dispute_type=DisputeType.PLAGIARISM,
        claim_description="Dispute already closed.",
        status=DisputeStatus.RESOLVED,
        resolution_notes="Previously resolved.",
    )
    db_session.add(dispute)
    db_session.commit()

    resp = client.patch(
        f"/api/v1/admin/disputes/{dispute.public_id}/adjudicate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "resolution_status": "REJECTED",
            "resolution_notes": "Trying to overturn resolved dispute.",
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "DISPUTE_ALREADY_RESOLVED"


def test_20_resolve_nonexistent_dispute(client: TestClient, create_test_user):
    """Scenario 20: Adjudicating nonexistent dispute ID returns 404 NOT_FOUND."""
    _, admin_token = create_test_user(role=UserRole.ADMIN)
    resp = client.patch(
        "/api/v1/admin/disputes/DSP-202609-99999/adjudicate",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "resolution_status": "REJECTED",
            "resolution_notes": "Adjudicating ghost dispute.",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "DISPUTE_NOT_FOUND"


def test_21_blockchain_resolution_failure_handling(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 21: Blockchain revert during resolveDispute returns 502 and does not update dispute status."""
    _, admin_token = create_test_user(role=UserRole.ADMIN)
    project = anchored_project["project"]
    claimant, _ = create_test_user(email_prefix="claimant")

    dispute = Dispute(
        public_id="DSP-202609-FAIL",
        project_id=project.id,
        claimant_user_id=claimant.id,
        dispute_type=DisputeType.PLAGIARISM,
        claim_description="Dispute for blockchain revert test.",
        status=DisputeStatus.OPEN,
    )
    db_session.add(dispute)
    anchored_project["version"].dispute_status = DisputeStatus.OPEN
    db_session.commit()

    mock_bc = MagicMock()
    mock_bc.resolve_dispute = AsyncMock(side_effect=BlockchainException(
        code="BLOCKCHAIN_TRANSACTION_FAILED",
        message="resolveDispute reverted on-chain.",
        status_code=502,
    ))

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.patch(
            f"/api/v1/admin/disputes/{dispute.public_id}/adjudicate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "resolution_status": "RESOLVED",
                "resolution_notes": "Admin notes.",
            },
        )
    assert resp.status_code == 502

    # Verify DB status is NOT updated to RESOLVED
    db_session.expire_all()
    re_dispute = db_session.execute(select(Dispute).where(Dispute.id == dispute.id)).scalar_one()
    assert re_dispute.status == DisputeStatus.OPEN


def test_22_public_verification_with_active_dispute(client: TestClient, db_session: Session, anchored_project):
    """Scenario 22: Public verification endpoint reflects active dispute (is_valid=False, dispute_status=OPEN)."""
    reg_id = anchored_project["registration_id"]
    version = anchored_project["version"]
    version.dispute_status = DisputeStatus.OPEN
    db_session.commit()

    mock_provider = MagicMock()
    mock_provider.get_project_version = AsyncMock(return_value={
        "exists": True,
        "registration_id": reg_id,
        "composite_hash": version.composite_sha256,
        "ipfs_cid": version.ipfs_root_cid,
        "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "co_authors": [],
        "version_index": 1,
        "lifecycle_stage": "FINAL",
        "block_number": 100,
        "anchored_timestamp": datetime.now(timezone.utc),
        "dispute_state": "OPEN",
    })
    mock_provider.verify_project_version = AsyncMock(return_value=None)

    with patch("app.services.verification_service.get_blockchain_provider", return_value=mock_provider):
        resp = client.get(f"/api/v1/verification/verify-registration/{reg_id}")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_valid"] is False
    assert data["blockchain_proof"]["dispute_status"] == "OPEN"
    assert data["blockchain_proof"]["match_confirmed"] is True  # Hash still matches, but dispute is active!
    assert "dispute" in data["message"].lower()


def test_23_public_verification_after_dispute_rejected(client: TestClient, db_session: Session, anchored_project):
    """Scenario 23: Public verification returns is_valid=True and dispute_status=REJECTED after dispute dismissed."""
    reg_id = anchored_project["registration_id"]
    version = anchored_project["version"]
    version.dispute_status = DisputeStatus.REJECTED
    db_session.commit()

    mock_provider = MagicMock()
    mock_provider.get_project_version = AsyncMock(return_value={
        "exists": True,
        "registration_id": reg_id,
        "composite_hash": version.composite_sha256,
        "ipfs_cid": version.ipfs_root_cid,
        "author": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "co_authors": [],
        "version_index": 1,
        "lifecycle_stage": "FINAL",
        "block_number": 100,
        "anchored_timestamp": datetime.now(timezone.utc),
        "dispute_state": "REJECTED",
    })
    mock_provider.verify_project_version = AsyncMock(return_value=None)

    with patch("app.services.verification_service.get_blockchain_provider", return_value=mock_provider):
        resp = client.get(f"/api/v1/verification/verify-registration/{reg_id}")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_valid"] is True
    assert data["blockchain_proof"]["dispute_status"] == "REJECTED"
    assert data["blockchain_proof"]["match_confirmed"] is True


def test_24_original_ownership_proof_immutability(client: TestClient, db_session: Session, create_test_user, anchored_project):
    """Scenario 24: Resolving dispute NEVER mutates original composite hash, IPFS CID, author, or block timestamp."""
    _, admin_token = create_test_user(role=UserRole.ADMIN)
    reg_id = anchored_project["registration_id"]
    version = anchored_project["version"]
    record = anchored_project["record"]
    claimant, _ = create_test_user(email_prefix="claimant")

    # Snapshot baseline values
    orig_hash = version.composite_sha256
    orig_cid = version.ipfs_root_cid
    orig_index = version.version_index
    orig_reg_id = version.registration_id
    orig_tx = record.transaction_hash
    orig_author = record.author_wallet

    dispute = Dispute(
        public_id="DSP-202609-IMMUT",
        project_id=anchored_project["project"].id,
        claimant_user_id=claimant.id,
        dispute_type=DisputeType.PLAGIARISM,
        claim_description="Dispute for immutability invariant test.",
        status=DisputeStatus.OPEN,
    )
    db_session.add(dispute)
    version.dispute_status = DisputeStatus.OPEN
    db_session.commit()

    mock_bc = MagicMock()
    mock_bc.resolve_dispute = AsyncMock(return_value={
        "transaction_hash": "0x" + "9" * 64,
        "block_number": 120,
        "event_data": {"registrationId": reg_id, "status": 3},
    })

    with patch("app.services.dispute_service.get_blockchain_service", return_value=mock_bc):
        resp = client.patch(
            f"/api/v1/admin/disputes/{dispute.public_id}/adjudicate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "resolution_status": "RESOLVED",
                "resolution_notes": "Plagiarism claim upheld after evaluation.",
            },
        )
    assert resp.status_code == 200

    # Verify baseline immutable parameters are identical
    db_session.expire_all()
    post_version = db_session.execute(select(ProjectVersion).where(ProjectVersion.id == version.id)).scalar_one()
    post_record = db_session.execute(select(BlockchainRecord).where(BlockchainRecord.id == record.id)).scalar_one()

    assert post_version.composite_sha256 == orig_hash
    assert post_version.ipfs_root_cid == orig_cid
    assert post_version.version_index == orig_index
    assert post_version.registration_id == orig_reg_id
    assert post_record.transaction_hash == orig_tx
    assert post_record.author_wallet == orig_author
