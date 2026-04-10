"""Unit tests for posting freshness row shaping and DB persistence guards."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from agents.analytics.insights.posting_freshness_store import (
    build_posting_freshness_row_dicts,
    persist_posting_freshness_rows,
)

UTC = timezone.utc


def test_build_rows_uses_first_and_last_seen() -> None:
    computed_at = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
    rows = build_posting_freshness_row_dicts(
        [
            {
                "posting_id": "a",
                "first_seen": "2026-01-01T00:00:00Z",
                "last_seen": "2026-01-10T00:00:00Z",
                "days_since_posted": 99,
            }
        ],
        computed_at,
    )
    assert len(rows) == 1
    assert rows[0]["posting_id"] == "a"
    assert rows[0]["duration_days"] == 9


def test_build_rows_fallback_days_and_computed_at_window() -> None:
    computed_at = datetime(2026, 3, 15, 0, 0, 0, tzinfo=UTC)
    rows = build_posting_freshness_row_dicts(
        [{"posting_id": "b", "days_since_posted": 3}],
        computed_at,
    )
    assert rows[0]["duration_days"] == 3
    assert rows[0]["last_seen"] == computed_at
    assert rows[0]["first_seen"] == computed_at - timedelta(days=3)


def test_build_rows_repost_defaults_count() -> None:
    computed_at = datetime(2026, 1, 1, tzinfo=UTC)
    rows = build_posting_freshness_row_dicts(
        [{"posting_id": "c", "days_since_posted": 0, "is_repost": True}],
        computed_at,
    )
    assert rows[0]["is_repost"] is True
    assert rows[0]["repost_count"] == 1


def test_build_rows_fill_proxy_stub_heuristic() -> None:
    computed_at = datetime(2026, 1, 1, tzinfo=UTC)
    rows = build_posting_freshness_row_dicts(
        [{"posting_id": "d", "days_since_posted": 0, "stub": True}],
        computed_at,
    )
    assert rows[0]["fill_proxy"] is True


def test_persist_skips_when_env_url_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
    persist_posting_freshness_rows(
        [
            {
                "posting_id": "x",
                "first_seen": datetime.now(UTC),
                "last_seen": datetime.now(UTC),
                "duration_days": 0,
                "is_repost": False,
                "repost_count": 0,
                "fill_proxy": False,
                "computed_at": datetime.now(UTC),
            }
        ]
    )


def test_persist_skips_when_db_unreachable() -> None:
    row = {
        "posting_id": "y",
        "first_seen": datetime.now(UTC),
        "last_seen": datetime.now(UTC),
        "duration_days": 0,
        "is_repost": False,
        "repost_count": 0,
        "fill_proxy": False,
        "computed_at": datetime.now(UTC),
    }
    with (
        patch.dict("os.environ", {"PYTHON_DATABASE_URL": "postgresql+psycopg2://x"}),
        patch("agents.common.data_store.database.check_db_connection", return_value=False),
    ):
        persist_posting_freshness_rows([row])


def test_persist_merge_on_mock_session() -> None:
    row = {
        "posting_id": "z",
        "first_seen": datetime.now(UTC),
        "last_seen": datetime.now(UTC),
        "duration_days": 1,
        "is_repost": True,
        "repost_count": 1,
        "fill_proxy": False,
        "computed_at": datetime.now(UTC),
    }
    mock_session = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=mock_session)
    ctx.__exit__ = MagicMock(return_value=False)
    with (
        patch.dict("os.environ", {"PYTHON_DATABASE_URL": "postgresql+psycopg2://x"}),
        patch("agents.common.data_store.database.check_db_connection", return_value=True),
        patch("agents.common.data_store.database.session_scope", return_value=ctx),
    ):
        persist_posting_freshness_rows([row])
    mock_session.merge.assert_called_once()


def test_persist_failure_logs_only() -> None:
    row = {
        "posting_id": "err",
        "first_seen": datetime.now(UTC),
        "last_seen": datetime.now(UTC),
        "duration_days": 0,
        "is_repost": False,
        "repost_count": 0,
        "fill_proxy": False,
        "computed_at": datetime.now(UTC),
    }

    def _boom() -> None:
        raise RuntimeError("db down")

    ctx = MagicMock()
    ctx.__enter__ = MagicMock(side_effect=_boom)
    ctx.__exit__ = MagicMock(return_value=False)
    with (
        patch.dict("os.environ", {"PYTHON_DATABASE_URL": "postgresql+psycopg2://x"}),
        patch("agents.common.data_store.database.check_db_connection", return_value=True),
        patch("agents.common.data_store.database.session_scope", return_value=ctx),
    ):
        persist_posting_freshness_rows([row])  # does not raise
