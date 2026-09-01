from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """
    Returns the current timezone-aware UTC datetime.
    """
    return datetime.now(timezone.utc)


def format_iso_utc(dt: Optional[datetime] = None) -> str:
    """
    Formats a datetime object as a strict ISO 8601 UTC string ending in 'Z'.
    Example: '2026-08-31T18:50:00.000Z'
    """
    if dt is None:
        dt = utc_now()
    elif dt.tzinfo is None:
        # Assume naive datetimes are UTC
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    # Format with millisecond precision and 'Z' suffix
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
