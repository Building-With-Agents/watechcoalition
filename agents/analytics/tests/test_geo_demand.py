"""Unit tests for :mod:`agents.analytics.aggregators.geo_demand`."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from agents.analytics.aggregators.geo_demand import compute_geo_demand_weekly


def _pg_session() -> MagicMock:
    session = MagicMock()
    bind = MagicMock()
    bind.dialect.name = "postgresql"
    session.get_bind.return_value = bind
    return session


def test_compute_geo_demand_weekly_non_postgresql_raises() -> None:
    session = MagicMock()
    bind = MagicMock()
    bind.dialect.name = "sqlite"
    session.get_bind.return_value = bind
    with pytest.raises(NotImplementedError, match="PostgreSQL"):
        compute_geo_demand_weekly(session, date(2026, 1, 5))


def test_compute_geo_demand_weekly_returns_orm_rows() -> None:
    session = _pg_session()
    ws = date(2026, 1, 5)
    mappings = MagicMock()
    mappings.all.return_value = [
        {"region": "el_paso", "cnt": 42},
        {"region": "las_cruces", "cnt": 7},
    ]
    session.execute.return_value.mappings.return_value = mappings

    rows = compute_geo_demand_weekly(session, ws)

    assert len(rows) == 2
    assert rows[0].week_start == ws
    assert rows[0].borderplex_subregion == "el_paso"
    assert rows[0].posting_count == 42
    assert rows[1].borderplex_subregion == "las_cruces"
    assert rows[1].posting_count == 7
    session.execute.assert_called_once()
    bound = session.execute.call_args[0][1]
    assert bound["week_start_ts"].date() == ws
    assert bound["week_end_ts"].date() == date(2026, 1, 12)


def test_compute_geo_demand_weekly_empty() -> None:
    session = _pg_session()
    mappings = MagicMock()
    mappings.all.return_value = []
    session.execute.return_value.mappings.return_value = mappings

    rows = compute_geo_demand_weekly(session, date(2025, 12, 1))
    assert rows == []
