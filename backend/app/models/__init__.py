"""
Database ORM Models Package.

All domain models are exported here to ensure clean package-level imports
and automatic registration with SQLAlchemy Base.metadata.
"""

from app.models.enums import (
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
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.project_version import ProjectVersion
from app.models.artifact import Artifact
from app.models.blockchain_record import BlockchainRecord
from app.models.dispute import Dispute
from app.models.notification import Notification

__all__ = [
    # Enums
    "UserRole",
    "ProjectVisibility",
    "ProjectStatus",
    "ProjectMemberRole",
    "ProjectVersionStage",
    "ProjectVersionStatus",
    "AnchoringStatus",
    "DisputeStatus",
    "DisputeType",
    "ArtifactCategory",
    "NotificationType",
    # Models
    "User",
    "Project",
    "ProjectMember",
    "ProjectVersion",
    "Artifact",
    "BlockchainRecord",
    "Dispute",
    "Notification",
]
