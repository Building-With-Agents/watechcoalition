"""Unit tests for :mod:`agents.analytics.aggregators.sector_weekly`."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import MagicMock, call

import pytest

from agents.analytics.aggregators.sector_weekly import compute_sector_summary_weekly


def _pg_session() -> MagicMock:
    session = MagicMock()
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    session.get_bind.return_value = bind
    return session


def _make_select_result(rows: list[dict]) -> MagicMock:
    """Return a mock execute() result whose .mappings().all() yields *rows*."""
    mappings = MagicMock()
    mappings.all.return_value = rows
    result = MagicMock()
    result.mappings.return_value = mappings
    return result


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# New tests
# ---------------------------------------------------------------------------

def test_compute_sector_summary_weekly_empty_result() -> None:
    """No sectors met the 5-posting minimum — should return [] without crashing."""
    session = _pg_session()
    session.execute.side_effect = [MagicMock(), _make_select_result([])]

    rows = compute_sector_summary_weekly(session, date(2026, 3, 2))

    assert rows == []
    session.add_all.assert_called_once_with([])


def test_compute_sector_summary_weekly_multiple_sectors() -> None:
    """Three sectors returned → three ORM objects, one per sector."""
    session = _pg_session()
    db_rows = [
        {"sector_label": "Healthcare", "posting_count": 20, "employer_count": 8, "p50_salary": 90_000.0, "top_skills": ["nursing"]},
        {"sector_label": "Finance",    "posting_count": 15, "employer_count": 6, "p50_salary": 120_000.0, "top_skills": ["excel", "python"]},
        {"sector_label": "Retail",     "posting_count": 7,  "employer_count": 4, "p50_salary": 45_000.0, "top_skills": []},
    ]
    session.execute.side_effect = [MagicMock(), _make_select_result(db_rows)]

    rows = compute_sector_summary_weekly(session, date(2026, 3, 9))

    assert len(rows) == 3
    labels = [r.sector for r in rows]
    assert "Healthcare" in labels
    assert "Finance" in labels
    assert "Retail" in labels
    session.add_all.assert_called_once_with(rows)


def test_compute_sector_summary_weekly_delete_before_insert() -> None:
    """DELETE for the target week must be the *first* execute() call (idempotent refresh)."""
    from sqlalchemy.sql.dml import Delete

    session = _pg_session()
    session.execute.side_effect = [MagicMock(), _make_select_result([])]

    ws = date(2026, 4, 7)
    compute_sector_summary_weekly(session, ws)

    first_call_arg = session.execute.call_args_list[0][0][0]
    assert isinstance(first_call_arg, Delete), (
        "First execute() call must be the DELETE statement, not the SELECT"
    )


def test_compute_sector_summary_weekly_week_boundary_params() -> None:
    """SQL params must span exactly 7 days and be UTC-aware datetimes."""
    session = _pg_session()
    session.execute.side_effect = [MagicMock(), _make_select_result([])]

    ws = date(2026, 1, 12)
    compute_sector_summary_weekly(session, ws)

    # Second execute() is the big SELECT; its params dict holds the window.
    select_call = session.execute.call_args_list[1]
    params = select_call[0][1]  # positional second arg

    expected_start = datetime.combine(ws, time.min, tzinfo=timezone.utc)
    expected_end = datetime.combine(ws + timedelta(days=7), time.min, tzinfo=timezone.utc)

    assert params["week_start_ts"] == expected_start
    assert params["week_end_ts"] == expected_end
    assert (params["week_end_ts"] - params["week_start_ts"]).days == 7


def test_compute_sector_summary_weekly_unknown_sector_fallback() -> None:
    """Null/blank sector_label is coalesced to 'Unknown' by the SQL; ORM must preserve that string."""
    session = _pg_session()
    db_rows = [
        {"sector_label": "Unknown", "posting_count": 6, "employer_count": 2, "p50_salary": None, "top_skills": []},
    ]
    session.execute.side_effect = [MagicMock(), _make_select_result(db_rows)]

    rows = compute_sector_summary_weekly(session, date(2026, 2, 9))

    assert rows[0].sector == "Unknown"


def test_compute_sector_summary_weekly_null_top_skills() -> None:
    """If the DB driver returns None for top_skills, the ORM object gets an empty list."""
    session = _pg_session()
    db_rows = [
        {"sector_label": "Logistics", "posting_count": 9, "employer_count": 3, "p50_salary": 60_000.0, "top_skills": None},
    ]
    session.execute.side_effect = [MagicMock(), _make_select_result(db_rows)]

    rows = compute_sector_summary_weekly(session, date(2026, 2, 16))

    assert rows[0].top_skills == []


def test_compute_sector_summary_weekly_top_skills_iterable() -> None:
    """top_skills as a non-list iterable (e.g. tuple) is still flattened to a plain list."""
    session = _pg_session()
    db_rows = [
        {"sector_label": "Energy", "posting_count": 11, "employer_count": 5, "p50_salary": 95_000.0, "top_skills": ("python", "sql", "spark")},
    ]
    session.execute.side_effect = [MagicMock(), _make_select_result(db_rows)]

    rows = compute_sector_summary_weekly(session, date(2026, 2, 23))

    assert isinstance(rows[0].top_skills, list)
    assert rows[0].top_skills == ["python", "sql", "spark"]


def test_compute_sector_summary_weekly_none_bind_raises() -> None:
    """session.get_bind() returns None (misconfigured session) → NotImplementedError."""
    session = MagicMock()
    session.get_bind.return_value = None

    with pytest.raises(NotImplementedError, match="PostgreSQL"):
        compute_sector_summary_weekly(session, date(2026, 3, 2))
