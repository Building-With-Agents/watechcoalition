"""Trajectory map scaffold — pure helpers for skill/sector demand deltas (no I/O)."""

from __future__ import annotations

from typing import Literal, TypedDict


class TrajectoryEntry(TypedDict):
    trend: Literal["rising", "stable", "declining"]
    delta: float
    confidence: float


def classify_trajectory(delta: float) -> Literal["rising", "stable", "declining"]:
    """Map a posting-count delta vs the prior period to a coarse trend label."""
    if delta > 0:
        return "rising"
    if delta < 0:
        return "declining"
    return "stable"


def build_trajectory_map(records: list[dict]) -> dict[str, TrajectoryEntry]:
    """Build ``label`` → trajectory entry from aggregate-style rows.

    Each dict must include ``label``, ``current_count``, ``prior_count``, and ``confidence``.
    ``label`` is a skill name or ``sector:{name}``. ``delta`` is ``current_count - prior_count``.
    """
    out: dict[str, TrajectoryEntry] = {}
    for rec in records:
        label = str(rec["label"])
        current = int(rec["current_count"])
        prior = int(rec["prior_count"])
        confidence = float(rec["confidence"])
        delta = float(current - prior)
        trend = classify_trajectory(delta)
        entry: TrajectoryEntry = {
            "trend": trend,
            "delta": delta,
            "confidence": confidence,
        }
        out[label] = entry
    return out
