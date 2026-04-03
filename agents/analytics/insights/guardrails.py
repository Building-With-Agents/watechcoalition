"""Analytics aggregate staleness guardrails (pure helpers, no I/O)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

STALENESS_THRESHOLD_MINUTES = int(os.getenv("STALENESS_THRESHOLD_MINUTES", "15"))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def check_staleness(table_name: str, computed_at: datetime) -> bool:
    """Return True if ``computed_at`` is strictly older than :data:`STALENESS_THRESHOLD_MINUTES`.

    Comparison uses UTC. ``table_name`` is reserved for call-site context (e.g. logging); it does
    not affect the result. Current time is obtained via :func:`_utc_now` (patchable in tests).
    """
    _ = table_name
    now = _utc_now()
    computed = _ensure_utc(computed_at)
    age = now - computed
    return age > timedelta(minutes=STALENESS_THRESHOLD_MINUTES)


def build_stale_alert_payload(
    table_name: str,
    computed_at: datetime,
    queried_at: datetime,
) -> dict[str, Any]:
    """Build an ``AnalyticsStaleAlert``-shaped payload dict (``event_type`` + staleness fields)."""
    ca = _ensure_utc(computed_at)
    qa = _ensure_utc(queried_at)
    age_td = qa - ca
    age_minutes = int(age_td.total_seconds() // 60)
    return {
        "event_type": "AnalyticsStaleAlert",
        "table_name": table_name,
        "computed_at": ca.isoformat(),
        "queried_at": qa.isoformat(),
        "age_minutes": age_minutes,
    }
