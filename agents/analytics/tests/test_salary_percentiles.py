"""Unit tests for :mod:`agents.analytics.aggregators.salary_percentiles`."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.analytics.aggregators.salary_percentiles import compute_salary_percentiles


def _pg_session() -> MagicMock:
    session = MagicMock()
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    session.get_bind.return_value = bind
    return session


def test_compute_salary_percentiles_invalid_group_col_raises() -> None:
    session = _pg_session()
    with pytest.raises(ValueError, match="group_col"):
        compute_salary_percentiles(session, "role_title", having_threshold=10)


def test_compute_salary_percentiles_non_postgresql_raises() -> None:
    session = MagicMock()
    bind = MagicMock()
    bind.dialect.name = "sqlite"
    session.get_bind.return_value = bind
    with pytest.raises(NotImplementedError, match="PostgreSQL"):
        compute_salary_percentiles(session, "soc_code")


def test_compute_salary_percentiles_maps_pg_rows() -> None:
    session = _pg_session()
    mappings = MagicMock()
    mappings.all.return_value = [
        {
            "grp": "15-1252",
            "row_count": 100,
            "p25": 90_000.0,
            "p50": 120_000.0,
            "p75": 140_000.0,
            "p95": 165_000.0,
        },
        {
            "grp": "el_paso",
            "row_count": 55,
            "p25": 50_000.0,
            "p50": 60_000.0,
            "p75": 70_000.0,
            "p95": 85_000.0,
        },
    ]
    result_mock = MagicMock()
    result_mock.mappings.return_value = mappings
    session.execute.return_value = result_mock

    out = compute_salary_percentiles(session, "borderplex_subregion", having_threshold=50)

    assert out["15-1252"] == {
        "p25": 90_000.0,
        "p50": 120_000.0,
        "p75": 140_000.0,
        "p95": 165_000.0,
    }
    assert out["el_paso"]["p50"] == 60_000.0
    session.execute.assert_called_once()
    args, kwargs = session.execute.call_args
    assert "percentile_disc(0.25)" in str(args[0])
    assert args[1]["having_threshold"] == 50
    assert not kwargs


def test_compute_salary_percentiles_empty_result() -> None:
    session = _pg_session()
    mappings = MagicMock()
    mappings.all.return_value = []
    result_mock = MagicMock()
    result_mock.mappings.return_value = mappings
    session.execute.return_value = result_mock

    out = compute_salary_percentiles(session, "naics_code", having_threshold=50)
    assert out == {}
