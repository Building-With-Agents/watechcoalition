"""
Analytics Agent — Week 7 pipeline (scaffold) + Week 2 fixture fallback.

Internal processing order matches ``ARCHITECTURE_DEEP.md`` (13 steps). Steps 1–9 are Phase 1
stubs. Step 10 wires posting-freshness computation + staleness/cardinality guardrails and,
when ``PYTHON_DATABASE_URL`` is set and the DB is reachable, upserts rows to
``dbo.posting_freshness``; step 11 builds an empty trajectory scaffold (Phase 2 placeholder);
step 12 runs
``generate_summaries`` over the scaffold + posting freshness; step 13 emits
``AnalyticsRefreshed`` via :func:`agents.analytics.insights.events.build_analytics_refreshed_event`.

Agent ID (canonical): analytics-agent
Emits:    AnalyticsRefreshed
          AnalyticsStaleAlert / CardinalityWarning (optional alert bus, orchestration-only)
Consumes: RecordEnriched

Fixture: agents/data/fixtures/fixture_analytics_refreshed.json
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from agents.analytics.insights.events import build_analytics_refreshed_event
from agents.analytics.insights.freshness import PostingFreshnessResult, detect_staleness
from agents.analytics.insights.guardrails import (
    CARDINALITY_CAP,
    build_cardinality_warning_payload,
    build_stale_alert_payload,
    cap_cardinality,
    check_staleness,
)
from agents.analytics.insights.llm_summary import SummaryResult, generate_summaries
from agents.analytics.insights.posting_freshness_store import (
    build_posting_freshness_row_dicts,
    persist_posting_freshness_rows,
)
from agents.analytics.insights.trajectory import TrajectoryEntry, build_trajectory_map
from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

log = structlog.get_logger()

_FIXTURE_PATH = Path(__file__).parent.parent / "data" / "fixtures" / "fixture_analytics_refreshed.json"

_analytics_alert_bus: Any | None = None
_trajectory_scaffold_phase2_logged = False


def register_analytics_alert_bus(bus: Any | None) -> None:
    """Register the in-process bus so ``AnalyticsStaleAlert`` / ``CardinalityWarning`` can publish."""
    global _analytics_alert_bus
    _analytics_alert_bus = bus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _records_from_record_enriched_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize ``RecordEnriched`` payload to a list of job rows (batch or single-record)."""
    fr = payload.get("freshness_records")
    if isinstance(fr, list) and len(fr) > 0:
        return [dict(x) if isinstance(x, dict) else {} for x in fr]
    raw = payload.get("records")
    if isinstance(raw, list) and len(raw) > 0:
        return [dict(x) if isinstance(x, dict) else {} for x in raw]
    if payload.get("posting_id") is not None:
        return [dict(payload)]
    return []


def _parse_optional_iso(dt_val: Any) -> datetime | None:
    if not dt_val or not isinstance(dt_val, str):
        return None
    try:
        return datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
    except ValueError:
        return None


