"""Staleness detection for posting freshness (pure helpers, no I/O)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from agents.common.data_store.models import (
    FRESH_THRESHOLD_DAYS,
    STALE_THRESHOLD_DAYS,
    classify_freshness,
)


@dataclass(frozen=True)
class PostingFreshnessResult:
    posting_id: str
    days_since_posted: int
    freshness_status: Literal["fresh", "stale", "expired"]
    reason: str


def _reason_for(days: int, status: Literal["fresh", "stale", "expired"]) -> str:
    return (
        f"{days} days since posted; classified {status} (fresh ≤{FRESH_THRESHOLD_DAYS}, stale ≤{STALE_THRESHOLD_DAYS})"
    )


def detect_staleness(records: list[dict]) -> list[PostingFreshnessResult]:
    """Classify each record by ``days_since_posted`` using :func:`classify_freshness`.

    Each dict must include ``posting_id`` and ``days_since_posted`` (coerced to ``str`` / ``int``).
    """
    out: list[PostingFreshnessResult] = []
    for rec in records:
        posting_id = str(rec["posting_id"])
        days = int(rec["days_since_posted"])
        status = classify_freshness(days)
        out.append(
            PostingFreshnessResult(
                posting_id=posting_id,
                days_since_posted=days,
                freshness_status=status,
                reason=_reason_for(days, status),
            )
        )
    return out
