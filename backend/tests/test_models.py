import uuid
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    User,
    Project,
    ProjectMember,
    ProjectVersion,
    Artifact,
    BlockchainRecord,
    Dispute,
    Notification,
    UserRole,
    ProjectVisibility,
    ProjectStatus,
    ProjectMemberRole,
    ProjectVersionStage,
    ProjectVersionStatus,
    AnchoringStatus,
    DisputeStatus,
    DisputeType,
    ArtifactCategory,
    NotificationType,
)


def test_user_creation(db_session: Session):
    """Test 1: User model creation with default values, UUID, and enums."""
    user = User(
        public_id=f"USR-202609-{uuid.uuid4().hex[:5].upper()}",
        email=f"student_{uuid.uuid4().hex[:6]}@sih2026.edu",
        hashed_password="argon2id$mock_hash_for_test",
        full_name="Alice Student",
        institution_id="INST-IIT-001",
        department="Computer Science",
        role=UserRole.STUDENT,
        wallet_address="0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
    )
    db_session.add(user)
    db_session.flush()

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.is_active is True
    assert user.is_verified is False
    assert user.role == UserRole.STUDENT
    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.created_at.tzinfo is not None


def test_project_creation(db_session: Session):
    """Test 2: Project model creation with slug, metadata, and default status."""
    project = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"ai-medical-diagnostics-{uuid.uuid4().hex[:6]}",
        title="AI Medical Diagnostics System",
        abstract="A decentralized machine learning platform for medical diagnostics.",
        category="ARTIFICIAL_INTELLIGENCE",
        department="Computer Science",
        academic_year="2025-2026",
        current_lifecycle_stage=ProjectVersionStage.IDEA,
        visibility=ProjectVisibility.PUBLIC,
        status=ProjectStatus.ACTIVE,
    )
    db_session.add(project)
    db_session.flush()

    assert project.id is not None
    assert isinstance(project.id, uuid.UUID)
    assert project.status == ProjectStatus.ACTIVE
    assert project.visibility == ProjectVisibility.PUBLIC
    assert project.current_lifecycle_stage == ProjectVersionStage.IDEA


def test_project_member_relationship(db_session: Session):
    """Test 3: ProjectMember relationship connecting User and Project."""
    user = User(
        public_id=f"USR-202609-{uuid.uuid4().hex[:5].upper()}",
        email=f"lead_{uuid.uuid4().hex[:6]}@sih2026.edu",
        hashed_password="mock_hash_password",
        full_name="Bob Lead",
        role=UserRole.STUDENT,
    )
    project = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"decentralized-registry-{uuid.uuid4().hex[:6]}",
        title="Decentralized Registry",
        category="CYBERSECURITY",
        department="Information Technology",
        academic_year="2025-2026",
    )
    db_session.add_all([user, project])
    db_session.flush()

    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role_in_project=ProjectMemberRole.LEAD,
        contribution_percentage=Decimal("60.00"),
        is_owner=True,
    )
    db_session.add(member)
    db_session.flush()

    assert member.id is not None
    assert member.is_owner is True
    assert member.role_in_project == ProjectMemberRole.LEAD
    assert len(project.members) == 1
    assert project.members[0].user.full_name == "Bob Lead"
    assert len(user.project_memberships) == 1
    assert user.project_memberships[0].project.title == "Decentralized Registry"


def test_project_version_relationship(db_session: Session):
    """Test 4: ProjectVersion relationship and sequential versioning under Project."""
    project = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"blockchain-voting-{uuid.uuid4().hex[:6]}",
        title="Blockchain Voting System",
        category="WEB3",
        department="Computer Science",
        academic_year="2025-2026",
    )
    db_session.add(project)
    db_session.flush()

    v1 = ProjectVersion(
        public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project.id,
        registration_id=f"REG-2026-{uuid.uuid4().hex[:6].upper()}",
        idempotency_key=str(uuid.uuid4()),
        version_index=1,
        version_tag="v1.0",
        lifecycle_stage=ProjectVersionStage.IDEA,
        title="Initial Architecture Milestone",
        description="Core design and whitepaper",
        anchoring_status=AnchoringStatus.PENDING,
        dispute_status=DisputeStatus.NONE,
    )
    v2 = ProjectVersion(
        public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project.id,
        registration_id=f"REG-2026-{uuid.uuid4().hex[:6].upper()}",
        idempotency_key=str(uuid.uuid4()),
        version_index=2,
        version_tag="v2.0",
        lifecycle_stage=ProjectVersionStage.PROTOTYPE,
        title="Prototype Milestone",
        description="Smart contract implementation",
        anchoring_status=AnchoringStatus.ANCHORED,
        dispute_status=DisputeStatus.NONE,
    )
    db_session.add_all([v1, v2])
    db_session.flush()

    assert len(project.versions) == 2
    assert project.versions[0].version_index == 1
    assert project.versions[1].version_index == 2
    assert project.versions[0].project.slug == project.slug


