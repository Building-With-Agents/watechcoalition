"""Per-row slice for analytics posting freshness (``RecordEnriched.freshness_records``)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def coerce_days_since_posted(posting: dict[str, Any], enriched: dict[str, Any]) -> int:
    """Whole days since publish/posting date, or explicit ``days_since_posted`` on posting/enriched."""
    for src in (enriched, posting):
        raw = src.get("days_since_posted")
        if raw is not None:
            try:
                return max(0, int(raw))
            except (TypeError, ValueError):
                pass

    dp = enriched.get("date_posted") or posting.get("date_posted")
    if dp is None:
        return 0
    if isinstance(dp, datetime):
        dt = dp if dp.tzinfo else dp.replace(tzinfo=timezone.utc)
        return max(0, (_utc_now() - dt).days)
    if isinstance(dp, str):
        try:
            parsed = datetime.fromisoformat(dp.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return max(0, (_utc_now() - parsed).days)
        except ValueError:
            return 0
    return 0


def build_freshness_record_for_analytics(posting: dict[str, Any], enriched: dict[str, Any]) -> dict[str, Any]:
    """Minimal dict for :func:`agents.analytics.agent._records_from_record_enriched_payload`."""
    days = coerce_days_since_posted(posting, enriched)

    def _pick(key: str) -> Any:
        if key in enriched:
            return enriched[key]
        return posting.get(key)

    out: dict[str, Any] = {
        "posting_id": posting.get("posting_id"),
        "days_since_posted": days,
        "skills": enriched.get("skills") if enriched.get("skills") is not None else posting.get("skills") or [],
        "is_duplicate": _pick("is_duplicate"),
        "is_repost": _pick("is_repost"),
        "repost_count": _pick("repost_count"),
        "fill_proxy": _pick("fill_proxy"),
        "stub": _pick("stub"),
        "fuzzy_dedup_stub": _pick("fuzzy_dedup_stub"),
    }
    dp = _pick("date_posted")
    if dp is not None:
        out["date_posted"] = dp
    return out
