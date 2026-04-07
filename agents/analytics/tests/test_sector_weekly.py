"""Unit tests for :mod:`agents.analytics.aggregators.sector_weekly`."""

from __future__ import annotations

from datetime import date, timezone
from unittest.mock import MagicMock

import pytest

from agents.analytics.aggregators.sector_weekly import compute_sector_summary_weekly


def _pg_session() -> MagicMock:
    session = MagicMock()
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    session.get_bind.return_value = bind
    return session


def test_compute_sector_summary_weekly_non_postgresql_raises() -> None:
    session = MagicMock()
    bind = MagicMock()
    bind.dialect.name = "sqlite"
    session.get_bind.return_value = bind
    with pytest.raises(NotImplementedError, match="PostgreSQL"):
        compute_sector_summary_weekly(session, date(2026, 1, 5))


def test_compute_sector_summary_weekly_maps_rows() -> None:
    session = _pg_session()
    ws = date(2026, 1, 5)
    mappings = MagicMock()
    mappings.all.return_value = [
        {
            "sector_label": "Software",
            "posting_count": 12,
            "employer_count": 5,
            "p50_salary": 110_000.0,
            "top_skills": ["python", "sql"],
        },
    ]
    select_result = MagicMock()
    select_result.mappings.return_value = mappings
    session.execute.side_effect = [MagicMock(), select_result]

    rows = compute_sector_summary_weekly(session, ws)

    assert len(rows) == 1
    r = rows[0]
    assert r.week_start == ws
    assert r.sector == "Software"
    assert r.posting_count == 12
    assert r.employer_count == 5
    assert r.avg_salary == 110_000.0
    assert r.top_skills == ["python", "sql"]
    assert r.computed_at.tzinfo == timezone.utc
    session.add_all.assert_called_once_with(rows)
    assert session.execute.call_count >= 1


def test_compute_sector_summary_weekly_null_p50() -> None:
    session = _pg_session()
    ws = date(2026, 2, 2)
    mappings = MagicMock()
    mappings.all.return_value = [
        {
            "sector_label": "Other",
            "posting_count": 8,
            "employer_count": 3,
            "p50_salary": None,
            "top_skills": [],
        },
    ]
    select_result = MagicMock()
    select_result.mappings.return_value = mappings
    session.execute.side_effect = [MagicMock(), select_result]

    rows = compute_sector_summary_weekly(session, ws)

    assert rows[0].avg_salary is None
    assert rows[0].top_skills == []
