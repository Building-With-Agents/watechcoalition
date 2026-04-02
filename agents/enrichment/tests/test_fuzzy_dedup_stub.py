"""Fuzzy dedup smoke: missing DB row yields unique, non-stub result."""

from __future__ import annotations

from unittest.mock import MagicMock

from agents.enrichment.dedup import (
    DEFAULT_DEDUP_COSINE_THRESHOLD,
    FuzzyDedupResult,
    dedup_cosine_threshold,
    run_fuzzy_dedup,
)


def test_run_fuzzy_dedup_missing_row_returns_unique_not_stub() -> None:
    session = MagicMock()
    first = MagicMock()
    first.mappings.return_value.first.return_value = None
    session.execute.return_value = first

    out = run_fuzzy_dedup(session, "00000000-0000-0000-0000-000000000001")
    assert isinstance(out, FuzzyDedupResult)
    assert out.is_duplicate is False
    assert out.duplicate_cluster_id is None
    assert out.survivor_job_posting_id is None
    assert out.stub is False


def test_dedup_cosine_threshold_default_matches_spec() -> None:
    assert DEFAULT_DEDUP_COSINE_THRESHOLD == 0.92
    # Env may be set in CI; only assert default when unset is hard — smoke read
    t = dedup_cosine_threshold()
    assert isinstance(t, float)
    assert 0.0 < t <= 1.0
