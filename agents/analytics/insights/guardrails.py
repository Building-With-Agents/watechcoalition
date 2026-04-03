"""Analytics aggregate staleness guardrails (pure helpers, no I/O)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

STALENESS_THRESHOLD_MINUTES = int(os.getenv("STALENESS_THRESHOLD_MINUTES", "15"))
CARDINALITY_CAP = int(os.getenv("CARDINALITY_CAP", "500"))


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


def cap_cardinality(values: list[str], limit: int | None = None) -> tuple[list[str], bool]:
    """Cap a list of category labels; overflow is coalesced into a single ``\"Other\"`` bucket.

    If ``limit`` is ``None``, uses :data:`CARDINALITY_CAP` (read on each call so tests can monkeypatch).

    Returns ``(capped_list, needs_warning)``. When capping, the result is ``values[:limit] + [\"Other\"]`` —
    ``\"Other\"`` appears exactly once at the end.
    """
    cap = CARDINALITY_CAP if limit is None else limit
    if len(values) <= cap:
        return (list(values), False)
    capped = list(values[:cap]) + ["Other"]
    return (capped, True)


def build_cardinality_warning_payload(
    table: str,
    column: str,
    original_count: int,
    cap: int,
) -> dict[str, Any]:
    """Build a ``CardinalityWarning``-shaped payload dict (see ``typed_events`` / runbook)."""
    return {
        "event_type": "CardinalityWarning",
        "table": table,
        "column": column,
        "cardinality_count": original_count,
        "threshold": cap,
        "triggered_at": _utc_now().isoformat(),
    }