def test_artifact_relationship(db_session: Session):
    """Test 5: Artifact relationship linked to a ProjectVersion."""
    project = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"iot-agriculture-{uuid.uuid4().hex[:6]}",
        title="Smart Agriculture IoT",
        category="IOT",
        department="Electronics",
        academic_year="2025-2026",
    )
    db_session.add(project)
    db_session.flush()

    version = ProjectVersion(
        public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project.id,
        version_index=1,
        version_tag="v1.0",
        lifecycle_stage=ProjectVersionStage.DESIGN,
        title="Hardware Design",
        anchoring_status=AnchoringStatus.DRAFT,
    )
    db_session.add(version)
    db_session.flush()

    artifact1 = Artifact(
        public_id=f"ART-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=version.id,
        file_name="circuit_schematic.pdf",
        file_type="application/pdf",
        file_size_bytes=1048576,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ipfs_cid="bafybeicysg23kiwv34eg2dqwvsndjodcg7d4e62bevdqiufapx6q6bgfqy",
        artifact_category=ArtifactCategory.DESIGN_SPEC,
    )
    artifact2 = Artifact(
        public_id=f"ART-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=version.id,
        file_name="firmware.ino",
        file_type="text/plain",
        file_size_bytes=45230,
        sha256_hash="ca978112ca1bbdcafac231b39a23dc4da786081cd1e14eed6eaa5d1123c7a718",
        ipfs_cid="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        artifact_category=ArtifactCategory.SOURCE_CODE,
    )
    db_session.add_all([artifact1, artifact2])
    db_session.flush()

    assert len(version.artifacts) == 2
    assert version.artifacts[0].file_name == "circuit_schematic.pdf"
    assert version.artifacts[1].artifact_category == ArtifactCategory.SOURCE_CODE
    assert version.artifacts[0].version.title == "Hardware Design"


def test_blockchain_record_one_to_one(db_session: Session):
    """Test 6: BlockchainRecord 1-to-1 relationship with ProjectVersion."""
    project = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"quantum-crypto-{uuid.uuid4().hex[:6]}",
        title="Post-Quantum Cryptography",
        category="CYBERSECURITY",
        department="Mathematics",
        academic_year="2025-2026",
    )
    db_session.add(project)
    db_session.flush()

    version = ProjectVersion(
        public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project.id,
        registration_id="REG-2026-QNTM01",
        version_index=1,
        version_tag="v1.0",
        lifecycle_stage=ProjectVersionStage.FINAL,
        title="Final Quantum Proof",
        anchoring_status=AnchoringStatus.ANCHORED,
    )
    db_session.add(version)
    db_session.flush()

    record = BlockchainRecord(
        public_id=f"BLK-202609-{uuid.uuid4().hex[:5].upper()}",
        version_id=version.id,
        transaction_hash="0x" + "a" * 64,
        block_number=4512930,
        block_hash="0x" + "b" * 64,
        onchain_record_id=1,
        smart_contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        anchored_hash="0x" + "c" * 64,
        ipfs_cid_anchored="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        submitter_wallet="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        author_wallet="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        network_name="hardhat",
        chain_id=31337,
        anchored_timestamp=datetime.now(timezone.utc),
    )
    db_session.add(record)
    db_session.flush()

    assert version.blockchain_record is not None
    assert version.blockchain_record.transaction_hash.startswith("0x")
    assert version.blockchain_record.chain_id == 31337
    assert record.version.registration_id == "REG-2026-QNTM01"


