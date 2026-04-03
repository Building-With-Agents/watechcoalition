"""Full-table SQL aggregates for Batch Insights (not limited to newest N rows).

Charts and counts reflect the entire ``normalized_jobs`` or ``raw_ingested_jobs``
table (whichever is used for the main view), so distributions stay accurate as
data grows. The recent-records table remains a small LIMIT sample.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from agents.dashboard.readonly_engine import get_dashboard_engine


def _norm_count(engine: Any) -> int:
    q = "SELECT COUNT(*)::bigint AS c FROM dbo.normalized_jobs"
    return int(pd.read_sql(q, engine).iloc[0]["c"])


@st.cache_data(ttl=300, show_spinner=False)
def fetch_batch_insights_bundle() -> dict[str, Any]:
    """Run aggregate queries; returns dict of DataFrames and scalars for Batch Insights."""
    engine = get_dashboard_engine()
    use_norm = _norm_count(engine) > 0
    table = "dbo.normalized_jobs" if use_norm else "dbo.raw_ingested_jobs"
    state_col = "state_province" if use_norm else "state"

    out: dict[str, Any] = {
        "use_normalized": use_norm,
        "table": table,
        "state_col": state_col,
    }

    total = pd.read_sql(f"SELECT COUNT(*)::bigint AS c FROM {table}", engine).iloc[0]["c"]
    out["total_rows"] = int(total)

    out["source_df"] = pd.read_sql(
        f"""
        SELECT source AS category, COUNT(*)::bigint AS cnt
        FROM {table}
        GROUP BY source
        ORDER BY cnt DESC
        """,
        engine,
    )

    out["state_df"] = pd.read_sql(
        f"""
        SELECT {state_col} AS category, COUNT(*)::bigint AS cnt
        FROM {table}
        WHERE {state_col} IS NOT NULL AND BTRIM({state_col}::text) <> ''
        GROUP BY {state_col}
        ORDER BY cnt DESC
        LIMIT 15
        """,
        engine,
    )

    out["city_df"] = pd.read_sql(
        f"""
        SELECT city AS category, COUNT(*)::bigint AS cnt
        FROM {table}
        WHERE city IS NOT NULL AND BTRIM(city::text) <> ''
        GROUP BY city
        ORDER BY cnt DESC
        LIMIT 15
        """,
        engine,
    )

    remote_case = """
        CASE
            WHEN is_remote IS TRUE THEN 'Remote'
            WHEN is_remote IS FALSE THEN 'On-site'
            ELSE 'Unknown'
        END
    """
    out["remote_df"] = pd.read_sql(
        f"""
        SELECT {remote_case} AS category, COUNT(*)::bigint AS cnt
        FROM {table}
        GROUP BY {remote_case}
        ORDER BY cnt DESC
        """,
        engine,
    )

    out["employment_df"] = pd.read_sql(
        f"""
        SELECT employment_type AS category, COUNT(*)::bigint AS cnt
        FROM {table}
        WHERE employment_type IS NOT NULL AND BTRIM(employment_type::text) <> ''
        GROUP BY employment_type
        ORDER BY cnt DESC
        """,
        engine,
    )

    out["experience_df"] = pd.read_sql(
        f"""
        SELECT experience_level AS category, COUNT(*)::bigint AS cnt
        FROM {table}
        WHERE experience_level IS NOT NULL AND BTRIM(experience_level::text) <> ''
        GROUP BY experience_level
        ORDER BY cnt DESC
        """,
        engine,
    )

    sal_count_row = pd.read_sql(
        f"""
        SELECT COUNT(*) FILTER (
            WHERE salary_min IS NOT NULL
               OR salary_max IS NOT NULL
               OR (salary_raw IS NOT NULL AND BTRIM(salary_raw::text) <> '')
        )::bigint AS rows_with_salary
        FROM {table}
        """,
        engine,
    ).iloc[0]
    out["salary_rows"] = int(sal_count_row["rows_with_salary"])

    med_min_row = pd.read_sql(
        f"""
        SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY salary_min) AS median_min
        FROM {table}
        WHERE salary_min IS NOT NULL
        """,
        engine,
    )
    med_max_row = pd.read_sql(
        f"""
        SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY salary_max) AS median_max
        FROM {table}
        WHERE salary_max IS NOT NULL
        """,
        engine,
    )
    out["median_min"] = None if med_min_row.empty else med_min_row.iloc[0]["median_min"]
    out["median_max"] = None if med_max_row.empty else med_max_row.iloc[0]["median_max"]

    bounds = pd.read_sql(
        f"""
        SELECT MIN(salary_min) AS lo, MAX(salary_min) AS hi
        FROM {table}
        WHERE salary_min IS NOT NULL
        """,
        engine,
    ).iloc[0]
    lo, hi = bounds["lo"], bounds["hi"]
    if lo is not None and hi is not None and float(hi) > float(lo):
        flo, fhi = float(lo), float(hi)
        out["salary_hist_lo"] = flo
        out["salary_hist_hi"] = fhi
        out["salary_hist_df"] = pd.read_sql(
            f"""
            SELECT
                WIDTH_BUCKET(salary_min, %(lo)s, %(hi)s, 10) AS bin,
                (
                    %(lo)s
                    + (WIDTH_BUCKET(salary_min, %(lo)s, %(hi)s, 10) - 1)
                    * ((%(hi)s - %(lo)s) / 10.0)
                )::double precision AS bin_start,
                COUNT(*)::bigint AS cnt
            FROM {table}
            WHERE salary_min IS NOT NULL
            GROUP BY 1, 2
            ORDER BY 1
            """,
            engine,
            params={"lo": flo, "hi": fhi},
        )
    else:
        out["salary_hist_lo"] = None
        out["salary_hist_hi"] = None
        out["salary_hist_df"] = pd.DataFrame(columns=["bin", "bin_start", "cnt"])

    out["raw_status_df"] = pd.read_sql(
        """
        SELECT processing_status AS category, COUNT(*)::bigint AS cnt
        FROM dbo.raw_ingested_jobs
        GROUP BY processing_status
        ORDER BY cnt DESC
        """,
        engine,
    )

    recent_cols_norm = (
        "title, company, source, city, state_province, employment_type, experience_level"
    )
    recent_cols_raw = (
        "title, company, source, city, state AS state_province, employment_type, experience_level"
    )
    recent_sql = (
        f"""
        SELECT {recent_cols_norm}
        FROM dbo.normalized_jobs
        ORDER BY id DESC
        LIMIT 50
        """
        if use_norm
        else f"""
        SELECT {recent_cols_raw}
        FROM dbo.raw_ingested_jobs
        ORDER BY id DESC
        LIMIT 50
        """
    )
    out["recent_df"] = pd.read_sql(recent_sql, engine)

    return out


def series_from_category_count(df: pd.DataFrame) -> pd.Series:
    """Turn category/cnt SQL result into a Series for st.bar_chart (index = category)."""
    if df.empty or "category" not in df.columns or "cnt" not in df.columns:
        return pd.Series(dtype="int64")
    s = pd.Series(df["cnt"].values, index=df["category"].astype(str))
    return s.sort_values(ascending=False)


def series_from_salary_histogram(
    hist_df: pd.DataFrame,
    lo: float,
    hi: float,
    *,
    n_buckets: int = 10,
) -> pd.Series:
    """Build a count Series with human-readable salary range labels (for st.bar_chart)."""
    if hist_df.empty or "cnt" not in hist_df.columns or "bin" not in hist_df.columns:
        return pd.Series(dtype="int64")
    width = (hi - lo) / float(n_buckets)
    rows = hist_df.sort_values("bin")
    labels: list[str] = []
    counts: list[int] = []
    for _, r in rows.iterrows():
        wb = int(r["bin"])
        cnt = int(r["cnt"])
        start = (
            float(r["bin_start"])
            if "bin_start" in r and pd.notna(r["bin_start"])
            else lo + (wb - 1) * width
        )
        if wb < 1:
            lab = f"< ${lo:,.0f}"
        elif wb > n_buckets:
            lab = f"≥ ${start:,.0f}"
        else:
            end = start + width
            lab = f"${start:,.0f}–${end:,.0f}"
        labels.append(lab)
        counts.append(cnt)
    return pd.Series(counts, index=labels)
