"""Unit tests for enrichment promotion helpers."""

from __future__ import annotations

import uuid
from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from agents.enrichment.dedup.types import FuzzyDedupResult
from agents.enrichment.job_postings_promotion import (
    apply_enrichment_to_job_postings,
    apply_fuzzy_dedup_result,
)

CURRENT_ID = "00000000-0000-0000-0000-000000000001"
MATCHED_ID = "00000000-0000-0000-0000-000000000002"
CLUSTER_ID = "00000000-0000-0000-0000-0000000000aa"


def _mapping_first(row: dict | None) -> MagicMock:
    m = MagicMock()
    m.mappings.return_value.first.return_value = row
    return m


def _mapping_all(rows: list[dict]) -> MagicMock:
    m = MagicMock()
    m.mappings.return_value.all.return_value = rows
    return m


def _execute_params(session: MagicMock) -> list[dict]:
    return [call.args[1] for call in session.execute.call_args_list]


def _update_execute_params(session: MagicMock) -> list[dict]:
    out: list[dict] = []
    for call in session.execute.call_args_list:
        params = call.args[1]
        if isinstance(params, dict) and "is_duplicate" in params:
            out.append(params)
    return out


def _execute_sql(session: MagicMock) -> list[str]:
    return [str(call.args[0]) for call in session.execute.call_args_list]


def _promotion_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "quality_score": 0.84,
        "quality_components": {"description": 0.9},
        "field_confidence": {"spam_score": 0.8},
        "overall_confidence": 0.82,
        "spam_tier": "clean",
        "spam_score": 0.25,
    }
    payload.update(overrides)
    return payload


def test_apply_fuzzy_dedup_result_clears_current_row_for_unique_posting() -> None:
    session = MagicMock()
    session.execute.side_effect = [
        _mapping_first({"is_duplicate": False, "duplicate_cluster_id": None}),
        MagicMock(),
    ]
    result = FuzzyDedupResult(
        is_duplicate=False,
        duplicate_cluster_id=None,
        matched_job_posting_id=None,
        survivor_job_posting_id=None,
        stub=False,
    )

    applied = apply_fuzzy_dedup_result(session, CURRENT_ID, result)

    assert applied is True
    assert session.execute.call_count == 2
    assert _update_execute_params(session) == [
        {
            "job_posting_id": CURRENT_ID,
            "is_duplicate": False,
            "duplicate_cluster_id": None,
        }
    ]
    assert "duplicate_cluster_id" in _execute_sql(session)[0]


