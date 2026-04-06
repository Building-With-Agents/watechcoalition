"""Tests for agents.analytics.insights.llm_summary."""

from __future__ import annotations

from unittest.mock import patch

from agents.analytics.insights.freshness import PostingFreshnessResult
from agents.analytics.insights.llm_summary import (
    FALLBACK_TEMPLATE,
    generate_summaries,
    generate_summary,
)
from agents.analytics.insights.trajectory import TrajectoryEntry


def _sample_freshness() -> list[PostingFreshnessResult]:
    return [
        PostingFreshnessResult(
            posting_id="a",
            days_since_posted=5,
            freshness_status="fresh",
            reason="ok",
        ),
        PostingFreshnessResult(
            posting_id="b",
            days_since_posted=40,
            freshness_status="stale",
            reason="ok",
        ),
    ]


def _sample_trajectory() -> TrajectoryEntry:
    return TrajectoryEntry(trend="rising", delta=12.0, confidence=0.91)


@patch("agents.analytics.insights.llm_summary.complete")
def test_llm_success_sets_flags_and_model(mock_complete):
    mock_complete.return_value = {
        "content": "Paragraph one.\n\nParagraph two.\n\nParagraph three.",
        "input_tokens": 10,
        "output_tokens": 20,
        "cost_usd": 0.0,
        "model_tier": "sonnet",
        "success": True,
        "extraction_failed": False,
    }
    traj = _sample_trajectory()
    fresh = _sample_freshness()
    r = generate_summary("Python", traj, fresh)
    assert r["is_llm_generated"] is True
    assert r["model_used"] == "claude-sonnet-4-5"
    assert r["summary_text"].strip() != ""
    assert "Paragraph one" in r["summary_text"]
    mock_complete.assert_called_once()


@patch("agents.analytics.insights.llm_summary.complete")
def test_llm_exception_uses_fallback(mock_complete):
    mock_complete.side_effect = RuntimeError("api down")
    traj = _sample_trajectory()
    fresh = _sample_freshness()
    r = generate_summary("Rust", traj, fresh)
    assert r["is_llm_generated"] is False
    assert r["model_used"] is None
    assert "Generated from template" in r["summary_text"]


@patch("agents.analytics.insights.llm_summary.complete")
def test_empty_content_uses_fallback(mock_complete):
    mock_complete.return_value = {
        "content": "   ",
        "success": True,
        "extraction_failed": False,
    }
    traj = _sample_trajectory()
    r = generate_summary("Go", traj, [])
    assert r["is_llm_generated"] is False
    assert r["model_used"] is None


def test_sector_key_sets_sector_label_only():
    tm: dict[str, TrajectoryEntry] = {
        "sector:healthcare": TrajectoryEntry(trend="stable", delta=0.0, confidence=0.8),
    }
    fresh = _sample_freshness()
    with patch("agents.analytics.insights.llm_summary.complete") as mock_complete:
        mock_complete.return_value = {
            "content": "x",
            "success": True,
            "extraction_failed": False,
        }
        out = generate_summaries(tm, fresh)
    assert len(out) == 1
    assert out[0]["sector_label"] == "healthcare"
    assert out[0]["skill_label"] is None


def test_skill_key_sets_skill_label_only():
    tm = {"Python": TrajectoryEntry(trend="rising", delta=1.0, confidence=0.9)}
    with patch("agents.analytics.insights.llm_summary.complete") as mock_complete:
        mock_complete.return_value = {
            "content": "y",
            "success": True,
            "extraction_failed": False,
        }
        out = generate_summaries(tm, [])
    assert out[0]["skill_label"] == "Python"
    assert out[0]["sector_label"] is None


def test_generate_summaries_mixed_map_order_and_labels():
    tm: dict[str, TrajectoryEntry] = {
        "Python": TrajectoryEntry(trend="rising", delta=1.0, confidence=0.9),
        "sector:finance": TrajectoryEntry(trend="declining", delta=-2.0, confidence=0.7),
    }
    with patch("agents.analytics.insights.llm_summary.complete") as mock_complete:
        mock_complete.return_value = {
            "content": "ok",
            "success": True,
            "extraction_failed": False,
        }
        out = generate_summaries(tm, _sample_freshness())
    assert len(out) == 2
    assert out[0]["skill_label"] == "Python" and out[0]["sector_label"] is None
    assert out[1]["sector_label"] == "finance" and out[1]["skill_label"] is None


@patch("agents.analytics.insights.llm_summary.complete")
def test_fallback_contains_numeric_trend_and_delta(mock_complete):
    mock_complete.side_effect = ValueError("no network")
    traj = TrajectoryEntry(trend="declining", delta=-7.0, confidence=0.55)
    fresh = [
        PostingFreshnessResult(
            posting_id="p",
            days_since_posted=1,
            freshness_status="fresh",
            reason="r",
        )
    ]
    r = generate_summary("Kotlin", traj, fresh)
    assert r["is_llm_generated"] is False
    assert "declining" in r["summary_text"]
    assert "-7" in r["summary_text"] or "−7" in r["summary_text"]
    # Template uses ASCII minus in format
    expected = FALLBACK_TEMPLATE.format(
        label="Kotlin",
        trend="declining",
        delta=-7.0,
        freshness_count=1,
        confidence=0.55,
    )
    assert r["summary_text"] == expected


def test_generate_summary_never_raises():
    with patch("agents.analytics.insights.llm_summary.complete") as mock_complete:
        mock_complete.side_effect = RuntimeError("anything")
        r = generate_summary("X", TrajectoryEntry(trend="stable", delta=0.0, confidence=1.0), [])
    assert r["summary_text"]
    assert r["is_llm_generated"] is False
