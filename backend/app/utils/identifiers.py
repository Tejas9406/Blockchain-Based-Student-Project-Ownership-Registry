import secrets
from datetime import datetime, timezone


def generate_user_public_id() -> str:
    """
    Generates a public user identifier conforming to DATABASE_DESIGN.md Section 7.
    Format: USR-YYYYMM-XXXXX (e.g. USR-202609-8F29A)
    """
    now = datetime.now(timezone.utc)
    year_month = now.strftime("%Y%m")
    random_hex = secrets.token_hex(3)[:5].upper()
    return f"USR-{year_month}-{random_hex}"


def generate_project_public_id() -> str:
    """
    Generates a public project identifier conforming to DATABASE_DESIGN.md Section 7.
    Format: PRJ-YYYYMM-XXXXX (e.g. PRJ-202609-99B12)
    """
    now = datetime.now(timezone.utc)
    year_month = now.strftime("%Y%m")
    random_hex = secrets.token_hex(3)[:5].upper()
    return f"PRJ-{year_month}-{random_hex}"


def generate_version_public_id() -> str:
    """
    Generates a public version identifier conforming to DATABASE_DESIGN.md Section 7.
    Format: VER-YYYYMM-XXXXX (e.g. VER-202609-41C88)
    """
    now = datetime.now(timezone.utc)
    year_month = now.strftime("%Y%m")
    random_hex = secrets.token_hex(3)[:5].upper()
    return f"VER-{year_month}-{random_hex}"


def generate_registration_id() -> str:
    """
    Generates a universal certificate registration ID conforming to DATABASE_DESIGN.md Section 7.
    Format: REG-YYYY-XXXXX (e.g. REG-2026-A8F92)
    """
    now = datetime.now(timezone.utc)
    year = now.strftime("%Y")
    random_hex = secrets.token_hex(3)[:5].upper()
    return f"REG-{year}-{random_hex}"


def generate_artifact_public_id() -> str:
    """
    Generates a public artifact identifier conforming to DATABASE_DESIGN.md Section 7.
    Format: ART-YYYYMM-XXXXX (e.g. ART-202609-11E54)
    """
    now = datetime.now(timezone.utc)
    year_month = now.strftime("%Y%m")
    random_hex = secrets.token_hex(3)[:5].upper()
    return f"ART-{year_month}-{random_hex}"