def test_apply_fuzzy_dedup_result_clears_old_cluster_when_prior_survivor_becomes_unique() -> None:
    session = MagicMock()
    peer_id = "00000000-0000-0000-0000-000000000003"
    session.execute.side_effect = [
        _mapping_first({"is_duplicate": False, "duplicate_cluster_id": CLUSTER_ID}),
        MagicMock(),
        _mapping_all([{"job_posting_id": MATCHED_ID}, {"job_posting_id": peer_id}]),
        MagicMock(),
        MagicMock(),
    ]
    result = FuzzyDedupResult(
        is_duplicate=False,
        duplicate_cluster_id=None,
        matched_job_posting_id=None,
        survivor_job_posting_id=None,
        stub=False,
    )

    applied = apply_fuzzy_dedup_result(session, CURRENT_ID, result)

    assert applied is True
    assert _update_execute_params(session) == [
        {
            "job_posting_id": CURRENT_ID,
            "is_duplicate": False,
            "duplicate_cluster_id": None,
        },
        {
            "job_posting_id": MATCHED_ID,
            "is_duplicate": False,
            "duplicate_cluster_id": None,
        },
        {
            "job_posting_id": peer_id,
            "is_duplicate": False,
            "duplicate_cluster_id": None,
        },
    ]


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
    assert _update_execute_params(session) == [
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
    assert _update_execute_params(session) == [
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


@pytest.mark.parametrize(
    ("tier", "spam_score"),
    [
        ("clean", 0.25),
        ("flagged", 0.8),
        ("uncertain", None),
    ],
)
def test_apply_enrichment_to_job_postings_calls_dedup_for_non_rejected_tiers(
    tier: str,
    spam_score: float | None,
) -> None:
    session = MagicMock()
    dedup_result = FuzzyDedupResult(
        is_duplicate=False,
        duplicate_cluster_id=None,
        matched_job_posting_id=None,
        survivor_job_posting_id=None,
        stub=False,
    )

    with (
        patch(
            "agents.enrichment.job_postings_promotion.resolve_job_posting_row",
            return_value={"job_posting_id": CURRENT_ID, "company_id": MATCHED_ID},
        ),
        patch("agents.enrichment.job_postings_promotion.run_fuzzy_dedup", return_value=dedup_result) as mock_run,
        patch("agents.enrichment.job_postings_promotion.apply_fuzzy_dedup_result", return_value=True) as mock_apply,
    ):
        applied = apply_enrichment_to_job_postings(
            session,
            normalized_job_id=123,
            record_enriched_payload=_promotion_payload(spam_tier=tier, spam_score=spam_score),
        )

    assert applied is True
    mock_run.assert_called_once_with(session, CURRENT_ID)
    mock_apply.assert_called_once_with(session, CURRENT_ID, dedup_result)


def test_apply_enrichment_to_job_postings_skips_dedup_for_rejected_tier() -> None:
    session = MagicMock()

    with (
        patch(
            "agents.enrichment.job_postings_promotion.resolve_job_posting_row",
            return_value={"job_posting_id": CURRENT_ID, "company_id": MATCHED_ID},
        ),
        patch("agents.enrichment.job_postings_promotion.run_fuzzy_dedup") as mock_run,
    ):
        applied = apply_enrichment_to_job_postings(
            session,
            normalized_job_id=123,
            record_enriched_payload=_promotion_payload(spam_tier="rejected", spam_score=0.95),
        )

    assert applied is False
    mock_run.assert_not_called()


def test_apply_enrichment_to_job_postings_logs_and_continues_on_dedup_failure() -> None:
    session = MagicMock()
    session.begin_nested.return_value = nullcontext()

    with (
        patch(
            "agents.enrichment.job_postings_promotion.resolve_job_posting_row",
            return_value={"job_posting_id": CURRENT_ID, "company_id": MATCHED_ID},
        ),
        patch("agents.enrichment.job_postings_promotion.run_fuzzy_dedup", side_effect=RuntimeError("boom")),
    ):
        applied = apply_enrichment_to_job_postings(
            session,
            normalized_job_id=123,
            record_enriched_payload=_promotion_payload(),
        )

    assert applied is True
    session.begin_nested.assert_called_once_with()
    assert session.execute.call_count == 1


def _apply_with_resolved_row_for_temporal_borderplex(resolved_row: dict[str, object]) -> tuple[bool, MagicMock]:
    """Promotion UPDATE + patched fuzzy dedup (no extra SQL from dedup path)."""
    session = MagicMock()
    session.begin_nested.return_value = nullcontext()
    resolve_result = MagicMock()
    resolve_result.mappings.return_value.first.return_value = resolved_row
    update_result = MagicMock()
    session.execute.side_effect = [resolve_result, update_result]
    dedup_result = FuzzyDedupResult(
        is_duplicate=False,
        duplicate_cluster_id=None,
        matched_job_posting_id=None,
        survivor_job_posting_id=None,
        stub=False,
    )
    with (
        patch("agents.enrichment.job_postings_promotion.run_fuzzy_dedup", return_value=dedup_result),
        patch("agents.enrichment.job_postings_promotion.apply_fuzzy_dedup_result", return_value=True),
    ):
        out = apply_enrichment_to_job_postings(
            session,
            42,
            {
                "spam_tier": "clean",
                "spam_score": 0.2,
                "quality_score": 0.85,
            },
        )
    return out, session


def test_apply_enrichment_binds_temporal_period_from_date_posted() -> None:
    out, session = _apply_with_resolved_row_for_temporal_borderplex(
        {
            "job_posting_id": "11111111-1111-1111-1111-111111111111",
            "company_id": "22222222-2222-2222-2222-222222222222",
            "date_posted": datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        }
    )

    assert out is True
    assert session.execute.call_count == 2
    _stmt, params = session.execute.call_args_list[1][0]
    assert params["temporal_period"] == "post_gpt4"
    assert "occupation_code" in params
    assert params["occupation_code"] is None
    assert params["naics_code"] == "unknown"


def test_apply_enrichment_binds_temporal_period_at_exact_boundary_date() -> None:
    out, session = _apply_with_resolved_row_for_temporal_borderplex(
        {
            "job_posting_id": "11111111-1111-1111-1111-111111111111",
            "company_id": "22222222-2222-2222-2222-222222222222",
            "date_posted": datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        }
    )

    assert out is True
    _stmt, params = session.execute.call_args_list[1][0]
    assert params["temporal_period"] == "agentic_era"


def test_apply_enrichment_binds_temporal_period_none_when_date_missing() -> None:
    out, session = _apply_with_resolved_row_for_temporal_borderplex(
        {
            "job_posting_id": "11111111-1111-1111-1111-111111111111",
            "company_id": "22222222-2222-2222-2222-222222222222",
            "date_posted": None,
        }
    )

    assert out is True
    _stmt, params = session.execute.call_args_list[1][0]
    assert params["temporal_period"] is None


def test_apply_enrichment_binds_borderplex_subregion_from_normalized_location() -> None:
    out, session = _apply_with_resolved_row_for_temporal_borderplex(
        {
            "job_posting_id": "11111111-1111-1111-1111-111111111111",
            "company_id": "22222222-2222-2222-2222-222222222222",
            "date_posted": datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            "city": "El Paso",
            "state_province": "Texas",
            "country": "United States",
            "is_remote": False,
            "work_arrangement": "on-site",
        }
    )

    assert out is True
    assert session.execute.call_count == 2
    _stmt, params = session.execute.call_args_list[1][0]
    assert params["borderplex_subregion"] == "el_paso"


def test_apply_enrichment_binds_borderplex_subregion_for_las_cruces() -> None:
    out, session = _apply_with_resolved_row_for_temporal_borderplex(
        {
            "job_posting_id": "11111111-1111-1111-1111-111111111111",
            "company_id": "22222222-2222-2222-2222-222222222222",
            "date_posted": datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            "city": "Las Cruces",
            "state_province": "New Mexico",
            "country": "United States",
            "is_remote": False,
            "work_arrangement": "on-site",
        }
    )

    assert out is True
    _stmt, params = session.execute.call_args_list[1][0]
    assert params["borderplex_subregion"] == "las_cruces"


def test_apply_enrichment_binds_occupation_code_from_soc_code() -> None:
    session = MagicMock()
    resolve_result = MagicMock()
    resolve_result.mappings.return_value.first.return_value = {
        "job_posting_id": "11111111-1111-1111-1111-111111111111",
        "company_id": "22222222-2222-2222-2222-222222222222",
        "date_posted": datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    }
    update_result = MagicMock()
    session.execute.side_effect = [resolve_result, update_result]

    out = apply_enrichment_to_job_postings(
        session,
        42,
        {
            "spam_tier": "clean",
            "spam_score": 0.2,
            "quality_score": 0.85,
            "soc_code": "17-3029",
            "naics_code": "541512",
        },
    )
    assert out is True
    _stmt, params = session.execute.call_args_list[1][0]
    assert params["occupation_code"] == "17-3029"
    assert params["naics_code"] == "541512"


def test_apply_enrichment_binds_borderplex_subregion_regional_for_remote_job() -> None:
    out, session = _apply_with_resolved_row_for_temporal_borderplex(
        {
            "job_posting_id": "11111111-1111-1111-1111-111111111111",
            "company_id": "22222222-2222-2222-2222-222222222222",
            "date_posted": datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            "city": None,
            "state_province": "Texas",
            "country": "United States",
            "is_remote": True,
            "work_arrangement": "Remote",
        }
    )

    assert out is True
    _stmt, params = session.execute.call_args_list[1][0]
    assert params["borderplex_subregion"] == "regional"


def test_apply_enrichment_selects_employer_profile_id_when_metadata_present() -> None:
    ep_id = uuid.uuid4()
    session = MagicMock()
    resolve_result = MagicMock()
    resolve_result.mappings.return_value.first.return_value = {
        "job_posting_id": "11111111-1111-1111-1111-111111111111",
        "company_id": "22222222-2222-2222-2222-222222222222",
        "date_posted": datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
    }
    select_scalar = MagicMock()
    select_scalar.scalar_one_or_none.return_value = ep_id
    update_result = MagicMock()
    session.execute.side_effect = [
        resolve_result,
        select_scalar,
        update_result,
        *[MagicMock() for _ in range(10)],
    ]

    out = apply_enrichment_to_job_postings(
        session,
        42,
        {
            "spam_tier": "clean",
            "spam_score": 0.2,
            "quality_score": 0.85,
            "employer_metadata": {"company_size": "smb", "is_known_employer": True},
        },
    )

    assert out is True
    # Index 2: main promotion UPDATE (after resolve + employer_profile id lookup).
    _stmt, params = session.execute.call_args_list[2][0]
    assert params["employer_profile_id"] == ep_id
