"""Unit tests for canonical role loader/persist wiring (no live DB)."""

from __future__ import annotations

from unittest.mock import MagicMock

from agents.analytics.canonical_roles.loader import _row_to_features
from agents.analytics.canonical_roles.persist import persist_clustering_result
from agents.analytics.clustering.types import ClusteringResult


def test_row_to_features_parses_skill_name_and_label_fallback() -> None:
    row = {
        "job_posting_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "title": "Software Engineer",
        "company_id": "cccccccc-dddd-eeee-ffff-000000000001",
        "company_name": "Acme",
        "quality_score": 0.85,
        "seniority": "mid",
        "skills": [{"skill_name": "Go"}, {"label": "LegacySkill"}],
        "tools": [{"tool_name": "Git"}],
        "responsibilities": [{"responsibility_description": "Ship features"}],
    }
    f = _row_to_features(row)
    assert f.posting_id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert f.skills == ["Go", "LegacySkill"]
    assert f.tools == ["Git"]
    assert f.responsibilities == ["Ship features"]
    assert f.quality_score == 0.85
    assert f.seniority == "mid"


def test_persist_skipped_no_session_add() -> None:
    session = MagicMock()
    result = ClusteringResult(
        assignments=[],
        clusters=[],
        emergence_candidates=[],
        total_input_postings=10,
        eligible_posting_count=0,
        clustered_posting_count=0,
        noise_posting_count=0,
        skipped=True,
        skip_reason="insufficient_total_postings",
    )
    out = persist_clustering_result(session, result, correlation_id="test-corr")
    assert out["cluster_id_to_role_id"] == {}
    assert out["roles_inserted"] == 0
    session.add.assert_not_called()
