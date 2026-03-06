"""
Shared datetime formatting for display, storage, and run logs.
Single place for ISO timestamp → human-readable UTC and for UTC now → ISO string.
"""
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Current time as ISO 8601 UTC string (Z suffix). Use for started_at, finished_at, logs."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def datetime_to_iso_utc(dt: datetime) -> str:
    """Convert datetime to ISO 8601 UTC string (Z suffix). Use for run log and event timestamps."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def format_iso_timestamp_for_display(iso_timestamp: str) -> str:
    """Format ISO timestamp for human-readable display (e.g. Feb 27, 2026 at 3:45 PM UTC)."""
    if not iso_timestamp or iso_timestamp == "—":
        return "—"
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y at %I:%M %p UTC").replace(" 0", " ")
    except (ValueError, TypeError):
        return iso_timestamp
