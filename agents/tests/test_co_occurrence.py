"""Tests for skill co-occurrence refresh (Analytics step 9)."""

from __future__ import annotations

import os
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, select

from agents.analytics.aggregators import co_occurrence as co
from agents.analytics.aggregators import demand_weekly as dw


def test_extract_cooccurrence_pairs_runbook_shape() -> None:
    posting_skills = [
        ["b", "a", "c"],
        ["a", "b"],
    ]
    out = co._extract_cooccurrence_pairs(posting_skills)
    assert out[("a", "b")] == 2
    assert out[("a", "c")] == 1
    assert out[("b", "c")] == 1


def test_extract_cooccurrence_pairs_top_200_cap() -> None:
    posting_skills = [[f"s{i}", f"s{i + 1}"] for i in range(0, 500, 2)]
    out = co._extract_cooccurrence_pairs(posting_skills)
    assert len(out) <= 200
    if out:
        assert max(out.values()) >= min(out.values())


def test_extract_cooccurrence_pairs_per_posting_cap_20() -> None:
    skills = [f"x{i}" for i in range(25)]
    out = co._extract_cooccurrence_pairs([skills])
    assert len(out) == 190


def test_refresh_skill_co_occurrence_delete_then_insert_mock() -> None:
    fake_rows = [("jp1", "A"), ("jp1", "B"), ("jp2", "A"), ("jp2", "B")]
    session = MagicMock()
    call_counter = {"n": 0}

    def exec_wrap(*args, **kwargs):
        call_counter["n"] += 1
        if call_counter["n"] == 1:
            m = MagicMock()
            m.all.return_value = fake_rows
            return m
        return MagicMock()

    session.execute.side_effect = exec_wrap

    with patch.object(co, "get_spam_thresholds", return_value=(0.7, 0.9)):
        n = co.refresh_skill_co_occurrence(session, date(2025, 1, 6))

    assert n >= 1
    assert session.execute.call_count == 3


def test_refresh_skill_co_occurrence_empty_deletes_only() -> None:
    session = MagicMock()
    call_counter = {"n": 0}

    def exec_wrap(*args, **kwargs):
        call_counter["n"] += 1
        if call_counter["n"] == 1:
            m = MagicMock()
            m.all.return_value = []
            return m
        return MagicMock()

    session.execute.side_effect = exec_wrap

    with patch.object(co, "get_spam_thresholds", return_value=(0.7, 0.9)):
        n = co.refresh_skill_co_occurrence(session, date(2025, 1, 6))

    assert n == 0
    assert session.execute.call_count == 2


def test_co_occurrence_select_compiles_postgres() -> None:
    engine = create_engine("postgresql+psycopg2://")
    expanded = dw._SKILLS_EXPANDED.subquery("exp_skills")
    stmt = select(expanded.c.job_posting_id, expanded.c.skill_label).select_from(expanded)
    compiled = str(stmt.compile(engine, compile_kwargs={"literal_binds": False}))
    assert "exp_skills" in compiled


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_refresh_skill_co_occurrence_db_smoke() -> None:
    from dotenv import load_dotenv
    from sqlalchemy.orm import Session

    load_dotenv()
    from agents.common.data_store.database import get_engine

    with Session(get_engine()) as session:
        n = co.refresh_skill_co_occurrence(session, date(2025, 1, 6))
        session.commit()
    assert n >= 0
    assert n <= co._TOP_PAIR_LIMIT
