"""Unit tests for canonical role loader/persist wiring (no live DB)."""

from __future__ import annotations

from unittest.mock import MagicMock

from agents.analytics.canonical_roles.loader import _row_to_features
from agents.analytics.canonical_roles.persist import (
    _build_cluster_role_ids,
    cleanup_orphan_canonical_roles,
    persist_clustering_result,
)
from agents.analytics.clustering.types import ClusteringResult, ClusterSummary
from agents.common.data_store.models import CanonicalRole


def _make_cluster(
    cluster_id: str,
    *,
    label: str,
    raw_cluster_label: int = 1,
) -> ClusterSummary:
    return ClusterSummary(
        cluster_id=cluster_id,
        raw_cluster_label=raw_cluster_label,
        label=label,
        label_source="dominant_title",
        member_posting_ids=["aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"],
        member_count=1,
        representative_titles=[label],
    )


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


def test_build_cluster_role_ids_stable_when_same_role_recomputed() -> None:
    first = _make_cluster("cluster-0001", label="Data Engineer", raw_cluster_label=7)
    second = _make_cluster("cluster-0009", label="Data Engineer", raw_cluster_label=42)

    first_ids = _build_cluster_role_ids([first])
    second_ids = _build_cluster_role_ids([second])

    assert first_ids["cluster-0001"] == second_ids["cluster-0009"]


def test_persist_reuses_existing_role_id_instead_of_adding_duplicate() -> None:
    cluster = _make_cluster("cluster-0001", label="Data Engineer")
    expected_role_id = _build_cluster_role_ids([cluster])["cluster-0001"]
    existing_role = CanonicalRole(
        role_id=expected_role_id,
        label="Old Label",
        representative_titles=["Old Label"],
    )

    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = [existing_role]

    session = MagicMock()
    session.execute.return_value = execute_result

    result = ClusteringResult(
        assignments=[],
        clusters=[cluster],
        emergence_candidates=[],
        total_input_postings=1,
        eligible_posting_count=1,
        clustered_posting_count=1,
        noise_posting_count=0,
        skipped=False,
        skip_reason=None,
    )

    out = persist_clustering_result(session, result, correlation_id="test-corr")

    assert out["cluster_id_to_role_id"]["cluster-0001"] == expected_role_id
    assert out["roles_inserted"] == 0
    assert existing_role.label == "Data Engineer"
    session.add.assert_not_called()


def test_cleanup_orphan_canonical_roles_checks_snapshots() -> None:
    session = MagicMock()
    session.execute.return_value.rowcount = 2

    deleted = cleanup_orphan_canonical_roles(session)

    assert deleted == 2
    stmt = str(session.execute.call_args.args[0])
    assert "role_snapshot_weekly" in stmt