def _collect_skill_labels(records: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for r in records:
        for s in r.get("skills") or []:
            if not isinstance(s, dict):
                continue
            label = s.get("name") or s.get("label")
            if not label:
                continue
            t = str(label).strip()
            if not t or t in seen:
                continue
            seen.add(t)
            ordered.append(t)
    return ordered


class AnalyticsAgent(BaseAgent):
    """Analytics Agent — 13-step internal pipeline with Week 2 fixture output."""

    @property
    def agent_id(self) -> str:
        return "analytics-agent"

    def __init__(self) -> None:
        self._fixture: dict = {}
        self._last_trajectory_scaffold: dict[str, TrajectoryEntry] = {}
        self._freshness_results: list[PostingFreshnessResult] = []
        self._summaries: list[SummaryResult] = []

    def health_check(self) -> dict:
        """Return ok status if the fixture file is present and loadable."""
        if not _FIXTURE_PATH.exists():
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}
        try:
            self._fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
            return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}
        except Exception:
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def _emit_control_plane_event(self, correlation_id: str, payload: dict[str, Any]) -> None:
        if _analytics_alert_bus is None:
            return
        try:
            _analytics_alert_bus.publish(
                EventEnvelope(
                    correlation_id=correlation_id,
                    agent_id=self.agent_id,
                    payload=payload,
                )
            )
        except Exception as exc:
            log.warning(
                "analytics_control_event_publish_failed",
                event_type=payload.get("event_type"),
                error=str(exc),
            )

    def _pipeline_step_1_data_validation_and_freshness_check(self, payload: dict[str, Any]) -> None:
        """Step 1 — data validation + freshness check (Phase 1 stub)."""

    def _pipeline_step_2_skill_demand_aggregation(self, payload: dict[str, Any]) -> None:
        """Step 2 — skill demand aggregation (Phase 1 stub)."""

    def _pipeline_step_3_tool_demand_aggregation(self, payload: dict[str, Any]) -> None:
        """Step 3 — tool demand aggregation (Phase 1 stub)."""

    def _pipeline_step_4_role_clustering(self, payload: dict[str, Any]) -> None:
        """Step 4 — CanonicalRole discovery (Phase 1 stub)."""

    def _pipeline_step_5_role_snapshot(self, payload: dict[str, Any]) -> None:
        """Step 5 — role snapshot computation (Phase 1 stub)."""

    def _pipeline_step_6_sector_summary(self, payload: dict[str, Any]) -> None:
        """Step 6 — sector summary (Phase 1 stub)."""

    def _pipeline_step_7_geo_demand(self, payload: dict[str, Any]) -> None:
        """Step 7 — geographic demand aggregation (Phase 1 stub)."""

    def _pipeline_step_8_skill_velocity(self, payload: dict[str, Any]) -> None:
        """Step 8 — skill velocity (Phase 1 stub)."""

    def _pipeline_step_9_skill_co_occurrence(self, payload: dict[str, Any]) -> None:
        """Step 9 — skill co-occurrence (Phase 1 stub)."""

    def _pipeline_step_10_posting_freshness_guardrails(
        self,
        correlation_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Step 10 — posting freshness rows, posting-age staleness, aggregate staleness alert, cardinality."""
        computed_at = _utc_now()
        records = _records_from_record_enriched_payload(payload)
        posting_rows = build_posting_freshness_row_dicts(records, computed_at)
        persist_posting_freshness_rows(posting_rows)
        log.info(
            "analytics_step_10_posting_freshness",
            row_count=len(posting_rows),
            batch_id=payload.get("batch_id"),
        )

        detect_inputs: list[dict[str, Any]] = []
        for r in records:
            if r.get("posting_id") is None:
                continue
            detect_inputs.append(
                {
                    "posting_id": str(r.get("posting_id")),
                    "days_since_posted": int(r.get("days_since_posted", 0)),
                }
            )
        if detect_inputs:
            self._freshness_results = detect_staleness(detect_inputs)
        else:
            self._freshness_results = []

        aggregate_computed_at = _parse_optional_iso(payload.get("analytics_aggregate_computed_at")) or computed_at
        queried_at = _utc_now()
        if check_staleness("posting_freshness", aggregate_computed_at):
            self._emit_control_plane_event(
                correlation_id,
                build_stale_alert_payload("posting_freshness", aggregate_computed_at, queried_at),
            )

        skill_labels = _collect_skill_labels(records)
        _, warn = cap_cardinality(skill_labels)
        if warn:
            self._emit_control_plane_event(
                correlation_id,
                build_cardinality_warning_payload(
                    "skill_demand_weekly",
                    "skill_label",
                    original_count=len(skill_labels),
                    cap=CARDINALITY_CAP,
                ),
            )

    def _pipeline_step_11_trajectory_scaffold(self, payload: dict[str, Any]) -> None:
        """Step 11 — trajectory map scaffold (empty in-memory; ``dbo.trajectory_map`` Phase 2)."""
        global _trajectory_scaffold_phase2_logged
        self._last_trajectory_scaffold = build_trajectory_map([])
        log.info("analytics_step_11_trajectory_scaffold", keys=len(self._last_trajectory_scaffold))
        if not _trajectory_scaffold_phase2_logged:
            log.info(
                "analytics_trajectory_map_schema_only_phase2",
                note="dbo.trajectory_map row population is Phase 2; scaffold is in-memory only",
            )
            _trajectory_scaffold_phase2_logged = True

    def _pipeline_step_12_disruption_fingerprint(self, payload: dict[str, Any]) -> None:
        """Step 12 — LLM insight summaries from trajectory scaffold + posting freshness."""
        freshness_results = self._freshness_results
        trajectory_map = self._last_trajectory_scaffold
        self._summaries = generate_summaries(trajectory_map, freshness_results)
        llm_generated = sum(1 for s in self._summaries if s.get("is_llm_generated"))
        fallback = len(self._summaries) - llm_generated
        log.info(
            "analytics_step_12_llm_summaries",
            total=len(self._summaries),
            llm_generated=llm_generated,
            fallback=fallback,
            batch_id=payload.get("batch_id"),
        )

    def _pipeline_step_13_llm_insight_summary(self, correlation_id: str, payload: dict[str, Any]) -> EventEnvelope:
        """Step 13 — emit ``AnalyticsRefreshed`` with Week 7 counts and summary rollups."""
        batch_id = str(payload.get("batch_id") or "")
        return build_analytics_refreshed_event(
            correlation_id=correlation_id,
            batch_id=batch_id,
            freshness_results=self._freshness_results,
            trajectory_map=self._last_trajectory_scaffold,
            summaries=self._summaries,
        )

    def _run_internal_pipeline(self, correlation_id: str, payload: dict[str, Any]) -> EventEnvelope:
        self._pipeline_step_1_data_validation_and_freshness_check(payload)
        self._pipeline_step_2_skill_demand_aggregation(payload)
        self._pipeline_step_3_tool_demand_aggregation(payload)
        self._pipeline_step_4_role_clustering(payload)
        self._pipeline_step_5_role_snapshot(payload)
        self._pipeline_step_6_sector_summary(payload)
        self._pipeline_step_7_geo_demand(payload)
        self._pipeline_step_8_skill_velocity(payload)
        self._pipeline_step_9_skill_co_occurrence(payload)
        self._pipeline_step_10_posting_freshness_guardrails(correlation_id, payload)
        self._pipeline_step_11_trajectory_scaffold(payload)
        self._pipeline_step_12_disruption_fingerprint(payload)
        return self._pipeline_step_13_llm_insight_summary(correlation_id, payload)

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Run the 13-step internal pipeline, then emit ``AnalyticsRefreshed`` from step 13.
        """
        if not self._fixture:
            self._fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

        correlation_id = event.correlation_id
        payload = event.payload if isinstance(event.payload, dict) else {}

        return self._run_internal_pipeline(correlation_id, payload)
