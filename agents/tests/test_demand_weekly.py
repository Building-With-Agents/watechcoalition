"""Tests for weekly skill/tool demand aggregate refresh (Analytics steps 2–3)."""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import DateTime, create_engine, func, literal, select

from agents.analytics.aggregators import demand_weekly as dw


def test_refresh_skill_demand_weekly_delete_then_insert() -> None:
    session = MagicMock()
    session.execute = MagicMock(
        side_effect=[
            MagicMock(rowcount=0),
            MagicMock(rowcount=3),
        ]
    )
    with patch.object(dw, "get_spam_thresholds", return_value=(0.7, 0.9)):
        n = dw.refresh_skill_demand_weekly(session, date(2025, 1, 6))
    assert n == 3
    assert session.execute.call_count == 2


def test_refresh_tool_demand_weekly_delete_then_insert() -> None:
    session = MagicMock()
    session.execute = MagicMock(
        side_effect=[
            MagicMock(rowcount=0),
            MagicMock(rowcount=2),
        ]
    )
    with patch.object(dw, "get_spam_thresholds", return_value=(0.7, 0.9)):
        n = dw.refresh_tool_demand_weekly(session, date(2025, 1, 6))
    assert n == 2
    assert session.execute.call_count == 2


def test_skill_agg_select_compiles_postgres() -> None:
    """Outer aggregation compiles (bind params on execute)."""
    engine = create_engine("postgresql+psycopg2://")
    computed_at = datetime(2025, 1, 6, 12, 0, 0, tzinfo=timezone.utc)
    expanded = dw._SKILLS_EXPANDED.subquery("exp_skills")

    agg = (
        select(
            expanded.c.skill_label,
            func.max(expanded.c.esco_uri).label("esco_uri"),
            expanded.c.week_start,
            func.count(func.distinct(expanded.c.job_posting_id)).label("posting_count"),
            func.count(func.distinct(expanded.c.company_id)).label("employer_count"),
            literal(computed_at, type_=DateTime(timezone=True)).label("computed_at"),
        )
        .select_from(expanded)
        .group_by(expanded.c.week_start, expanded.c.skill_label)
    )
    sql = str(agg.compile(engine, compile_kwargs={"literal_binds": False}))
    assert "exp_skills" in sql
    assert "GROUP BY" in sql.upper()


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_refresh_skill_runs_against_db() -> None:
    from dotenv import load_dotenv
    from sqlalchemy.orm import Session

    load_dotenv()
    from agents.common.data_store.database import get_engine

    with Session(get_engine()) as session:
        n = dw.refresh_skill_demand_weekly(session, date(2025, 1, 6))
        session.commit()
    assert n >= 0
