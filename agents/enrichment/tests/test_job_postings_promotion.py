"""Tests for enrichment ``job_postings`` promotion writes."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from agents.enrichment.job_postings_promotion import apply_enrichment_to_job_postings


def _apply_with_resolved_row(resolved_row: dict[str, object]) -> tuple[bool, MagicMock]:
    session = MagicMock()
    resolve_result = MagicMock()
    resolve_result.mappings.return_value.first.return_value = resolved_row
    update_result = MagicMock()
    session.execute.side_effect = [resolve_result, update_result]

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
    out, session = _apply_with_resolved_row(
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


def test_apply_enrichment_binds_temporal_period_at_exact_boundary_date() -> None:
    out, session = _apply_with_resolved_row(
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
    out, session = _apply_with_resolved_row(
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
    out, session = _apply_with_resolved_row(
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
    out, session = _apply_with_resolved_row(
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


def test_apply_enrichment_binds_borderplex_subregion_regional_for_remote_job() -> None:
    out, session = _apply_with_resolved_row(
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
