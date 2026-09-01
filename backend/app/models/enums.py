import enum


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    ADMIN = "ADMIN"
    VERIFIER = "VERIFIER"


class ProjectVisibility(str, enum.Enum):
    PUBLIC = "PUBLIC"
    INSTITUTIONAL = "INSTITUTIONAL"
    PRIVATE = "PRIVATE"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    UNDER_DISPUTE = "UNDER_DISPUTE"


class ProjectMemberRole(str, enum.Enum):
    LEAD = "LEAD"
    CONTRIBUTOR = "CONTRIBUTOR"
    FACULTY_MENTOR = "FACULTY_MENTOR"


class ProjectVersionStage(str, enum.Enum):
    IDEA = "IDEA"
    DESIGN = "DESIGN"
    PROTOTYPE = "PROTOTYPE"
    FINAL = "FINAL"


class ProjectVersionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    ANCHORING = "ANCHORING"
    ANCHORED = "ANCHORED"
    FAILED = "FAILED"


# Alias for AnchoringStatus to support both naming conventions seamlessly
AnchoringStatus = ProjectVersionStatus


class DisputeStatus(str, enum.Enum):
    NONE = "NONE"
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class DisputeType(str, enum.Enum):
    PLAGIARISM = "PLAGIARISM"
    UNAUTHORIZED_USE = "UNAUTHORIZED_USE"
    CITATION_FAILURE = "CITATION_FAILURE"
    OTHER = "OTHER"


class ArtifactCategory(str, enum.Enum):
    SOURCE_CODE = "SOURCE_CODE"
    DOCUMENTATION = "DOCUMENTATION"
    DESIGN_SPEC = "DESIGN_SPEC"
    PRESENTATION = "PRESENTATION"
    OTHER = "OTHER"


class NotificationType(str, enum.Enum):
    BLOCKCHAIN_CONFIRMATION = "BLOCKCHAIN_CONFIRMATION"
    TEAM_INVITE = "TEAM_INVITE"
    DISPUTE_ALERT = "DISPUTE_ALERT"
    SYSTEM = "SYSTEM"
