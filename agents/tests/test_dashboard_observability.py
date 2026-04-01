"""Unit tests for Week 6 dashboard observability helpers (no Streamlit runtime)."""

from __future__ import annotations

import pandas as pd
import pytest

from agents.dashboard.observability_metrics import (
    compute_conformance_pct,
    compute_dedup_rate_pct,
    compute_error_rate_pct,
    compute_salary_coverage_pct,
)


class TestDedupRate:
    def test_basic_ratio(self) -> None:
        df = pd.DataFrame({"staged_count": [80, 20], "dedup_count": [20, 5]})
        # total staged+dedup = 125, dedup = 25 -> 20%
        assert compute_dedup_rate_pct(df) == pytest.approx(20.0)

    def test_empty(self) -> None:
        assert compute_dedup_rate_pct(pd.DataFrame()) is None

    def test_zero_denominator(self) -> None:
        df = pd.DataFrame({"staged_count": [0], "dedup_count": [0]})
        assert compute_dedup_rate_pct(df) is None


class TestErrorRate:
    def test_basic(self) -> None:
        df = pd.DataFrame({"total_fetched": [100, 50], "error_count": [2, 3]})
        assert compute_error_rate_pct(df) == pytest.approx(100.0 * 5 / 150)

    def test_empty(self) -> None:
        assert compute_error_rate_pct(pd.DataFrame()) is None


class TestConformance:
    def test_all_success(self) -> None:
        df = pd.DataFrame({"normalization_status": ["success", "success"]})
        assert compute_conformance_pct(df) == pytest.approx(100.0)

    def test_mixed(self) -> None:
        df = pd.DataFrame({"normalization_status": ["success", "failed", "success"]})
        assert compute_conformance_pct(df) == pytest.approx(100.0 * 2 / 3)


class TestSalaryCoverage:
    def test_structured_salary(self) -> None:
        df = pd.DataFrame(
            {
                "salary_min": [1.0, None],
                "salary_max": [None, None],
                "salary_raw": [None, None],
            }
        )
        assert compute_salary_coverage_pct(df) == pytest.approx(50.0)

    def test_raw_only(self) -> None:
        df = pd.DataFrame(
            {
                "salary_min": [None],
                "salary_max": [None],
                "salary_raw": ["80k"],
            }
        )
        assert compute_salary_coverage_pct(df) == pytest.approx(100.0)