def test_duplicate_project_membership_rejected(db_session: Session):
    """Test 7: Duplicate membership for the same project/user is rejected."""
    user = User(
        public_id=f"USR-202609-{uuid.uuid4().hex[:5].upper()}",
        email=f"dup_user_{uuid.uuid4().hex[:6]}@sih2026.edu",
        hashed_password="mock_password",
        full_name="Duplicate Tester",
        role=UserRole.STUDENT,
    )
    project = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"duplicate-membership-project-{uuid.uuid4().hex[:6]}",
        title="Duplicate Test Project",
        category="OTHER",
        department="Computer Science",
        academic_year="2025-2026",
    )
    db_session.add_all([user, project])
    db_session.flush()

    m1 = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role_in_project=ProjectMemberRole.LEAD,
    )
    db_session.add(m1)
    db_session.flush()

    # Attempt duplicate membership
    m2 = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role_in_project=ProjectMemberRole.CONTRIBUTOR,
    )
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_duplicate_registration_id_rejected(db_session: Session):
    """Test 8: Duplicate registration_id across versions is strictly rejected."""
    project1 = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"project-alpha-{uuid.uuid4().hex[:6]}",
        title="Project Alpha",
        category="AI",
        department="CS",
        academic_year="2025-2026",
    )
    project2 = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"project-beta-{uuid.uuid4().hex[:6]}",
        title="Project Beta",
        category="AI",
        department="CS",
        academic_year="2025-2026",
    )
    db_session.add_all([project1, project2])
    db_session.flush()

    shared_reg_id = "REG-2026-SHARED01"

    v1 = ProjectVersion(
        public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project1.id,
        registration_id=shared_reg_id,
        version_index=1,
        version_tag="v1.0",
        lifecycle_stage=ProjectVersionStage.IDEA,
        title="Alpha Milestone",
    )
    db_session.add(v1)
    db_session.flush()

    # Second version attempting same registration_id
    v2 = ProjectVersion(
        public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project2.id,
        registration_id=shared_reg_id,
        version_index=1,
        version_tag="v1.0",
        lifecycle_stage=ProjectVersionStage.IDEA,
        title="Beta Milestone",
    )
    db_session.add(v2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_project_version_lifecycle_values(db_session: Session):
    """Test 9: Valid lifecycle stages and anchoring statuses for ProjectVersion."""
    project = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"lifecycle-test-project-{uuid.uuid4().hex[:6]}",
        title="Lifecycle Project",
        category="AI",
        department="CS",
        academic_year="2025-2026",
    )
    db_session.add(project)
    db_session.flush()

    stages = [
        ProjectVersionStage.IDEA,
        ProjectVersionStage.DESIGN,
        ProjectVersionStage.PROTOTYPE,
        ProjectVersionStage.FINAL,
    ]
    statuses = [
        AnchoringStatus.DRAFT,
        AnchoringStatus.PENDING,
        AnchoringStatus.ANCHORING,
        AnchoringStatus.ANCHORED,
        AnchoringStatus.FAILED,
    ]

    for idx, (stage, status) in enumerate(zip(stages, statuses), start=1):
        version = ProjectVersion(
            public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
            project_id=project.id,
            version_index=idx,
            version_tag=f"v{idx}.0",
            lifecycle_stage=stage,
            title=f"Stage {stage.value} Version",
            anchoring_status=status,
        )
        db_session.add(version)
        db_session.flush()

        assert version.lifecycle_stage == stage
        assert version.anchoring_status == status


