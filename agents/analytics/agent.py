"""
Analytics Agent stub — Week 2 Walking Skeleton.

Real implementation: Week 7 (aggregates) + Week 8 (Ask the Data).

In the walking skeleton this agent returns the pre-computed batch analytics
fixture (fixture_analytics_refreshed.json) for every record it processes.
The fixture represents aggregate analytics across all 10 demo postings.

Note: in the walking skeleton, the same batch analytics payload is emitted
for every record processed.  In Week 7 the Analytics Agent accumulates data
across all records before emitting a single AnalyticsRefreshed event at
the end of a batch run.

``RecordEnriched`` batch payloads (schema v3) include ``batch_id``, batch counts,
distributions, and ``dedup``; this stub sets ``triggered_by_batch_id`` from that envelope.

Agent ID (canonical): analytics-agent
Emits:    AnalyticsRefreshed
Consumes: RecordEnriched

Fixture: agents/data/fixtures/fixture_analytics_refreshed.json

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
before any aggregate work or ``AnalyticsRefreshed`` emission.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import MetaData, Table, func, or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from agents.common.base_agent import BaseAgent
from agents.common.data_store.database import session_scope
from agents.common.event_envelope import EventEnvelope
from agents.enrichment.classifiers.spam_preview import get_spam_thresholds

log = structlog.get_logger()

MINIMUM_NEW_RECORDS = 50

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


class AnalyticsAgent(BaseAgent):
    """
    Stub for the Analytics Agent.

    Week 2: returns batch-level fixture data for every record processed.
    Week 7: replaces this with real aggregate queries and LLM summaries.
    """

    @property
    def agent_id(self) -> str:
        return "analytics-agent"

    def __init__(self) -> None:
        self._fixture: dict = {}

    def health_check(self) -> dict:
        """Return ok status if the fixture file is present and loadable."""
        if not _FIXTURE_PATH.exists():
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}
        try:
            self._fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
            return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}
        except Exception:
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def _emit_analytics_refreshed(self, event: EventEnvelope) -> EventEnvelope:
        if not self._fixture:
            self._fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "AnalyticsRefreshed",
                "triggered_by_batch_id": event.payload.get("batch_id"),
                **self._fixture,
            },
        )

    def run_pipeline(self, session: Session, last_computed_at: datetime | None, event: EventEnvelope) -> EventEnvelope | None:
        """Run analytics batch work. Minimum-data guard is always the first step."""
        if not check_minimum_data(session, last_computed_at):
            return None
        return self._emit_analytics_refreshed(event)

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """
        Accept a RecordEnriched event and emit an AnalyticsRefreshed event
        using the pre-loaded batch-level fixture payload when the minimum-data
        guard passes (or when the guard is not active).

        Returns None when the guard skips the run — no partial aggregates and
        no AnalyticsRefreshed event.
        """
        last_computed_at = _coerce_last_computed_at(event.payload)

        if not _minimum_guard_db_configured() or _minimum_guard_disabled():
            return self._emit_analytics_refreshed(event)

        with session_scope() as session:
            return self.run_pipeline(session, last_computed_at, event)
