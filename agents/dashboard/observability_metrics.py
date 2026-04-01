"""Pure metric helpers for Week 6 observability pages (unit-testable, no Streamlit).

Dedup/error rates are used from ``observability_queries`` after loading runs into
DataFrames. Conformance and salary coverage are mirrored in SQL there; the
DataFrame versions here stay as the documented definition and test oracle.

DB failure / session fallback lives in ``observability_queries.resolve_*_obs`` (not
here) so it stays tied to Streamlit session state and does not duplicate
``@st.cache_data`` behavior.
"""

from __future__ import annotations

import pandas as pd


def compute_dedup_rate_pct(runs_df: pd.DataFrame) -> float | None:
    """Share of duplicates among all records considered for staging (dedup + staged).

    Formula: SUM(dedup_count) / NULLIF(SUM(staged_count + dedup_count), 0) → percentage.
    """
    if runs_df.empty or "dedup_count" not in runs_df.columns or "staged_count" not in runs_df.columns:
        return None
    staged = pd.to_numeric(runs_df["staged_count"], errors="coerce").fillna(0).sum()
    dedup = pd.to_numeric(runs_df["dedup_count"], errors="coerce").fillna(0).sum()
    denom = staged + dedup
    if denom <= 0:
        return None
    return float(dedup / denom * 100.0)


def compute_error_rate_pct(runs_df: pd.DataFrame) -> float | None:
    """Share of row-level ingestion errors vs rows fetched across runs."""
    if runs_df.empty or "error_count" not in runs_df.columns or "total_fetched" not in runs_df.columns:
        return None
    err = pd.to_numeric(runs_df["error_count"], errors="coerce").fillna(0).sum()
    fetched = pd.to_numeric(runs_df["total_fetched"], errors="coerce").fillna(0).sum()
    if fetched <= 0:
        return None
    return float(err / fetched * 100.0)


def compute_conformance_pct(normalized_jobs_df: pd.DataFrame) -> float | None:
    """Percentage of rows with normalization_status == 'success'.

    Must match the FILTER in ``_fetch_normalization_obs_cached`` (normalized_jobs).
    """
    if normalized_jobs_df.empty or "normalization_status" not in normalized_jobs_df.columns:
        return None
    total = len(normalized_jobs_df)
    if total == 0:
        return None
    ok = (normalized_jobs_df["normalization_status"].astype(str) == "success").sum()
    return float(ok / total * 100.0)


def compute_salary_coverage_pct(normalized_jobs_df: pd.DataFrame) -> float | None:
    """Share of rows with min/max salary or non-empty salary_raw.

    Must match the FILTER in ``_fetch_normalization_obs_cached`` (normalized_jobs).
    """
    if normalized_jobs_df.empty:
        return None
    df = normalized_jobs_df
    has_min = df["salary_min"].notna() if "salary_min" in df.columns else pd.Series(False, index=df.index)
    has_max = df["salary_max"].notna() if "salary_max" in df.columns else pd.Series(False, index=df.index)
    raw = df["salary_raw"] if "salary_raw" in df.columns else pd.Series([None] * len(df), index=df.index)
    raw_filled = raw.astype(str).str.strip().ne("") & raw.notna()
    mask = has_min | has_max | raw_filled
    total = len(df)
    if total == 0:
        return None
    return float(mask.sum() / total * 100.0)