def test_dispute_status_separate_from_version_status(db_session: Session):
    """Test 10: Dispute lifecycle is strictly separated from ProjectVersion lifecycle."""
    claimant = User(
        public_id=f"USR-202609-{uuid.uuid4().hex[:5].upper()}",
        email=f"claimant_{uuid.uuid4().hex[:6]}@sih2026.edu",
        hashed_password="mock_password",
        full_name="Dr. Claimant",
        role=UserRole.FACULTY,
    )
    admin = User(
        public_id=f"USR-202609-{uuid.uuid4().hex[:5].upper()}",
        email=f"admin_{uuid.uuid4().hex[:6]}@sih2026.edu",
        hashed_password="mock_password",
        full_name="Admin Reviewer",
        role=UserRole.ADMIN,
    )
    project = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"disputed-project-{uuid.uuid4().hex[:6]}",
        title="Disputed Blockchain Project",
        category="WEB3",
        department="CS",
        academic_year="2025-2026",
    )
    db_session.add_all([claimant, admin, project])
    db_session.flush()

    # ProjectVersion remains ANCHORED while Dispute is OPEN / UNDER_REVIEW
    version = ProjectVersion(
        public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project.id,
        version_index=1,
        version_tag="v1.0",
        lifecycle_stage=ProjectVersionStage.FINAL,
        title="Anchored Version Under Dispute",
        anchoring_status=AnchoringStatus.ANCHORED,
        dispute_status=DisputeStatus.UNDER_REVIEW,
    )
    dispute = Dispute(
        public_id=f"DSP-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project.id,
        claimant_user_id=claimant.id,
        dispute_type=DisputeType.PLAGIARISM,
        claim_description="Claimant asserts prior art published in IEEE 2024.",
        evidence_url="https://doi.org/10.1109/MOCK.2024.123456",
        status=DisputeStatus.UNDER_REVIEW,
        resolution_notes="Investigation initiated by institutional committee.",
        resolved_by_admin_id=admin.id,
    )
    db_session.add_all([version, dispute])
    db_session.flush()

    # Assert independence
    assert version.anchoring_status == AnchoringStatus.ANCHORED
    assert version.dispute_status == DisputeStatus.UNDER_REVIEW
    assert dispute.status == DisputeStatus.UNDER_REVIEW
    assert dispute.claimant.full_name == "Dr. Claimant"
    assert dispute.resolver.full_name == "Admin Reviewer"
    assert dispute.project.title == "Disputed Blockchain Project"


def test_notification_creation(db_session: Session):
    """Test 11: Notification model creation and recipient relationship."""
    user = User(
        public_id=f"USR-202609-{uuid.uuid4().hex[:5].upper()}",
        email=f"notify_{uuid.uuid4().hex[:6]}@sih2026.edu",
        hashed_password="mock_password",
        full_name="Notification Recipient",
        role=UserRole.STUDENT,
    )
    db_session.add(user)
    db_session.flush()

    notification = Notification(
        public_id=f"NTF-202609-{uuid.uuid4().hex[:5].upper()}",
        user_id=user.id,
        title="Blockchain Anchoring Confirmed",
        message="Your milestone v1.0 has been successfully anchored on-chain.",
        notification_type=NotificationType.BLOCKCHAIN_CONFIRMATION,
        link_url="/projects/PRJ-202609-00001/versions/1",
        is_read=False,
    )
    db_session.add(notification)
    db_session.flush()

    assert notification.id is not None
    assert notification.is_read is False
    assert notification.notification_type == NotificationType.BLOCKCHAIN_CONFIRMATION
    assert len(user.notifications) == 1
    assert user.notifications[0].title == "Blockchain Anchoring Confirmed"


def test_version_index_unique_per_project(db_session: Session):
    """Test 12: version_index must be unique per project."""
    project = Project(
        public_id=f"PRJ-202609-{uuid.uuid4().hex[:5].upper()}",
        slug=f"version-index-project-{uuid.uuid4().hex[:6]}",
        title="Version Index Project",
        category="AI",
        department="CS",
        academic_year="2025-2026",
    )
    db_session.add(project)
    db_session.flush()

    v1 = ProjectVersion(
        public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project.id,
        version_index=1,
        version_tag="v1.0",
        lifecycle_stage=ProjectVersionStage.IDEA,
        title="Version 1",
    )
    db_session.add(v1)
    db_session.flush()

    # Attempt second version with duplicate version_index=1 for same project
    v1_dup = ProjectVersion(
        public_id=f"VER-202609-{uuid.uuid4().hex[:5].upper()}",
        project_id=project.id,
        version_index=1,
        version_tag="v1.0-duplicate",
        lifecycle_stage=ProjectVersionStage.DESIGN,
        title="Version 1 Duplicate",
    )
    db_session.add(v1_dup)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
