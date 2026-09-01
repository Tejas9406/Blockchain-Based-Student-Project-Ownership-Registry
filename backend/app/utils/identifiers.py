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
