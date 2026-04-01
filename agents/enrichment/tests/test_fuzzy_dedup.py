"""Unit tests for fuzzy dedup (mocked DB + embeddings)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from agents.enrichment.dedup.fuzzy_dedup import run_fuzzy_dedup


def _unit_vec_xy(t: float, dim: int = 1536) -> list[float]:
    """Unit vector in R^dim with dot(e1, v) = t (first coordinate t after normalization)."""
    t = max(-1.0, min(1.0, t))
    s = (1.0 - t * t) ** 0.5
    return [t, s] + [0.0] * (dim - 2)


def _emb_json(t: float) -> str:
    return json.dumps(_unit_vec_xy(t))


def _exec_first(row: dict | None) -> MagicMock:
    m = MagicMock()
    m.mappings.return_value.first.return_value = row
    return m


def _exec_all(rows: list) -> MagicMock:
    m = MagicMock()
    m.mappings.return_value.all.return_value = rows
    return m


def _base_current_row(
    *,
    jid: str = "00000000-0000-0000-0000-000000000001",
    cid: str = "00000000-0000-0000-0000-0000000000cc",
    anchor: datetime | None = None,
    dedup_hash: str | None = None,
    dedup_emb: str | None = None,
    salary: str | None = None,
    requirements: str | None = None,
) -> dict:
    if anchor is None:
        anchor = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    return {
        "job_posting_id": jid,
        "company_id": cid,
        "publish_date": anchor,
        "job_title": "Engineer",
        "job_description": requirements or "Build systems " * 50,
        "salary_range": salary,
        "location": "WA",
        "zip": None,
        "county": None,
        "source": "jsearch",
        "external_id": "ext-1",
        "is_duplicate": False,
        "duplicate_cluster_id": None,
        "dedup_text_hash": dedup_hash,
        "dedup_embedding_text": dedup_emb,
        "company_name": "Acme",
        "requirements": requirements,
    }


@patch("agents.enrichment.dedup.fuzzy_dedup._embed_texts_azure", return_value=None)
def test_embedding_none_returns_unique(mock_embed: MagicMock) -> None:
    session = MagicMock()
    cur = _base_current_row(dedup_hash=None, dedup_emb=None)
    session.execute.side_effect = [_exec_first(cur)]

    out = run_fuzzy_dedup(session, cur["job_posting_id"])

    assert out.stub is False
    assert out.is_duplicate is False
    assert out.duplicate_cluster_id is None
    mock_embed.assert_called_once()


@patch("agents.enrichment.dedup.fuzzy_dedup._embed_texts_azure")
def test_hash_skip_avoids_embed_call(mock_embed: MagicMock) -> None:
    from agents.enrichment.dedup.text import build_dedup_text, dedup_text_hash, row_requirements_fallback

    session = MagicMock()
    cur = _base_current_row(requirements="alpha beta")
    body = row_requirements_fallback(cur)
    plain = build_dedup_text(cur["job_title"], cur["company_name"], body)
    h = dedup_text_hash(plain)
    cur["dedup_text_hash"] = h
    cur["dedup_embedding_text"] = _emb_json(1.0)

    session.execute.side_effect = [
        _exec_first(cur),
        _exec_all([]),
    ]

    out = run_fuzzy_dedup(session, cur["job_posting_id"])

    assert out.stub is False
    mock_embed.assert_not_called()
    assert session.execute.call_count == 2


@patch("agents.enrichment.dedup.fuzzy_dedup._embed_texts_azure")
def test_unique_when_no_survivors(mock_embed: MagicMock) -> None:
    session = MagicMock()
    cur = _base_current_row(dedup_hash=None, dedup_emb=None)
    mock_embed.return_value = [_unit_vec_xy(1.0)]

    session.execute.side_effect = [
        _exec_first(cur),
        MagicMock(),
        _exec_all([]),
    ]

    out = run_fuzzy_dedup(session, cur["job_posting_id"], threshold=0.5)

    assert out.stub is False
    assert out.is_duplicate is False
    assert out.duplicate_cluster_id is None


@patch("agents.enrichment.dedup.fuzzy_dedup._embed_texts_azure")
def test_list_survivors_filters_by_company_id_param(mock_embed: MagicMock) -> None:
    session = MagicMock()
    cid = "00000000-0000-0000-0000-0000000000dd"
    cur = _base_current_row(dedup_hash=None, dedup_emb=None, cid=cid)
    mock_embed.return_value = [_unit_vec_xy(1.0)]

    session.execute.side_effect = [
        _exec_first(cur),
        MagicMock(),
        _exec_all([]),
    ]

    run_fuzzy_dedup(session, cur["job_posting_id"])

    assert session.execute.call_count == 3
    _sql_load, p0 = session.execute.call_args_list[0][0]
    _sql_surv, p_surv = session.execute.call_args_list[2][0]
    assert p_surv["company_id"] == cid


@patch("agents.enrichment.dedup.fuzzy_dedup._embed_texts_azure")
def test_threshold_below_returns_unique(mock_embed: MagicMock) -> None:
    session = MagicMock()
    cur = _base_current_row(dedup_hash=None, dedup_emb=None)
    mock_embed.return_value = [_unit_vec_xy(1.0)]
    anchor = cur["publish_date"]
    assert isinstance(anchor, datetime)
    survivor = {
        "job_posting_id": "00000000-0000-0000-0000-000000000002",
        "duplicate_cluster_id": None,
        "dedup_embedding_text": _emb_json(0.5),
        "salary_range": None,
        "location": None,
        "zip": None,
        "county": None,
        "job_description": "",
        "publish_date": anchor - timedelta(days=5),
    }

    session.execute.side_effect = [
        _exec_first(cur),
        MagicMock(),
        _exec_all([survivor]),
    ]

    out = run_fuzzy_dedup(session, cur["job_posting_id"], threshold=0.92)

    assert out.stub is False
    assert out.is_duplicate is False
    assert out.duplicate_cluster_id is None


@patch("agents.enrichment.dedup.fuzzy_dedup._embed_texts_azure")
def test_threshold_above_marks_duplicate_when_survivor_wins(mock_embed: MagicMock) -> None:
    session = MagicMock()
    cur = _base_current_row(dedup_hash=None, dedup_emb=None, salary=None)
    mock_embed.return_value = [_unit_vec_xy(1.0)]
    anchor = cur["publish_date"]
    assert isinstance(anchor, datetime)
    cluster = "00000000-0000-0000-0000-00000000aa11"
    survivor = {
        "job_posting_id": "00000000-0000-0000-0000-000000000002",
        "duplicate_cluster_id": cluster,
        "dedup_embedding_text": _emb_json(1.0),
        "salary_range": "100k-120k",
        "location": "TX",
        "zip": None,
        "county": None,
        "job_description": "x" * 500,
        "publish_date": anchor - timedelta(days=5),
    }

    session.execute.side_effect = [
        _exec_first(cur),
        MagicMock(),
        _exec_all([survivor]),
    ]

    out = run_fuzzy_dedup(session, cur["job_posting_id"], threshold=0.99)

    assert out.stub is False
    assert out.is_duplicate is True
    assert out.duplicate_cluster_id == cluster
    assert out.survivor_job_posting_id == survivor["job_posting_id"]
    assert out.matched_job_posting_id == survivor["job_posting_id"]


@patch("agents.enrichment.dedup.fuzzy_dedup._embed_texts_azure")
def test_current_wins_completeness_flips_contract(mock_embed: MagicMock) -> None:
    session = MagicMock()
    cur = _base_current_row(dedup_hash=None, dedup_emb=None, salary="90k-100k")
    mock_embed.return_value = [_unit_vec_xy(1.0)]
    anchor = cur["publish_date"]
    assert isinstance(anchor, datetime)
    survivor = {
        "job_posting_id": "00000000-0000-0000-0000-000000000002",
        "duplicate_cluster_id": None,
        "dedup_embedding_text": _emb_json(1.0),
        "salary_range": None,
        "location": None,
        "zip": None,
        "county": None,
        "job_description": "",
        "publish_date": anchor - timedelta(days=5),
    }

    session.execute.side_effect = [
        _exec_first(cur),
        MagicMock(),
        _exec_all([survivor]),
    ]

    out = run_fuzzy_dedup(session, cur["job_posting_id"], threshold=0.99)

    assert out.stub is False
    assert out.is_duplicate is False
    assert out.survivor_job_posting_id == cur["job_posting_id"]
    assert out.matched_job_posting_id == survivor["job_posting_id"]
    assert out.duplicate_cluster_id is not None


@patch("agents.enrichment.dedup.fuzzy_dedup._embed_texts_azure")
def test_window_params_half_open(mock_embed: MagicMock) -> None:
    session = MagicMock()
    anchor = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    cur = _base_current_row(dedup_hash=None, dedup_emb=None, anchor=anchor)
    mock_embed.return_value = [_unit_vec_xy(1.0)]

    session.execute.side_effect = [
        _exec_first(cur),
        MagicMock(),
        _exec_all([]),
    ]

    run_fuzzy_dedup(session, cur["job_posting_id"])

    _s, params = session.execute.call_args_list[2][0]
    assert params["anchor"] == anchor
    assert params["window_start"] == anchor - timedelta(days=30)


def test_missing_company_returns_unique() -> None:
    session = MagicMock()
    cur = _base_current_row()
    cur["company_id"] = ""
    session.execute.side_effect = [_exec_first(cur)]

    out = run_fuzzy_dedup(session, cur["job_posting_id"])

    assert out.stub is False
    assert out.is_duplicate is False


def test_missing_row_returns_unique() -> None:
    session = MagicMock()
    session.execute.side_effect = [_exec_first(None)]

    out = run_fuzzy_dedup(session, "00000000-0000-0000-0000-000000000099")

    assert out.stub is False


@pytest.mark.parametrize("blank_id", ["", "   "])
def test_blank_job_posting_id_returns_unique(blank_id: str) -> None:
    session = MagicMock()
    out = run_fuzzy_dedup(session, blank_id)
    assert out.stub is False
    session.execute.assert_not_called()
