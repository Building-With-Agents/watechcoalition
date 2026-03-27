"""Unit tests for spam preview tiers and degradation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.enrichment.classifiers.spam_preview import (
    apply_spam_tiers,
    score_spam_preview,
)


def test_apply_spam_tiers_boundaries_explicit_thresholds() -> None:
    f, r = 0.7, 0.9
    assert apply_spam_tiers(0.69, flag=f, reject=r) == (False, "clean")
    assert apply_spam_tiers(0.7, flag=f, reject=r) == (None, "flagged")
    assert apply_spam_tiers(0.9, flag=f, reject=r) == (None, "flagged")
    assert apply_spam_tiers(0.91, flag=f, reject=r) == (True, "rejected")


def test_apply_spam_tiers_custom_thresholds() -> None:
    assert apply_spam_tiers(0.5, flag=0.6, reject=0.8) == (False, "clean")
    assert apply_spam_tiers(0.65, flag=0.6, reject=0.8) == (None, "flagged")
    assert apply_spam_tiers(0.85, flag=0.6, reject=0.8) == (True, "rejected")


def test_score_spam_preview_degraded_no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SPAM_PREVIEW_ALLOW_HEURISTIC", raising=False)
    with patch("agents.common.llm_client.invoke_skills_llm") as m:
        m.side_effect = ValueError("no deployment")
        r = score_spam_preview(
            job_title="Engineer",
            job_description="Build things.",
            extraction={"skills": []},
            extraction_failed=False,
            extraction_empty=False,
        )
    assert r.spam_score is None
    assert r.is_spam is None
    assert r.tier == "uncertain"
    assert r.degraded is True
    assert r.field_confidence == {}


def test_score_spam_preview_successful_parse() -> None:
    payload = '{"spam_score": 0.4, "rationale": "ok", "spam_confidence": 0.9}'
    with patch("agents.common.llm_client.invoke_skills_llm") as m:
        m.return_value = (
            payload,
            {
                "success": True,
                "extraction_failed": False,
            },
        )
        r = score_spam_preview(
            job_title="Engineer",
            job_description="Build things.",
            extraction={},
            extraction_failed=False,
            extraction_empty=True,
        )
    assert r.degraded is False
    assert r.spam_score == 0.4
    assert r.tier == "clean"
    assert "spam_score" in r.field_confidence
