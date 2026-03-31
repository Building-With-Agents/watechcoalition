"""Tests for enrichment ``job_postings`` promotion writes."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from agents.enrichment.job_postings_promotion import apply_enrichment_to_job_postings


def test_apply_enrichment_binds_temporal_period_from_date_posted() -> None:
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
        },
    )

    assert out is True
    assert session.execute.call_count == 2
    _stmt, params = session.execute.call_args_list[1][0]
    assert params["temporal_period"] == "post_gpt4"
