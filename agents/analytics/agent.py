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

Fixture: agents/data/fixtures/fixture_analytics_refreshed.json
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import structlog

from agents.analytics.aggregators import (
    refresh_skill_co_occurrence,
    refresh_skill_demand_weekly,
    refresh_skill_velocity,
    refresh_tool_demand_weekly,
)
from agents.common.base_agent import BaseAgent
from agents.common.data_store.database import check_db_connection, check_db_connection_detail, session_scope
from agents.common.event_envelope import EventEnvelope

log = structlog.get_logger()

_FIXTURE_PATH = Path(__file__).parent.parent / "data" / "fixtures" / "fixture_analytics_refreshed.json"


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
