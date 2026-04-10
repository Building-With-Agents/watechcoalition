"""Tests for analytics trajectory map scaffold."""

from __future__ import annotations

import pytest

from agents.analytics.insights.trajectory import build_trajectory_map, classify_trajectory


def test_rising_skill_current_gt_prior() -> None:
    rows = [{"label": "Python", "current_count": 10, "prior_count": 5, "confidence": 0.9}]
    m = build_trajectory_map(rows)
    assert m["Python"]["trend"] == "rising"
    assert m["Python"]["delta"] == 5.0
    assert m["Python"]["confidence"] == 0.9


def test_declining_skill_current_lt_prior() -> None:
    rows = [{"label": "Rust", "current_count": 3, "prior_count": 8, "confidence": 0.85}]
    m = build_trajectory_map(rows)
    assert m["Rust"]["trend"] == "declining"
    assert m["Rust"]["delta"] == -5.0


def test_stable_skill_current_eq_prior() -> None:
    rows = [{"label": "Go", "current_count": 12, "prior_count": 12, "confidence": 0.7}]
    m = build_trajectory_map(rows)
    assert m["Go"]["trend"] == "stable"
    assert m["Go"]["delta"] == 0.0


def test_sector_key_sector_prefix() -> None:
    rows = [
        {
            "label": "sector:healthcare",
            "current_count": 100,
            "prior_count": 95,
            "confidence": 0.75,
        },
    ]
    m = build_trajectory_map(rows)
    assert "sector:healthcare" in m
    assert m["sector:healthcare"]["trend"] == "rising"
    assert m["sector:healthcare"]["delta"] == 5.0


def test_mixed_batch_skills_and_sectors() -> None:
    rows = [
        {"label": "Kubernetes", "current_count": 20, "prior_count": 18, "confidence": 0.8},
        {"label": "sector:finance", "current_count": 40, "prior_count": 50, "confidence": 0.6},
    ]
    m = build_trajectory_map(rows)
    assert set(m.keys()) == {"Kubernetes", "sector:finance"}
    assert m["Kubernetes"]["trend"] == "rising"
    assert m["sector:finance"]["trend"] == "declining"


def test_empty_input_returns_empty_dict() -> None:
    assert build_trajectory_map([]) == {}


@pytest.mark.parametrize(
    ("delta", "expected"),
    [
        (3.5, "rising"),
        (-2.0, "declining"),
        (0.0, "stable"),
    ],
)
def test_classify_trajectory_direct(delta: float, expected: str) -> None:
    assert classify_trajectory(delta) == expected
