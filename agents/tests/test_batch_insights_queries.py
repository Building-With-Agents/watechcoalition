"""Unit tests for Batch Insights SQL helpers (no DB required)."""

from __future__ import annotations

import pandas as pd

from agents.dashboard.batch_insights_queries import (
    series_from_category_count,
    series_from_salary_histogram,
)


class TestSeriesFromCategoryCount:
    def test_builds_series_with_string_index(self) -> None:
        df = pd.DataFrame({"category": ["a", "b"], "cnt": [3, 1]})
        s = series_from_category_count(df)
        assert s["a"] == 3
        assert s["b"] == 1

    def test_empty_dataframe(self) -> None:
        df = pd.DataFrame(columns=["category", "cnt"])
        s = series_from_category_count(df)
        assert len(s) == 0


class TestSeriesFromSalaryHistogram:
    def test_labels_use_currency_ranges(self) -> None:
        hist = pd.DataFrame(
            {
                "bin": [1, 2],
                "bin_start": [0.0, 1_000.0],
                "cnt": [3, 7],
            }
        )
        s = series_from_salary_histogram(hist, 0.0, 10_000.0, n_buckets=10)
        assert len(s) == 2
        assert s.index.tolist()[0] == "$0–$1,000"
        assert s.index.tolist()[1] == "$1,000–$2,000"
        assert s.iloc[0] == 3
        assert s.iloc[1] == 7
