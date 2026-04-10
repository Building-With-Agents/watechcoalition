"""
Analytics Agent — Phase 1 batch aggregates + Week 2 fixture overlay.

Implements **IMP-021 / Week 7 Pair A** substeps of the 13-step internal analytics
pipeline (see ``docs/planning/ARCHITECTURE_DEEP.md``): **2** skill demand weekly,
**3** tool demand weekly, **8** skill velocity, **9** skill co-occurrence.
Those run inside ``process()`` when ``PYTHON_DATABASE_URL`` is set, in dependency
order (8 and 9 only after step 2 succeeds). Each refresh uses its own
``session_scope`` commit — no single wrapping transaction.

Agent ID (canonical): analytics-agent
Emits:    AnalyticsRefreshed
Consumes: RecordEnriched

When the DB URL is unset, aggregate refresh is skipped and the legacy
``fixture_analytics_refreshed.json`` payload still merges into the outbound event
for walking-skeleton demos.

Week 7 replaces this stub with:
- Aggregation across 6 dimensions: skill, role, industry, region,
  experience level, company size
- Salary distributions: median, p25, p75, p95 per dimension
- Co-occurrence matrices
- Posting lifecycle metrics
- LLM-generated weekly summaries (deterministic template fallback)
- SQL guardrails: SELECT only, allowed tables, 100-row limit, 30s timeout

Minimum data guard (Step 1 / issue #179): when ``PYTHON_DATABASE_URL`` is set and
``ANALYTICS_DISABLE_MINIMUM_DATA_GUARD`` is not ``1``, the pipeline counts new rows
in ``dbo.job_postings`` (the enriched-job store; no separate ``enriched_jobs`` table)
with ``created_at`` / ``createdAt`` strictly after the watermark stored in
``dbo.analytics_pipeline_state.last_successful_run_at`` (updated after each successful
run). If that column is NULL (never run), all qualifying rows are counted.
Optional payload keys ``last_computed_at`` / ``analytics_last_computed_at`` override
the DB watermark for backfill and tests.

Thirteen-step batch runner: Step 1 is the minimum-data guard. Step 6 writes
``dbo.sector_summary_weekly`` via :func:`agents.analytics.aggregators.sector_weekly.compute_sector_summary_weekly`.
Step 7 writes ``dbo.geo_demand_weekly`` via
:func:`agents.analytics.aggregators.geo_demand.compute_geo_demand_weekly`.
``compute_salary_percentiles`` is implemented for single dimensions without a week
bucket; Step 6 reuses the same salary expression (:data:`SALARY_VALUE_SQL`) and
``percentile_disc(0.5)`` in SQL grouped by sector + week (see module docstring in
``sector_weekly.py``). Steps 2–5 and 8–13 are placeholders until implemented.

Weekly rollups use ``analytics_week_start`` or ``week_start`` in the inbound payload
(ISO date); if absent, the current UTC week’s Monday is used.

Fixture: agents/data/fixtures/fixture_analytics_refreshed.json
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import MetaData, Table, func, or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from agents.analytics.aggregators import (
    refresh_skill_co_occurrence,
    refresh_skill_demand_weekly,
    refresh_skill_velocity,
    refresh_tool_demand_weekly,
)
from agents.common.base_agent import BaseAgent
from agents.common.data_store.database import check_db_connection, check_db_connection_detail, session_scope
from agents.common.data_store.models import AnalyticsPipelineState
from agents.common.event_envelope import EventEnvelope
from agents.enrichment.classifiers.spam_preview import get_spam_thresholds

log = structlog.get_logger()

MINIMUM_NEW_RECORDS = 50

# Thirteen-step analytics batch pipeline (Week 7+). Step 1 = minimum-data guard in ``run_pipeline``.
ANALYTICS_PIPELINE_TOTAL_STEPS = 13

_JOB_POSTINGS_GUARD_CACHE: dict[int, Table] = {}

_FIXTURE_PATH = Path(__file__).parent.parent / "data" / "fixtures" / "fixture_analytics_refreshed.json"


def _minimum_guard_db_configured() -> bool:
    return bool(os.getenv("PYTHON_DATABASE_URL", "").strip())


def _minimum_guard_disabled() -> bool:
    return os.getenv("ANALYTICS_DISABLE_MINIMUM_DATA_GUARD", "").strip() == "1"


def _coerce_last_computed_at(payload: dict[str, Any]) -> datetime | None:
    raw = payload.get("last_computed_at") or payload.get("analytics_last_computed_at")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str):
        normalized = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return None


def get_last_analytics_success_at(session: Session) -> datetime | None:
    """Return ``last_successful_run_at`` from the singleton analytics state row (``id=1``)."""
    row = session.get(AnalyticsPipelineState, 1)
    if row is None:
        return None
    return row.last_successful_run_at


def set_last_analytics_success_at(session: Session, when: datetime) -> None:
    """Persist the watermark after a successful analytics pipeline run (same session as writes)."""
    ts = when if when.tzinfo else when.replace(tzinfo=timezone.utc)
    row = session.get(AnalyticsPipelineState, 1)
    if row is None:
        session.add(
            AnalyticsPipelineState(
                id=1,
                last_successful_run_at=ts,
                updated_at=ts,
            )
        )
    else:
        row.last_successful_run_at = ts
        row.updated_at = ts


def resolve_analytics_watermark(session: Session, payload: dict[str, Any]) -> datetime | None:
    """Watermark for the minimum-data guard: explicit payload override, else DB."""
    explicit = _coerce_last_computed_at(payload)
    if explicit is not None:
        return explicit
    return get_last_analytics_success_at(session)


def _coerce_analytics_week_start(payload: dict[str, Any]) -> date:
    """ISO week bucket for sector/geo aggregates (UTC Monday-based week of ``analytics_week_start``)."""
    raw = payload.get("analytics_week_start") or payload.get("week_start")
    if isinstance(raw, date):
        d = raw
    elif isinstance(raw, datetime):
        d = raw.date() if raw.tzinfo is None else raw.astimezone(timezone.utc).date()
    elif isinstance(raw, str) and raw.strip():
        d = date.fromisoformat(raw.strip()[:10])
    else:
        d = datetime.now(timezone.utc).date()
    # Normalize to Monday (UTC) as week_start boundary, matching typical weekly rollups.
    return d - timedelta(days=d.weekday())


def _analytics_pipeline_step_placeholder(step: int) -> None:
    log.debug("analytics_pipeline_step_placeholder", step=step, total_steps=ANALYTICS_PIPELINE_TOTAL_STEPS)


def _job_postings_table_for_guard(engine: Engine) -> Table:
    """Reflect ``dbo.job_postings`` (conceptual *enriched_jobs* table for analytics)."""
    key = id(engine)
    cached = _JOB_POSTINGS_GUARD_CACHE.get(key)
    if cached is not None:
        return cached
    md = MetaData()
    jp = Table("job_postings", md, autoload_with=engine, schema="dbo")
    _JOB_POSTINGS_GUARD_CACHE[key] = jp
    return jp


def check_minimum_data(session: Session, last_computed_at: datetime | None) -> bool:
    """Return True if enough new non-rejected enriched rows exist to run analytics.

    Counts ``dbo.job_postings`` rows (ORM-equivalent filters: exclude
    ``spam_tier`` in ``reject`` / ``rejected``) with ``created_at`` or ``createdAt``
    strictly after ``last_computed_at``. When ``last_computed_at`` is None, all
    rows matching the spam filter are counted.

    On reflection or query errors, logs and returns True (fail-open) so schema
    drift does not hard-stop the pipeline.
    """
    bind = session.get_bind()
    if bind is None:
        log.warning("analytics_minimum_data_guard_no_bind")
        return True

    try:
        jp = _job_postings_table_for_guard(bind)
        cols = jp.c

        if "created_at" in cols:
            created_col = cols.created_at
        elif "createdAt" in cols:
            created_col = cols.createdAt
        else:
            log.warning("analytics_minimum_data_guard_no_created_column")
            return True

        stmt = select(func.count()).select_from(jp)

        if last_computed_at is not None:
            ts = last_computed_at
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            stmt = stmt.where(created_col > ts)

        if "spam_tier" in cols:
            st = cols.spam_tier
            tier_norm = func.lower(func.trim(st))
            stmt = stmt.where(
                or_(
                    st.is_(None),
                    ~tier_norm.in_(("reject", "rejected")),
                )
            )
        elif "spam_score" in cols:
            _, reject_thr = get_spam_thresholds()
            sc = cols.spam_score
            stmt = stmt.where(or_(sc.is_(None), sc <= reject_thr))
        else:
            log.warning("analytics_minimum_data_guard_no_spam_columns")
            return True

        count = int(session.execute(stmt).scalar_one())

        if count < MINIMUM_NEW_RECORDS:
            log.info(
                "analytics_minimum_data_guard_skip",
                message=(
                    f"Minimum data guard: {count} new records (threshold: {MINIMUM_NEW_RECORDS}). "
                    "Skipping pipeline run — deliberate, not an error."
                ),
                new_records_count=count,
                threshold=MINIMUM_NEW_RECORDS,
            )
            return False
        return True
    except Exception as exc:
        log.warning("analytics_minimum_data_guard_error", error=str(exc))
        return True


def _db_url_configured() -> bool:
    return bool(os.getenv("PYTHON_DATABASE_URL"))


def default_analytics_target_week(reference: datetime | None = None) -> date:
    """Monday (PostgreSQL ``date_trunc('week', ...)`` anchor) for the **prior** ISO week.

    Nightly / scheduled jobs typically refresh the week that most recently
    completed (ended Sunday). ``reference`` defaults to UTC now.
    """
    ref = reference if reference is not None else datetime.now(timezone.utc)
    d = ref.date()
    this_monday = d - timedelta(days=d.weekday())
    return this_monday - timedelta(days=7)


def _resolve_target_week(payload: dict[str, Any]) -> date:
    """Parse optional override from ``RecordEnriched`` payload; else default prior Monday."""
    for key in ("analytics_target_week", "week_start", "aggregate_week_start"):
        raw = payload.get(key)
        if raw is None:
            continue
        if isinstance(raw, date):
            return raw
        if isinstance(raw, datetime):
            return raw.date()
        if isinstance(raw, str):
            # ISO8601 date or datetime prefix
            return date.fromisoformat(raw[:10])
    return default_analytics_target_week()


class AnalyticsAgent(BaseAgent):
    """Runs weekly aggregate refreshes (steps 2, 3, 8, 9) and emits ``AnalyticsRefreshed``."""

    @property
    def agent_id(self) -> str:
        return "analytics-agent"

    def __init__(self) -> None:
        self._fixture: dict[str, Any] = {}

    def _ensure_fixture(self) -> dict[str, Any]:
        if not self._fixture:
            if not _FIXTURE_PATH.exists():
                self._fixture = {}
            else:
                self._fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
        return self._fixture

    def health_check(self) -> dict:
        """Prefer DB OK when URL is set; without DB use degraded. Unreachable DB + fixture → degraded."""
        metrics: dict[str, Any] = {}
        if not _db_url_configured():
            return {
                "status": "degraded",
                "agent": self.agent_id,
                "last_run": None,
                "metrics": {**metrics, "reason": "PYTHON_DATABASE_URL not set"},
            }
        if check_db_connection():
            return {
                "status": "ok",
                "agent": self.agent_id,
                "last_run": None,
                "metrics": metrics,
            }
        _ok, err = check_db_connection_detail()
        if _FIXTURE_PATH.exists():
            return {
                "status": "degraded",
                "agent": self.agent_id,
                "last_run": None,
                "metrics": {
                    **metrics,
                    "reason": "database_unreachable",
                    "detail": err,
                    "fixture_overlay_available": True,
                },
            }
        return {
            "status": "down",
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {**metrics, "reason": "database_unreachable", "detail": err},
        }

    def _emit_analytics_refreshed(self, event: EventEnvelope) -> EventEnvelope:
        if not self._fixture:
            self._fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=out_payload,
        )

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Refresh Pair A aggregates for ``target_week``, then emit ``AnalyticsRefreshed``."""
        payload = event.payload
        target_week = _resolve_target_week(payload)
        fixture = self._ensure_fixture()

        aggregate_refresh: dict[str, Any] = {"target_week": str(target_week)}

        if _db_url_configured():
            step2_ok = False

            try:
                with session_scope() as session:
                    n2 = refresh_skill_demand_weekly(session, target_week)
                step2_ok = True
                aggregate_refresh["skill_demand_weekly_rows"] = n2
                log.info(
                    "analytics_refresh_step2",
                    agent_id=self.agent_id,
                    rows_inserted=n2,
                    target_week=str(target_week),
                    correlation_id=event.correlation_id,
                )
            except Exception as exc:
                log.exception(
                    "analytics_refresh_step2_failed",
                    agent_id=self.agent_id,
                    target_week=str(target_week),
                    correlation_id=event.correlation_id,
                    error=str(exc),
                )
                aggregate_refresh["skill_demand_weekly_error"] = str(exc)

            try:
                with session_scope() as session:
                    n3 = refresh_tool_demand_weekly(session, target_week)
                aggregate_refresh["tool_demand_weekly_rows"] = n3
                log.info(
                    "analytics_refresh_step3",
                    agent_id=self.agent_id,
                    rows_inserted=n3,
                    target_week=str(target_week),
                    correlation_id=event.correlation_id,
                )
            except Exception as exc:
                log.exception(
                    "analytics_refresh_step3_failed",
                    agent_id=self.agent_id,
                    target_week=str(target_week),
                    correlation_id=event.correlation_id,
                    error=str(exc),
                )
                aggregate_refresh["tool_demand_weekly_error"] = str(exc)

            if step2_ok:
                try:
                    with session_scope() as session:
                        n8 = refresh_skill_velocity(session, target_week)
                    aggregate_refresh["skill_velocity_rows"] = n8
                    log.info(
                        "analytics_refresh_step8",
                        agent_id=self.agent_id,
                        rows_inserted=n8,
                        target_week=str(target_week),
                        correlation_id=event.correlation_id,
                    )
                except Exception as exc:
                    log.exception(
                        "analytics_refresh_step8_failed",
                        agent_id=self.agent_id,
                        target_week=str(target_week),
                        correlation_id=event.correlation_id,
                        error=str(exc),
                    )
                    aggregate_refresh["skill_velocity_error"] = str(exc)

                try:
                    with session_scope() as session:
                        n9 = refresh_skill_co_occurrence(session, target_week)
                    aggregate_refresh["skill_co_occurrence_rows"] = n9
                    log.info(
                        "analytics_refresh_step9",
                        agent_id=self.agent_id,
                        rows_inserted=n9,
                        target_week=str(target_week),
                        correlation_id=event.correlation_id,
                    )
                except Exception as exc:
                    log.exception(
                        "analytics_refresh_step9_failed",
                        agent_id=self.agent_id,
                        target_week=str(target_week),
                        correlation_id=event.correlation_id,
                        error=str(exc),
                    )
                    aggregate_refresh["skill_co_occurrence_error"] = str(exc)
            else:
                aggregate_refresh["skill_velocity_skipped"] = True
                aggregate_refresh["skill_co_occurrence_skipped"] = True
                log.warning(
                    "analytics_refresh_steps_8_9_skipped",
                    agent_id=self.agent_id,
                    reason="step2_skill_demand_weekly_did_not_complete",
                    correlation_id=event.correlation_id,
                )
        else:
            aggregate_refresh["note"] = "PYTHON_DATABASE_URL not set — aggregate refresh skipped"
            log.warning(
                "analytics_refresh_skipped_no_db",
                agent_id=self.agent_id,
                correlation_id=event.correlation_id,
            )

        out_payload: dict[str, Any] = {
            "event_type": "AnalyticsRefreshed",
            "triggered_by_batch_id": payload.get("batch_id"),
            "aggregate_refresh": aggregate_refresh,
            **fixture,
        }

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=out_payload,
        )

    def _run_analytics_pipeline_step_6_sector_summary_weekly(
        self,
        session: Session,
        _event: EventEnvelope,
        ctx: dict[str, Any],
    ) -> None:
        """Step 6 — weekly aggregates by industry sector (posting/employer counts, p50 salary, top skills)."""
        from agents.analytics.aggregators.sector_weekly import compute_sector_summary_weekly

        week_start = ctx["week_start"]
        rows = compute_sector_summary_weekly(session, week_start)
        ctx["sector_summary_weekly_rows"] = len(rows)
        log.info(
            "analytics_pipeline_step_6_complete",
            week_start=str(week_start),
            rows=len(rows),
        )

    def _run_analytics_pipeline_step_7_geo_demand_weekly(
        self,
        session: Session,
        _event: EventEnvelope,
        ctx: dict[str, Any],
    ) -> None:
        """Step 7 — weekly job counts by Borderplex subregion (``borderplex_subregion``)."""
        from agents.analytics.aggregators.geo_demand import compute_geo_demand_weekly

        week_start = ctx["week_start"]
        rows = compute_geo_demand_weekly(session, week_start)
        ctx["geo_demand_weekly_rows"] = len(rows)
        log.info(
            "analytics_pipeline_step_7_complete",
            week_start=str(week_start),
            rows=len(rows),
        )

    def run_pipeline(self, session: Session, event: EventEnvelope) -> EventEnvelope | None:
        """Run the 13-step analytics batch. Step 1: minimum-data guard; Steps 6–7: sector and geo weekly rollups."""
        watermark = resolve_analytics_watermark(session, event.payload)
        if not check_minimum_data(session, watermark):
            return None

        ctx: dict[str, Any] = {"week_start": _coerce_analytics_week_start(event.payload)}

        for step in range(2, 6):
            _analytics_pipeline_step_placeholder(step)

        self._run_analytics_pipeline_step_6_sector_summary_weekly(session, event, ctx)

        self._run_analytics_pipeline_step_7_geo_demand_weekly(session, event, ctx)

        for step in range(8, ANALYTICS_PIPELINE_TOTAL_STEPS + 1):
            _analytics_pipeline_step_placeholder(step)

        out = self._emit_analytics_refreshed(event)
        set_last_analytics_success_at(session, datetime.now(timezone.utc))
        return out

    def process_with_guard(self, event: EventEnvelope) -> EventEnvelope | None:
        """Run the 13-step pipeline with minimum-data guard (Pair B).

        Accept a RecordEnriched event and emit an AnalyticsRefreshed event
        using the pre-loaded batch-level fixture payload when the minimum-data
        guard passes (or when the guard is not active).

        Returns None when the guard skips the run — no partial aggregates and
        no AnalyticsRefreshed event.
        """
        if not _minimum_guard_db_configured() or _minimum_guard_disabled():
            return self._emit_analytics_refreshed(event)

        with session_scope() as session:
            return self.run_pipeline(session, event)
