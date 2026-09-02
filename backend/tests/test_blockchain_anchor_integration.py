import hashlib
import io
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BlockchainException, IPFSException, ValidationException
from app.core.security import create_access_token, hash_password
from app.models.artifact import Artifact
from app.models.blockchain_record import BlockchainRecord
from app.models.enums import (
    AnchoringStatus,
    ArtifactCategory,
    DisputeStatus,
    ProjectMemberRole,
    ProjectVersionStage,
    UserRole,
)
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.services.blockchain_service import (
    BlockchainService,
    get_blockchain_service,
    set_blockchain_service,
)
from app.storage.ipfs_adapter import (
    IPFSStorageAdapter,
    get_ipfs_adapter,
    set_ipfs_adapter,
)
from app.storage.service import get_storage_service
from app.utils.hashing import compute_composite_sha256
from app.utils.identifiers import generate_blockchain_public_id

SAMPLE_RELAYER_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
SAMPLE_RELAYER_ADDR = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
SAMPLE_CONTRACT_ADDR = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
SAMPLE_OWNER_WALLET = "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
SAMPLE_CONTRIB_WALLET = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def test_user_with_wallet(db_session: Session):
    """Creates a student user with a configured Web3 wallet address."""
    def _create(email_prefix: str, wallet: str = SAMPLE_OWNER_WALLET) -> Tuple[User, str]:
        unique_id = uuid.uuid4().hex[:6]
        user = User(
            public_id=f"USR-202609-{unique_id[:5].upper()}",
            email=f"{email_prefix}_{unique_id}@sih2026.edu",
            hashed_password=hash_password("SecurePass123!"),
            full_name=f"Student {email_prefix.capitalize()}",
            institution_id=f"INST-{unique_id.upper()}",
            department="Cybersecurity",
            role=UserRole.STUDENT,
            wallet_address=wallet,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(
            subject=user.public_id,
            role=user.role.value,
            email=user.email,
        )
        return user, token
    return _create


@pytest.fixture
def mock_ipfs_adapter():
    """Provides a mocked IPFSStorageAdapter that simulates directory DAG pinning."""
    adapter = IPFSStorageAdapter(api_url="http://127.0.0.1:5001")
    root_cid = "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"

    async def mock_add_directory(files: Dict[str, bytes], pin: bool = True) -> Dict[str, str]:
        mapping = {"root": root_cid, "": root_cid}
        for name in files:
            mapping[name] = f"bafybei{hashlib.sha256(name.encode()).hexdigest()[:48]}"
        return mapping

    adapter.add_directory = AsyncMock(side_effect=mock_add_directory)
    adapter.cat = AsyncMock(return_value=b"mocked ipfs content")
    adapter.is_pinned = AsyncMock(return_value=True)

    set_ipfs_adapter(adapter)
    yield adapter
    set_ipfs_adapter(None)


@pytest.fixture
def mock_blockchain_service():
    """Provides a configured BlockchainService with mocked Web3 calls."""
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True
    mock_w3.eth.chain_id = 31337
    mock_w3.eth.block_number = 250
    mock_w3.eth.gas_price = 1000000000
    mock_w3.eth.get_block.return_value = {
        "timestamp": 1788330000,
        "baseFeePerGas": None,
    }
    mock_w3.eth.get_transaction_count.return_value = 1
    mock_w3.to_wei.side_effect = lambda val, unit: val * 10**9 if unit == "gwei" else val

    service = BlockchainService(
        rpc_url="http://127.0.0.1:8545",
        contract_address=SAMPLE_CONTRACT_ADDR,
        chain_id=31337,
        relayer_private_key=SAMPLE_RELAYER_KEY,
        confirmation_blocks=1,
        timeout_seconds=5,
        web3_instance=mock_w3,
    )

    # Mock register_project_version return
    async def mock_register(
        registration_id, composite_hash, ipfs_root_cid, version_index, lifecycle_stage, author=None, co_authors=None
    ):
        return {
            "transaction_hash": "0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb",
            "block_number": 251,
            "gas_used": 185000,
            "anchored_timestamp": datetime.fromtimestamp(1788330000, tz=timezone.utc),
            "record_id": 42,
            "event_data": {"recordId": 42, "registrationId": registration_id},
        }

    service.register_project_version = AsyncMock(side_effect=mock_register)
    set_blockchain_service(service)
    yield service
    set_blockchain_service(None)


# ==============================================================================
# 1. DETERMINISTIC COMPOSITE SHA-256 SPECIFICATION TESTS
# ==============================================================================

def test_composite_sha256_matches_frozen_specification_example():
    """
    Validates that compute_composite_sha256 produces the EXACT 32-byte digest
    specified in docs/blockchain/BLOCKCHAIN_DESIGN.md Section 2.2.
    """
    artifacts = [
        {
            "file_name": "report.pdf",
            "file_size_bytes": 1048576,
            "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        },
        {
            "file_name": "code.zip",
            "file_size_bytes": 5242880,
            "sha256_hash": "ca978112ca1bbdcafac231b39a23dc4da786081cd1e14eed6eaa5d1123c7a718",
        },
        {
            "file_name": "design.png",
            "file_size_bytes": 2097152,
            "sha256_hash": "8b1a9953c4611296a827abf8c47804d7ecd8cbe8b8f8a0fecd955f10fc94aea9",
        },
    ]

    # Mathematical SHA-256 of:
    # "code.zip:5242880:ca978112ca1bbdcafac231b39a23dc4da786081cd1e14eed6eaa5d1123c7a718\n"
    # "design.png:2097152:8b1a9953c4611296a827abf8c47804d7ecd8cbe8b8f8a0fecd955f10fc94aea9\n"
    # "report.pdf:1048576:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    expected_digest = "d0010ac9dae55598ad0584d89f70a4913dbdd41e2b8e40cd9f7aa4eb45b2729d"
    result = compute_composite_sha256(artifacts)
    assert result == expected_digest



def test_composite_sha256_order_independence():
    """
    Ensures input ordering does not affect the deterministic output.
    Artifacts passed in reverse or random order must produce the identical digest.
    """
    a1 = {"file_name": "alpha.py", "file_size_bytes": 100, "sha256_hash": "a" * 64}
    a2 = {"file_name": "beta.py", "file_size_bytes": 200, "sha256_hash": "b" * 64}
    a3 = {"file_name": "gamma.py", "file_size_bytes": 300, "sha256_hash": "c" * 64}

    digest_forward = compute_composite_sha256([a1, a2, a3])
    digest_reversed = compute_composite_sha256([a3, a2, a1])
    digest_shuffled = compute_composite_sha256([a2, a1, a3])

    assert digest_forward == digest_reversed == digest_shuffled


def test_composite_sha256_empty_list_rejected():
    """Empty artifact list raises ValidationException per BLOCKCHAIN_DESIGN.md Section 2.1."""
    with pytest.raises(ValidationException) as exc:
        compute_composite_sha256([])
    assert exc.value.code == "EMPTY_ARTIFACTS_NOT_ALLOWED"


def test_generate_blockchain_public_id_format():
    """Validates public identifier format BLK-YYYYMM-XXXXX."""
    blk_id = generate_blockchain_public_id()
    assert blk_id.startswith("BLK-")
    assert re.match(r"^BLK-\d{6}-[0-9A-F]{5}$", blk_id)


# ==============================================================================
# 2. END-TO-END ANCHORING WORKFLOW (HAPPY PATH)
# ==============================================================================

def test_e2e_project_version_anchoring_happy_path(
    client: TestClient,
    db_session: Session,
    test_user_with_wallet,
    mock_ipfs_adapter,
    mock_blockchain_service,
):
    """
    Tests the complete target workflow:
    1. Upload artifacts to project
    2. Create milestone version snapshot with artifact IDs
    3. Verify deterministic composite SHA-256 calculated
    4. Verify IPFS directory DAG pinned with root CID
    5. Verify individual artifact CIDs populated in PostgreSQL
    6. Verify registerProjectVersion called on blockchain with relayer
    7. Verify PostgreSQL BlockchainRecord created with tx hash, block, timestamp
    8. Verify ProjectVersion marked as ANCHORED
    9. Verify response envelope contains complete proof
    """
    owner, owner_token = test_user_with_wallet("lead_student", SAMPLE_OWNER_WALLET)

    # 1. Create Project
    proj_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Quantum Safe Identity Registry",
            "abstract": "Decentralized PKI on Ethereum and IPFS.",
            "category": "CYBERSECURITY",
            "department": "Computer Science",
            "academic_year": "2025-2026",
            "visibility": "PUBLIC",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["data"]["public_id"]

    # 2. Upload 2 Artifacts
    art1_content = b"Architecture specification PDF content bytes"
    art1_res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("architecture.pdf", io.BytesIO(art1_content), "application/pdf")},
        data={"artifact_category": "DESIGN_SPEC", "project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert art1_res.status_code == 201
    art1_data = art1_res.json()["data"]
    art1_id = art1_data["public_id"]

    art2_content = b"Source code repository ZIP content bytes"
    art2_res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("source_code.zip", io.BytesIO(art2_content), "application/zip")},
        data={"artifact_category": "SOURCE_CODE", "project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert art2_res.status_code == 201
    art2_data = art2_res.json()["data"]
    art2_id = art2_data["public_id"]

    # 3. Create Version Milestone referencing uploaded artifacts
    version_res = client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "DESIGN",
            "title": "Initial Architecture & Proof of Concept",
            "description": "First anchored milestone snapshot.",
            "artifact_ids": [art1_id, art2_id],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert version_res.status_code == 201
    body = version_res.json()
    assert body["success"] is True
    data = body["data"]

    # 4. Verify Version State
    assert data["anchoring_status"] == "ANCHORED"
    assert data["dispute_status"] == "NONE"
    assert data["composite_sha256"] is not None
    assert len(data["composite_sha256"]) == 64
    assert data["ipfs_root_cid"] == "bafybeic527ywh2k37pzn26oxbpxiynvxvxzvdvdg24k722jgyk33n65d3m"

    # Verify BlockchainProof in API response
    proof = data["blockchain_record"]
    assert proof is not None
    assert proof["transaction_hash"] == "0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb"
    assert proof["block_number"] == 251
    assert proof["network_name"] == "hardhat"
    assert proof["anchored_timestamp"] is not None

    # 5. Verify IPFS directory DAG was created with both files
    assert mock_ipfs_adapter.add_directory.called
    pinned_files = mock_ipfs_adapter.add_directory.call_args[1]["files"]
    assert "architecture.pdf" in pinned_files
    assert "source_code.zip" in pinned_files
    assert pinned_files["architecture.pdf"] == art1_content
    assert pinned_files["source_code.zip"] == art2_content

    # 6. Verify Blockchain Service was called with expected arguments
    assert mock_blockchain_service.register_project_version.called
    call_kwargs = mock_blockchain_service.register_project_version.call_args[1]
    assert call_kwargs["registration_id"] == data["registration_id"]
    assert call_kwargs["composite_hash"] == data["composite_sha256"]
    assert call_kwargs["ipfs_root_cid"] == data["ipfs_root_cid"]
    assert call_kwargs["version_index"] == 1
    assert call_kwargs["lifecycle_stage"] == ProjectVersionStage.DESIGN
    assert call_kwargs["author"] == SAMPLE_OWNER_WALLET

    # 7. Verify Database BlockchainRecord
    db_version = db_session.execute(
        select(ProjectVersion).where(ProjectVersion.public_id == data["public_id"])
    ).scalar_one()

    assert db_version.anchoring_status == AnchoringStatus.ANCHORED
    record = db_session.execute(
        select(BlockchainRecord).where(BlockchainRecord.version_id == db_version.id)
    ).scalar_one()

    assert record.public_id.startswith("BLK-")
    assert record.transaction_hash == "0x61c6092de432fa646d61f4086ef016512aa2dbdeda9a063e5c9dd7c484f944cb"
    assert record.block_number == 251
    assert record.onchain_record_id == 42
    assert record.smart_contract_address == SAMPLE_CONTRACT_ADDR
    assert record.author_wallet == SAMPLE_OWNER_WALLET
    assert record.submitter_wallet == SAMPLE_RELAYER_ADDR
    assert record.ipfs_cid_anchored == db_version.ipfs_root_cid

    # 8. Verify individual artifacts in DB updated with IPFS CIDs
    for art_pid in [art1_id, art2_id]:
        art_db = db_session.execute(
            select(Artifact).where(Artifact.public_id == art_pid)
        ).scalar_one()
        assert art_db.version_id == db_version.id
        assert art_db.ipfs_cid is not None
        assert art_db.ipfs_cid.startswith("bafybei")


# ==============================================================================
# 3. MULTI-AUTHOR / CO-AUTHOR WALLET ATTRIBUTION TESTS
# ==============================================================================

def test_team_member_coauthors_passed_to_blockchain(
    client: TestClient,
    test_user_with_wallet,
    mock_ipfs_adapter,
    mock_blockchain_service,
):
    """
    Validates that team members with wallet addresses are passed as coAuthors
    calldata array to ProjectRegistry.sol.
    """
    owner, owner_token = test_user_with_wallet("lead_author", SAMPLE_OWNER_WALLET)
    teammate, _ = test_user_with_wallet("teammate", SAMPLE_CONTRIB_WALLET)

    # Create project
    p_res = client.post(
        "/api/v1/projects",
        json={
            "title": "Team Coauthored Project",
            "abstract": "Team attribution verification test.",
            "category": "AI",
            "department": "Computer Science",
            "academic_year": "2025-2026",
            "visibility": "PUBLIC",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    project_id = p_res.json()["data"]["public_id"]

    # Add teammate to project
    client.post(
        f"/api/v1/projects/{project_id}/members",
        json={
            "user_public_id": teammate.public_id,
            "role_in_project": "CONTRIBUTOR",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # Upload artifact
    art_res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("team_spec.pdf", io.BytesIO(b"Team spec bytes"), "application/pdf")},
        data={"artifact_category": "DOCUMENTATION", "project_id": project_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    art_id = art_res.json()["data"]["public_id"]

    # Create version
    client.post(
        f"/api/v1/projects/{project_id}/versions",
        json={
            "version_tag": "v1.0",
            "lifecycle_stage": "IDEA",
            "title": "Team Idea Milestone",
            "artifact_ids": [art_id],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    call_kwargs = mock_blockchain_service.register_project_version.call_args[1]
    assert call_kwargs["author"] == SAMPLE_OWNER_WALLET
    assert SAMPLE_CONTRIB_WALLET in call_kwargs["co_authors"]


# ==============================================================================
# 4. TRUSTLESS VERIFICATION ROUNDTRIP TESTS
# ==============================================================================

def test_trustless_verification_of_newly_anchored_version(
    client: TestClient,
    test_user_with_wallet,
    mock_ipfs_adapter,
    mock_blockchain_service,
):
    """
    Verifies that a newly anchored version can be verified through all 3 public verification endpoints:
    1. verify-registration/{registration_id}
    2. verify-hash (using composite_sha256)
    3. verify-file (using uploaded raw artifact)
    """
    owner, owner_token = test_user_with_wallet("verify_lead", SAMPLE_OWNER_WALLET)

    # Create project & artifact
    proj_id = client.post(
        "/api/v1/projects",
        json={"title": "Verification Target", "abstract": "Test", "category": "WEB3", "department": "CS", "academic_year": "2025-2026"},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["data"]["public_id"]

    raw_file_bytes = b"Crucial scientific breakthrough paper contents 2026"
    art_res = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("paper.pdf", io.BytesIO(raw_file_bytes), "application/pdf")},
        data={"artifact_category": "DOCUMENTATION", "project_id": proj_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    art_id = art_res.json()["data"]["public_id"]

    # Anchor version
    ver_res = client.post(
        f"/api/v1/projects/{proj_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "DESIGN", "title": "Anchored Paper", "artifact_ids": [art_id]},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert ver_res.status_code == 201
    ver_data = ver_res.json()["data"]
    reg_id = ver_data["registration_id"]
    comp_hash = ver_data["composite_sha256"]

    # Mock verify_project_version view call on smart contract
    mock_blockchain_service.verify_project_version = MagicMock(return_value={
        "is_valid": True,
        "anchored_timestamp": datetime.now(timezone.utc),
        "ipfs_root_cid": ver_data["ipfs_root_cid"],
        "author_wallet": SAMPLE_OWNER_WALLET,
        "dispute_status": "NONE",
        "match_confirmed": True,
        "registration_id": reg_id,
        "smart_contract_address": SAMPLE_CONTRACT_ADDR,
    })

    # Test 1: Verify by Registration ID
    v1_res = client.get(f"/api/v1/verification/verify-registration/{reg_id}")
    assert v1_res.status_code == 200
    v1_data = v1_res.json()["data"]
    assert v1_data["is_valid"] is True
    assert v1_data["registration_id"] == reg_id
    assert v1_data["blockchain_proof"]["author_wallet"] == SAMPLE_OWNER_WALLET
    assert v1_data["blockchain_proof"]["match_confirmed"] is True

    # Test 2: Verify by Composite Hash
    v2_res = client.post("/api/v1/verification/verify-hash", json={"sha256_hash": comp_hash})
    assert v2_res.status_code == 200
    v2_data = v2_res.json()["data"]
    assert v2_data["is_valid"] is True
    assert v2_data["matched_hash"] == comp_hash
    assert v2_data["registration_id"] == reg_id

    # Test 3: Verify by Raw Uploaded File
    v3_res = client.post(
        "/api/v1/verification/verify-file",
        files={"file": ("paper.pdf", io.BytesIO(raw_file_bytes), "application/pdf")},
    )
    assert v3_res.status_code == 200
    v3_data = v3_res.json()["data"]
    assert v3_data["is_valid"] is True
    assert v3_data["verification_method"] == "FILE"
    assert v3_data["matched_file_name"] == "paper.pdf"


# ==============================================================================
# 5. IDEMPOTENCY WITH ANCHORED VERSIONS
# ==============================================================================

def test_idempotent_anchoring_submission_does_not_spend_duplicate_gas(
    client: TestClient,
    test_user_with_wallet,
    mock_ipfs_adapter,
    mock_blockchain_service,
):
    """
    Verifies that replaying a submission with the same Idempotency-Key returns
    the existing ANCHORED record with HTTP 200 without sending a second transaction.
    """
    owner, owner_token = test_user_with_wallet("idemp_lead")
    proj_id = client.post(
        "/api/v1/projects",
        json={"title": "Idempotent Project", "abstract": "Deduplication test", "category": "AI", "department": "CS", "academic_year": "2025-2026"},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["data"]["public_id"]

    art_id = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("model.json", io.BytesIO(b'{"weights": [1, 2, 3]}'), "application/json")},
        data={"artifact_category": "SOURCE_CODE", "project_id": proj_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["data"]["public_id"]

    idempotency_key = str(uuid.uuid4())

    # First submission -> 201 Created
    res1 = client.post(
        f"/api/v1/projects/{proj_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "PROTOTYPE", "title": "Idemp Test", "artifact_ids": [art_id]},
        headers={"Authorization": f"Bearer {owner_token}", "Idempotency-Key": idempotency_key},
    )
    assert res1.status_code == 201
    assert mock_blockchain_service.register_project_version.call_count == 1

    # Second submission with same Idempotency-Key -> 200 OK
    res2 = client.post(
        f"/api/v1/projects/{proj_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "PROTOTYPE", "title": "Idemp Test", "artifact_ids": [art_id]},
        headers={"Authorization": f"Bearer {owner_token}", "Idempotency-Key": idempotency_key},
    )
    assert res2.status_code == 200
    assert res2.json()["data"]["public_id"] == res1.json()["data"]["public_id"]
    assert res2.json()["data"]["anchoring_status"] == "ANCHORED"
    # Blockchain service must NOT be called again
    assert mock_blockchain_service.register_project_version.call_count == 1


# ==============================================================================
# 6. FAILURE SCENARIO RESILIENCE (INTEGRATION_CONTRACT.md SECTION 4)
# ==============================================================================

def test_blockchain_revert_marks_version_as_failed_and_preserves_hash(
    client: TestClient,
    db_session: Session,
    test_user_with_wallet,
    mock_ipfs_adapter,
    mock_blockchain_service,
):
    """
    Scenario B (INTEGRATION_CONTRACT.md):
    When blockchain transaction reverts, ProjectVersion status is transitioned to FAILED,
    and composite_sha256 and ipfs_root_cid are preserved for retry.
    """
    owner, owner_token = test_user_with_wallet("fail_lead")
    proj_id = client.post(
        "/api/v1/projects",
        json={"title": "Revert Handling Project", "abstract": "Failure scenario", "category": "AI", "department": "CS", "academic_year": "2025-2026"},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["data"]["public_id"]

    art_id = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("code.py", io.BytesIO(b"print('hello')"), "text/plain")},
        data={"artifact_category": "SOURCE_CODE", "project_id": proj_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["data"]["public_id"]

    # Force blockchain service to fail
    mock_blockchain_service.register_project_version = AsyncMock(
        side_effect=BlockchainException(
            code="BLOCKCHAIN_TRANSACTION_FAILED",
            message="Smart contract execution reverted: custom error",
            status_code=502,
        )
    )

    res = client.post(
        f"/api/v1/projects/{proj_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "Reverted Version", "artifact_ids": [art_id]},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 502
    assert res.json()["error"]["code"] == "BLOCKCHAIN_TRANSACTION_FAILED"

    # Verify database state
    ver_in_db = db_session.execute(
        select(ProjectVersion).where(ProjectVersion.version_tag == "v1.0")
    ).scalar_one()

    assert ver_in_db.anchoring_status == AnchoringStatus.FAILED
    assert ver_in_db.composite_sha256 is not None
    assert ver_in_db.ipfs_root_cid is not None
    assert ver_in_db.blockchain_record is None


def test_ipfs_failure_prevents_orphan_db_record(
    client: TestClient,
    db_session: Session,
    test_user_with_wallet,
    mock_ipfs_adapter,
    mock_blockchain_service,
):
    """
    Scenario A (INTEGRATION_CONTRACT.md):
    When IPFS pinning fails before DB commit, request fails with 502 and
    no orphaned ProjectVersion record is persisted in the database.
    """
    owner, owner_token = test_user_with_wallet("ipfs_fail_lead")
    proj_id = client.post(
        "/api/v1/projects",
        json={"title": "IPFS Failure Project", "abstract": "Failure scenario", "category": "AI", "department": "CS", "academic_year": "2025-2026"},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["data"]["public_id"]

    art_id = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("dataset.csv", io.BytesIO(b"col1,col2\n1,2"), "text/csv")},
        data={"artifact_category": "OTHER", "project_id": proj_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()["data"]["public_id"]

    # Force IPFS adapter to fail
    mock_ipfs_adapter.add_directory = AsyncMock(
        side_effect=IPFSException(
            code="IPFS_CONNECTION_ERROR",
            message="Cannot connect to IPFS node daemon.",
            status_code=502,
        )
    )

    res = client.post(
        f"/api/v1/projects/{proj_id}/versions",
        json={"version_tag": "v1.0", "lifecycle_stage": "IDEA", "title": "IPFS Failed Version", "artifact_ids": [art_id]},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert res.status_code == 502
    assert res.json()["error"]["code"] == "IPFS_CONNECTION_ERROR"

    # Verify no orphaned ProjectVersion exists in database
    existing_vers = db_session.execute(
        select(ProjectVersion).where(ProjectVersion.version_tag == "v1.0")
    ).scalars().all()
    assert len(existing_vers) == 0
