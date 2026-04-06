"""Posting freshness row shaping and optional persistence to ``dbo.posting_freshness`` (#184).

**duration_days**

- If ``first_seen`` and ``last_seen`` are present on the input record (ISO strings,
  ``datetime``, or values coercible via :func:`datetime.fromisoformat`), then
  ``duration_days = max(0, (last_seen - first_seen).days)``.
- Otherwise ``duration_days = int(record.get("days_since_posted") or 0)``. We set
  ``last_seen`` to *computed_at* and ``first_seen`` to ``last_seen - timedelta(days=duration_days)``
  when *duration_days* > 0 so first/last bounds match the staleness age; when
  *duration_days* is 0, ``first_seen == last_seen == computed_at``.

**fill_proxy**

- ``True`` when the record sets any of ``fill_proxy``, ``is_fill_proxy``, or
  ``enrichment_fill_proxy`` to a truthy value, or when ``stub`` / ``fuzzy_dedup_stub``
  is true (dedup placeholder / thin row). Default ``False``.

**Reposts**

- ``is_repost`` from ``is_duplicate`` / ``is_repost`` on the record.
- ``repost_count`` from ``repost_count``; if ``is_repost`` and count is 0, use ``1``.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

log = structlog.get_logger()


def _parse_iso(dt_val: Any) -> datetime | None:
    if not dt_val or not isinstance(dt_val, str):
        return None
    try:
        return datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
    except ValueError:
        return None


def _coerce_datetime(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    if isinstance(val, str):
        return _parse_iso(val)
    return None


def build_posting_freshness_row_dicts(
    records: list[dict[str, Any]],
    computed_at: datetime,
) -> list[dict[str, Any]]:
    """Build runbook-shaped rows for in-memory guardrails, LLM summary, and optional DB upsert."""
    if computed_at.tzinfo is None:
        computed_at = computed_at.replace(tzinfo=timezone.utc)

    rows: list[dict[str, Any]] = []
    for r in records:
        pid = r.get("posting_id")
        if pid is None:
            continue

        first_raw = _coerce_datetime(r.get("first_seen"))
        last_raw = _coerce_datetime(r.get("last_seen"))
        days_fallback = int(r.get("days_since_posted") or 0)

        if first_raw is not None and last_raw is not None:
            first, last = first_raw, last_raw
            duration_days = max(0, (last - first).days)
        elif last_raw is not None:
            last = last_raw
            first = last - timedelta(days=days_fallback) if days_fallback > 0 else last
            duration_days = max(0, (last - first).days)
        elif first_raw is not None:
            first = first_raw
            last = computed_at
            duration_days = max(0, (last - first).days)
        else:
            duration_days = max(0, days_fallback)
            last = computed_at
            first = last - timedelta(days=duration_days) if duration_days > 0 else last

        is_repost = bool(r.get("is_duplicate") or r.get("is_repost"))
        repost_count = int(r.get("repost_count") or 0)
        if is_repost and repost_count == 0:
            repost_count = 1

        fill_proxy = bool(
            r.get("fill_proxy")
            or r.get("is_fill_proxy")
            or r.get("enrichment_fill_proxy")
            or r.get("stub")
            or r.get("fuzzy_dedup_stub")
        )

        rows.append(
            {
                "posting_id": str(pid),
                "first_seen": first,
                "last_seen": last,
                "duration_days": duration_days,
                "is_repost": is_repost,
                "repost_count": repost_count,
                "fill_proxy": fill_proxy,
                "computed_at": computed_at,
            }
        )
    return rows


def persist_posting_freshness_rows(rows: list[dict[str, Any]]) -> None:
    """Upsert rows via ``session.merge`` when ``PYTHON_DATABASE_URL`` is set and DB is reachable."""
    if not rows:
        return
    if not os.getenv("PYTHON_DATABASE_URL"):
        return

    from agents.common.data_store.database import check_db_connection, session_scope
    from agents.common.data_store.models import PostingFreshness

    if not check_db_connection():
        log.info(
            "posting_freshness_persist_skipped",
            reason="db_unreachable",
            row_count=len(rows),
        )
        return

    try:
        with session_scope() as session:
            for row in rows:
                session.merge(
                    PostingFreshness(
                        posting_id=row["posting_id"],
                        first_seen=row["first_seen"],
                        last_seen=row["last_seen"],
                        duration_days=row["duration_days"],
                        is_repost=row["is_repost"],
                        repost_count=row["repost_count"],
                        fill_proxy=row["fill_proxy"],
                        computed_at=row["computed_at"],
                    )
                )
        log.info("posting_freshness_persisted", row_count=len(rows))
    except Exception as exc:
        log.warning(
            "posting_freshness_persist_failed",
            error=str(exc),
            row_count=len(rows),
        )
