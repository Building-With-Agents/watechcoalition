"""Unit tests for enrichment promotion helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.enrichment.dedup.types import FuzzyDedupResult
from agents.enrichment.job_postings_promotion import apply_fuzzy_dedup_result

CURRENT_ID = "00000000-0000-0000-0000-000000000001"
MATCHED_ID = "00000000-0000-0000-0000-000000000002"
CLUSTER_ID = "00000000-0000-0000-0000-0000000000aa"


def _execute_params(session: MagicMock) -> list[dict]:
    return [call.args[1] for call in session.execute.call_args_list]


def _execute_sql(session: MagicMock) -> list[str]:
    return [str(call.args[0]) for call in session.execute.call_args_list]


def test_apply_fuzzy_dedup_result_clears_current_row_for_unique_posting() -> None:
    session = MagicMock()
    result = FuzzyDedupResult(
        is_duplicate=False,
        duplicate_cluster_id=None,
        matched_job_posting_id=None,
        survivor_job_posting_id=None,
        stub=False,
    )

    applied = apply_fuzzy_dedup_result(session, CURRENT_ID, result)

    assert applied is True
    assert session.execute.call_count == 1
    assert _execute_params(session) == [
        {
            "job_posting_id": CURRENT_ID,
            "is_duplicate": False,
            "duplicate_cluster_id": None,
        }
    ]
    assert "duplicate_cluster_id" in _execute_sql(session)[0]


def test_apply_fuzzy_dedup_result_marks_current_row_duplicate_and_keeps_survivor() -> None:
    session = MagicMock()
    result = FuzzyDedupResult(
        is_duplicate=True,
        duplicate_cluster_id=CLUSTER_ID,
        matched_job_posting_id=MATCHED_ID,
        survivor_job_posting_id=MATCHED_ID,
        stub=False,
    )

    applied = apply_fuzzy_dedup_result(session, CURRENT_ID, result)

    assert applied is True
    assert _execute_params(session) == [
        {
            "job_posting_id": CURRENT_ID,
            "is_duplicate": True,
            "duplicate_cluster_id": CLUSTER_ID,
        },
        {
            "job_posting_id": MATCHED_ID,
            "is_duplicate": False,
            "duplicate_cluster_id": CLUSTER_ID,
        },
    ]


def test_apply_fuzzy_dedup_result_flips_prior_survivor_when_current_row_wins() -> None:
    session = MagicMock()
    result = FuzzyDedupResult(
        is_duplicate=False,
        duplicate_cluster_id=CLUSTER_ID,
        matched_job_posting_id=MATCHED_ID,
        survivor_job_posting_id=CURRENT_ID,
        stub=False,
    )

    applied = apply_fuzzy_dedup_result(session, CURRENT_ID, result)

    assert applied is True
    assert _execute_params(session) == [
        {
            "job_posting_id": CURRENT_ID,
            "is_duplicate": False,
            "duplicate_cluster_id": CLUSTER_ID,
        },
        {
            "job_posting_id": MATCHED_ID,
            "is_duplicate": True,
            "duplicate_cluster_id": CLUSTER_ID,
        },
    ]


def test_apply_fuzzy_dedup_result_skips_stub_results() -> None:
    session = MagicMock()
    result = FuzzyDedupResult(
        is_duplicate=False,
        duplicate_cluster_id=None,
        matched_job_posting_id=None,
        survivor_job_posting_id=None,
        stub=True,
    )

    applied = apply_fuzzy_dedup_result(session, CURRENT_ID, result)

    assert applied is False
    session.execute.assert_not_called()


def test_apply_fuzzy_dedup_result_rejects_invalid_duplicate_contract() -> None:
    session = MagicMock()
    result = FuzzyDedupResult(
        is_duplicate=True,
        duplicate_cluster_id=None,
        matched_job_posting_id=None,
        survivor_job_posting_id=None,
        stub=False,
    )

    with pytest.raises(ValueError, match="duplicate fuzzy dedup results must include duplicate_cluster_id"):
        apply_fuzzy_dedup_result(session, CURRENT_ID, result)
