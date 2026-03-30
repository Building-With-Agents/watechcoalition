"""Cached database reads for Week 6 observability pages (TTL 5 minutes)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from agents.dashboard.observability_metrics import (
    compute_dedup_rate_pct,
    compute_error_rate_pct,
)
from agents.dashboard.readonly_engine import get_dashboard_engine

SESSION_KEY_INGESTION_GOOD = "_obs_last_good_ingestion"
SESSION_KEY_NORM_GOOD = "_obs_last_good_normalization"


@dataclass
class IngestionObsFetchResult:
    fetched_at: datetime
    ok: bool
    error: str | None
    daily_df: pd.DataFrame
    runs_all_df: pd.DataFrame
    recent_runs_df: pd.DataFrame
    dedup_rate_pct: float | None
    error_rate_pct: float | None


@dataclass
class NormalizationObsFetchResult:
    fetched_at: datetime
    ok: bool
    error: str | None
    normalized_row_count: int
    conformance_pct: float | None
    quarantine_df: pd.DataFrame
    salary_coverage_pct: float | None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_ingestion_obs_cached() -> IngestionObsFetchResult:
    """Load ingestion observability datasets.

    On DB errors, **raises** so Streamlit does not cache a failure blob (transient
    outages recover on the next rerun). Callers use ``resolve_ingestion_obs`` for
    session fallback.
    """
    ts = _utcnow()
    engine = get_dashboard_engine()
    daily_sql = """
        SELECT date_trunc('day', ingestion_timestamp AT TIME ZONE 'UTC')::date AS day,
               COUNT(*)::bigint AS record_count
        FROM dbo.raw_ingested_jobs
        GROUP BY 1
        ORDER BY 1 ASC
    """
    runs_sql = """
        SELECT run_id, region_id, source, started_at, completed_at,
               status, total_fetched, staged_count, dedup_count, error_count,
               error_message
        FROM dbo.job_ingestion_runs
        ORDER BY started_at DESC
    """
    recent_sql = """
        SELECT run_id, region_id, source, started_at, completed_at,
               status, total_fetched, staged_count, dedup_count, error_count,
               error_message
        FROM dbo.job_ingestion_runs
        ORDER BY started_at DESC
        LIMIT 10
    """
    daily_df = pd.read_sql(daily_sql, engine)
    runs_all_df = pd.read_sql(runs_sql, engine)
    recent_runs_df = pd.read_sql(recent_sql, engine)
    dedup = compute_dedup_rate_pct(runs_all_df)
    err = compute_error_rate_pct(runs_all_df)
    return IngestionObsFetchResult(
        fetched_at=ts,
        ok=True,
        error=None,
        daily_df=daily_df,
        runs_all_df=runs_all_df,
        recent_runs_df=recent_runs_df,
        dedup_rate_pct=dedup,
        error_rate_pct=err,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_normalization_obs_cached() -> NormalizationObsFetchResult:
    """Load normalization observability aggregates; raises on DB failure (see resolver)."""
    ts = _utcnow()
    engine = get_dashboard_engine()
    norm_agg_sql = """
        SELECT
            COUNT(*)::bigint AS total,
            COUNT(*) FILTER (WHERE normalization_status = 'success')::bigint AS success_count,
            COUNT(*) FILTER (
                WHERE salary_min IS NOT NULL
                   OR salary_max IS NOT NULL
                   OR (salary_raw IS NOT NULL AND btrim(salary_raw::text) <> '')
            )::bigint AS salary_present
        FROM dbo.normalized_jobs
    """
    quarantine_sql = """
        SELECT error_type, COUNT(*)::bigint AS record_count
        FROM dbo.normalization_quarantine
        GROUP BY error_type
        ORDER BY record_count DESC
    """
    agg = pd.read_sql(norm_agg_sql, engine)
    quarantine_df = pd.read_sql(quarantine_sql, engine)
    total = int(agg.iloc[0]["total"]) if not agg.empty else 0
    success_count = int(agg.iloc[0]["success_count"]) if not agg.empty else 0
    salary_present = int(agg.iloc[0]["salary_present"]) if not agg.empty else 0
    conf = (success_count / total * 100.0) if total > 0 else None
    sal = (salary_present / total * 100.0) if total > 0 else None
    return NormalizationObsFetchResult(
        fetched_at=ts,
        ok=True,
        error=None,
        normalized_row_count=total,
        conformance_pct=conf,
        quarantine_df=quarantine_df,
        salary_coverage_pct=sal,
    )


def resolve_ingestion_obs(ss: Any) -> tuple[IngestionObsFetchResult, bool, str | None]:
    """Run cached fetch; on failure do not poison cache — fall back to last good session snapshot."""
    try:
        fresh = _fetch_ingestion_obs_cached()
        ss[SESSION_KEY_INGESTION_GOOD] = fresh
        return fresh, False, None
    except Exception as exc:
        err_msg = str(exc)
        prev = ss.get(SESSION_KEY_INGESTION_GOOD)
        if prev is not None and isinstance(prev, IngestionObsFetchResult):
            return prev, True, err_msg
        empty = pd.DataFrame()
        fail_state = IngestionObsFetchResult(
            fetched_at=_utcnow(),
            ok=False,
            error=err_msg,
            daily_df=empty,
            runs_all_df=empty,
            recent_runs_df=empty,
            dedup_rate_pct=None,
            error_rate_pct=None,
        )
        return fail_state, False, err_msg


def resolve_normalization_obs(ss: Any) -> tuple[NormalizationObsFetchResult, bool, str | None]:
    try:
        fresh = _fetch_normalization_obs_cached()
        ss[SESSION_KEY_NORM_GOOD] = fresh
        return fresh, False, None
    except Exception as exc:
        err_msg = str(exc)
        prev = ss.get(SESSION_KEY_NORM_GOOD)
        if prev is not None and isinstance(prev, NormalizationObsFetchResult):
            return prev, True, err_msg
        empty = pd.DataFrame()
        fail_state = NormalizationObsFetchResult(
            fetched_at=_utcnow(),
            ok=False,
            error=err_msg,
            normalized_row_count=0,
            conformance_pct=None,
            quarantine_df=empty,
            salary_coverage_pct=None,
        )
        return fail_state, False, err_msg
