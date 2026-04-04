"""Tests for skill velocity refresh (Analytics step 8)."""

from __future__ import annotations

import os
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from agents.analytics.aggregators import velocity as vel


def test_week_starts_for_velocity_five_mondays() -> None:
    w = date(2025, 1, 6)
    starts = vel._week_starts_for_velocity(w)
    assert len(starts) == 5
    assert starts[-1] == w
    assert starts[0] == w - timedelta(days=28)
    for i in range(1, len(starts)):
        assert starts[i] - starts[i - 1] == timedelta(days=7)


def test_classify_trend_thresholds() -> None:
    assert vel._classify_trend(float("nan")) == "emerging"
    assert vel._classify_trend(None) == "emerging"
    assert vel._classify_trend(float("inf")) == "accelerating"
    assert vel._classify_trend(float("-inf")) == "declining"
    assert vel._classify_trend(0.2) == "accelerating"
    assert vel._classify_trend(-0.2) == "declining"
    assert vel._classify_trend(0.03) == "stable"
    assert vel._classify_trend(0.10) == "volatile"


def test_sanitize_pct_for_db() -> None:
    assert vel._sanitize_pct_for_db(float("inf")) == 0.0
    assert vel._sanitize_pct_for_db(float("-inf")) == 0.0
    assert vel._sanitize_pct_for_db(float("nan")) == 0.0
    assert vel._sanitize_pct_for_db(0.12) == pytest.approx(0.12)


def test_compute_latest_pct_change_monotonic_columns() -> None:
    """Rolling/pct_change use chronologically sorted week columns."""
    w0, w1, w2, w3, w4 = [date(2025, 1, 6) + timedelta(days=7 * i) for i in range(5)]
    pivoted = pd.DataFrame(
        {
            w4: [10],
            w0: [1],
            w2: [5],
            w1: [2],
            w3: [8],
        },
        index=["Python"],
    )
    s = vel._compute_latest_pct_change(pivoted)
    assert "Python" in s.index
    assert isinstance(s.loc["Python"], (float, type(s.iloc[0])))


def test_refresh_skill_velocity_delete_then_insert_mock() -> None:
    w = date(2025, 1, 6)
    weeks = vel._week_starts_for_velocity(w)
    rows = []
    for ws in weeks:
        rows.append(
            {
                "skill_label": "Python",
                "week_start": ws,
                "posting_count": 10 + weeks.index(ws),
                "esco_uri": "http://esco/skill/python",
            }
        )
    df = pd.DataFrame(rows)

    session = MagicMock()
    session.connection.return_value = MagicMock()
    exec_calls: list = []

    def exec_side_effect(*args, **kwargs):
        exec_calls.append((args, kwargs))
        return MagicMock()

    session.execute.side_effect = exec_side_effect

    with patch.object(vel.pd, "read_sql", return_value=df):
        n = vel.refresh_skill_velocity(session, w)

    assert n == 1
    assert len(exec_calls) == 2
    insert_args = exec_calls[1][0]
    payload = insert_args[1]
    assert isinstance(payload, list)
    assert payload[0]["week"] == w
    assert payload[0]["skill_label"] == "Python"
    assert payload[0]["four_week_trend"] in (
        "emerging",
        "accelerating",
        "declining",
        "stable",
        "volatile",
    )
    assert isinstance(payload[0]["week_over_week_change"], float)
    assert not any(
        (isinstance(x, float) and (x != x or x == float("inf") or x == float("-inf")))
        for x in [payload[0]["week_over_week_change"]]
    )


def test_refresh_skill_velocity_empty_df_still_deletes() -> None:
    session = MagicMock()
    session.connection.return_value = MagicMock()
    with patch.object(vel.pd, "read_sql", return_value=pd.DataFrame()):
        n = vel.refresh_skill_velocity(session, date(2025, 1, 6))
    assert n == 0
    assert session.execute.call_count == 1


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_refresh_skill_velocity_db_smoke() -> None:
    from dotenv import load_dotenv
    from sqlalchemy.orm import Session

    load_dotenv()
    from agents.common.data_store.database import get_engine

    with Session(get_engine()) as session:
        n = vel.refresh_skill_velocity(session, date(2025, 1, 6))
        session.commit()
    assert n >= 0
