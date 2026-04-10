"""LLM-generated insight summaries with deterministic template fallback (Week 7)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import TypedDict

import structlog

from agents.analytics.insights.freshness import PostingFreshnessResult
from agents.analytics.insights.trajectory import TrajectoryEntry
from agents.common.llm_adapter import complete

log = structlog.get_logger()

_AGENT_NAME = "analytics-agent"
_DEFAULT_MODEL = os.getenv("EXTRACTION_MODEL_SKILLS", "claude-sonnet-4-5")


class SummaryResult(TypedDict):
    skill_label: str | None
    sector_label: str | None
    summary_text: str
    is_llm_generated: bool
    model_used: str | None
    generated_at: str


FALLBACK_TEMPLATE = (
    "{label} is {trend} with a posting delta of {delta:+.0f} "
    "and {freshness_count} active postings tracked. "
    "Confidence: {confidence:.0%}. (Generated from template.)"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _freshness_counts(records: list[PostingFreshnessResult]) -> dict[str, int]:
    out = {"fresh": 0, "stale": 0, "expired": 0}
    for r in records:
        out[r.freshness_status] = out[r.freshness_status] + 1
    return out


def _build_prompt(label: str, trajectory: TrajectoryEntry, freshness_records: list[PostingFreshnessResult]) -> str:
    trend = trajectory["trend"]
    delta = trajectory["delta"]
    confidence = trajectory["confidence"]
    total = len(freshness_records)
    fc = _freshness_counts(freshness_records)
    lines = [
        f"Dimension label: {label}",
        f"Trend: {trend}",
        f"Posting-count delta vs prior period: {delta:+.0f}",
        f"Confidence (0–1): {confidence:.4f}",
        f"Postings in freshness sample: {total} (fresh={fc['fresh']}, stale={fc['stale']}, expired={fc['expired']})",
        "",
        "Write exactly 3–5 paragraphs of plain prose for workforce analytics stakeholders.",
        "Ground every claim in the numbers above; do not invent employers, job titles, or regions.",
        "Explain what the trend and delta imply for demand, and briefly relate freshness buckets to signal quality.",
    ]
    return "\n".join(lines)


def _fallback_summary(
    label: str,
    trajectory: TrajectoryEntry,
    freshness_records: list[PostingFreshnessResult],
    generated_at: str,
) -> SummaryResult:
    freshness_count = len(freshness_records)
    text = FALLBACK_TEMPLATE.format(
        label=label,
        trend=trajectory["trend"],
        delta=trajectory["delta"],
        freshness_count=freshness_count,
        confidence=trajectory["confidence"],
    )
    return {
        "skill_label": None,
        "sector_label": None,
        "summary_text": text,
        "is_llm_generated": False,
        "model_used": None,
        "generated_at": generated_at,
    }


def generate_summary(
    label: str,
    trajectory: TrajectoryEntry,
    freshness_records: list[PostingFreshnessResult],
) -> SummaryResult:
    """Produce an LLM summary or a deterministic template; never raises."""
    generated_at = _utc_now_iso()
    try:
        prompt = _build_prompt(label, trajectory, freshness_records)
        model = _DEFAULT_MODEL
        result = complete(
            prompt=prompt,
            agent_name=_AGENT_NAME,
            model=model,
            system=(
                "You are an analytics writer for labor-market intelligence. "
                "Use only the facts in the user message. Output 3–5 paragraphs with no markdown headings."
            ),
            max_tokens=1200,
        )
        content = (result.get("content") or "").strip()
        ok = bool(result.get("success") and not result.get("extraction_failed") and content)
        if ok:
            return {
                "skill_label": None,
                "sector_label": None,
                "summary_text": content,
                "is_llm_generated": True,
                "model_used": model,
                "generated_at": generated_at,
            }
        log.info(
            "analytics_insight_summary_llm_fallback",
            reason="empty_or_failed",
            label=label,
            extraction_failed=bool(result.get("extraction_failed")),
        )
    except Exception as exc:
        log.info(
            "analytics_insight_summary_llm_fallback",
            reason="exception",
            label=label,
            error_type=type(exc).__name__,
        )
    return _fallback_summary(label, trajectory, freshness_records, generated_at)


def generate_summaries(
    trajectory_map: dict[str, TrajectoryEntry],
    freshness_records: list[PostingFreshnessResult],
) -> list[SummaryResult]:
    """One summary per trajectory key; skill vs sector labels derived from key prefix."""
    out: list[SummaryResult] = []
    for key, traj in trajectory_map.items():
        base = generate_summary(key, traj, freshness_records)
        if key.startswith("sector:"):
            sector = key.split(":", 1)[1] if ":" in key else key
            item: SummaryResult = {
                **base,
                "sector_label": sector,
                "skill_label": None,
            }
        else:
            item = {
                **base,
                "skill_label": key,
                "sector_label": None,
            }
        out.append(item)
    return out
