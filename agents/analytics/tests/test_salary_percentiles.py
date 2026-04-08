from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agents.analytics.aggregators.salary_percentiles import compute_salary_percentiles
from agents.analytics.canonical_roles.snapshots import refresh_role_snapshot_weekly


def test_compute_salary_percentiles_rejects_unknown_group_col() -> None:
    session = MagicMock()
    session.get_bind.return_value = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    with pytest.raises(ValueError, match="group_col must be one of"):
        compute_salary_percentiles(session, "unknown_group")


def test_compute_salary_percentiles_supports_canonical_role_id_and_week_filter() -> None:
    session = MagicMock()
    session.get_bind.return_value = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    execute_result = MagicMock()
    execute_result.mappings.return_value.all.return_value = [
        {"grp": "role-1", "p25": 90000, "p50": 100000, "p75": 110000, "p95": 130000},
    ]
    session.execute.return_value = execute_result

    week_start = date(2026, 4, 6)
    out = compute_salary_percentiles(
        session,
        "canonical_role_id",
        having_threshold=1,
        week_start=week_start,
    )

    assert out == {
        "role-1": {
            "p25": 90000.0,
            "p50": 100000.0,
            "p75": 110000.0,
            "p95": 130000.0,
        }
    }
    stmt = str(session.execute.call_args.args[0])
    params = session.execute.call_args.args[1]
    assert "jp.canonical_role_id" in stmt
    assert "DATE_TRUNC('week'" in stmt
    assert params["week_start"] == week_start


def test_refresh_role_snapshot_weekly_uses_shared_salary_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    week_start = date(2026, 4, 6)
    helper_calls: list[tuple[str, int, date]] = []

    def fake_compute_salary_percentiles(
        session: MagicMock,
        group_col: str,
        having_threshold: int = 50,
        *,
        week_start: date | None = None,
    ) -> dict[str, dict[str, float]]:
        helper_calls.append((group_col, having_threshold, week_start or date.min))
        return {
            "role-1": {
                "p25": 80000.0,
                "p50": 90000.0,
                "p75": 100000.0,
                "p95": 120000.0,
            }
        }

    monkeypatch.setattr(
        "agents.analytics.canonical_roles.snapshots.compute_salary_percentiles",
        fake_compute_salary_percentiles,
    )

    delete_result = MagicMock()
    rows_result = MagicMock()
    rows_result.mappings.return_value.all.return_value = [
        {
            "canonical_role_id": "role-1",
            "role_label": "Data Engineer",
            "top_skills": [{"skill_name": "Python", "count": 2}],
            "top_tools": [{"tool_name": "dbt", "count": 1}],
            "salary_min": 40.0,
            "salary_max": 50.0,
            "salary_period": "hourly",
        }
    ]

    session = MagicMock()
    session.execute.side_effect = [delete_result, rows_result]

    inserted = refresh_role_snapshot_weekly(session, week_start=week_start)

    assert inserted == 1
    assert helper_calls == [("canonical_role_id", 1, week_start)]
    added_row = session.add.call_args.args[0]
    assert added_row.salary_p25 == 80000.0
    assert added_row.salary_p50 == 90000.0
    assert added_row.salary_p75 == 100000.0
    assert added_row.salary_p95 == 120000.0
    assert added_row.median_salary == 90000.0
