"""
Analytics Agent — Week 7 canonical role clustering (Pair C) + legacy fixture merge.

When ``PYTHON_DATABASE_URL`` is set and :func:`check_db_connection` is true, loads
survivor postings, runs embedding + HDBSCAN via :mod:`agents.analytics.clustering`,
persists ``canonical_roles`` / ``job_postings.canonical_role_id`` / ``role_snapshot_weekly``,
and publishes ``EmergenceAlert`` events on the optional alert bus.

Otherwise (walking skeleton / CI): emits ``AnalyticsRefreshed`` from the batch fixture
file so downstream agents keep working.

Agent ID (canonical): analytics-agent
Emits:    AnalyticsRefreshed; EmergenceAlert (bus, when registered and candidates exist)
Consumes: RecordEnriched

``CLUSTER_MIN_TOTAL_POSTINGS`` (default 500) applies only inside the clustering package.
The global analytics #179 50-posting guard is not implemented here — document in loader.
"""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import structlog

from agents.analytics.canonical_roles.loader import load_posting_cluster_features
from agents.analytics.canonical_roles.persist import cleanup_orphan_canonical_roles, persist_clustering_result
from agents.analytics.canonical_roles.snapshots import refresh_role_snapshot_weekly
from agents.analytics.clustering.config import cluster_min_total_postings
from agents.analytics.clustering.embeddings import embed_posting_features
from agents.analytics.clustering.pipeline import run_clustering_pipeline
from agents.analytics.clustering.types import ClusteringResult
from agents.common.base_agent import BaseAgent
from agents.common.data_store.database import check_db_connection, session_scope
from agents.common.event_envelope import EventEnvelope
from agents.common.events.emergence_alert import build_emergence_alert_envelope

log = structlog.get_logger()

_FIXTURE_PATH = Path(__file__).parent.parent / "data" / "fixtures" / "fixture_analytics_refreshed.json"

_alert_bus: Any | None = None


def register_alert_bus(bus: Any | None) -> None:
    """Register the bus for ``EmergenceAlert`` publishes (orchestration subscribes)."""
    global _alert_bus
    _alert_bus = bus


def _iso_week_monday(today: date) -> date:
    """UTC calendar Monday for weekly snapshot alignment."""
    return today - timedelta(days=today.weekday())


def _load_fixture_dict() -> dict[str, Any]:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _merge_analytics_payload(
    *,
    correlation_id: str,
    triggered_by_batch_id: Any,
    extras: dict[str, Any],
) -> dict[str, Any]:
    """Merge clustering metrics into the Week 2 fixture shape for downstream compatibility."""
    base = _load_fixture_dict()
    out: dict[str, Any] = {
        **base,
        "event_type": "AnalyticsRefreshed",
        "triggered_by_batch_id": triggered_by_batch_id,
        **extras,
    }
    return out


class AnalyticsAgent(BaseAgent):
    """Analytics: canonical role clustering when DB is available; else fixture path."""

    @property
    def agent_id(self) -> str:
        return "analytics-agent"

    def __init__(self) -> None:
        self._fixture: dict[str, Any] = {}

    def health_check(self) -> dict:
        """DB + fixture: ok when DB reachable; degraded when only fixture; down if neither."""
        db_ok = False
        if os.getenv("PYTHON_DATABASE_URL"):
            db_ok = check_db_connection()
        fixture_ok = _FIXTURE_PATH.exists()
        try:
            if fixture_ok:
                self._fixture = _load_fixture_dict()
        except Exception:
            fixture_ok = False

        if db_ok:
            return {
                "status": "ok",
                "agent": self.agent_id,
                "last_run": None,
                "metrics": {"db_connected": True, "fixture_available": fixture_ok},
            }
        if fixture_ok:
            return {
                "status": "degraded",
                "agent": self.agent_id,
                "last_run": None,
                "metrics": {"db_connected": False, "fixture_available": True},
            }
        return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        triggered_by_batch_id = event.payload.get("batch_id")
        extras: dict[str, Any] = {
            "canonical_clustering_ran": False,
            "clustering_skipped": True,
            "clustering_skip_reason": None,
            "cluster_min_total_postings": cluster_min_total_postings(),
        }

        if not os.getenv("PYTHON_DATABASE_URL") or not check_db_connection():
            log.info("analytics_fixture_path", reason="db_unavailable", correlation_id=event.correlation_id)
            payload = _merge_analytics_payload(
                correlation_id=event.correlation_id,
                triggered_by_batch_id=triggered_by_batch_id,
                extras=extras,
            )
            return EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload=payload,
            )

        result: ClusteringResult | None = None
        cluster_id_to_role_id: dict[str, str] = {}

        try:
            with session_scope() as session:
                limit_raw = os.getenv("ANALYTICS_CLUSTERING_LOAD_LIMIT")
                limit = int(limit_raw) if limit_raw and limit_raw.isdigit() else None
                features = load_posting_cluster_features(session, limit=limit)
                extras["clustering_features_loaded"] = len(features)

                if len(features) < cluster_min_total_postings():
                    extras["clustering_skip_reason"] = "insufficient_total_postings"
                    payload = _merge_analytics_payload(
                        correlation_id=event.correlation_id,
                        triggered_by_batch_id=triggered_by_batch_id,
                        extras=extras,
                    )
                    return EventEnvelope(
                        correlation_id=event.correlation_id,
                        agent_id=self.agent_id,
                        payload=payload,
                    )

                embedded = embed_posting_features(features, allow_partial=False)
                if embedded is None:
                    extras["clustering_skip_reason"] = "embedding_generation_failed"
                    payload = _merge_analytics_payload(
                        correlation_id=event.correlation_id,
                        triggered_by_batch_id=triggered_by_batch_id,
                        extras=extras,
                    )
                    return EventEnvelope(
                        correlation_id=event.correlation_id,
                        agent_id=self.agent_id,
                        payload=payload,
                    )

                result = run_clustering_pipeline(features, embedded)

                if result.skipped:
                    extras["clustering_skip_reason"] = result.skip_reason
                    payload = _merge_analytics_payload(
                        correlation_id=event.correlation_id,
                        triggered_by_batch_id=triggered_by_batch_id,
                        extras=extras,
                    )
                    return EventEnvelope(
                        correlation_id=event.correlation_id,
                        agent_id=self.agent_id,
                        payload=payload,
                    )

                persist_info = persist_clustering_result(
                    session,
                    result,
                    correlation_id=event.correlation_id,
                )
                week_start = _iso_week_monday(date.today())
                snapshot_rows = refresh_role_snapshot_weekly(session, week_start=week_start)
                orphans_deleted = cleanup_orphan_canonical_roles(session)

                extras.update(
                    {
                        "canonical_clustering_ran": True,
                        "clustering_skipped": False,
                        "clustering_skip_reason": None,
                        "clustering_total_input": result.total_input_postings,
                        "clustering_eligible_count": result.eligible_posting_count,
                        "clustering_cluster_count": len(result.clusters),
                        "clustering_noise_count": result.noise_posting_count,
                        "canonical_roles_inserted": persist_info.get("roles_inserted"),
                        "canonical_postings_updated": persist_info.get("postings_updated"),
                        "canonical_roles_orphans_deleted": orphans_deleted,
                        "role_snapshot_weekly_rows": snapshot_rows,
                        "role_snapshot_week_start": week_start.isoformat(),
                        "emergence_candidate_count": len(result.emergence_candidates),
                    }
                )

                cluster_id_to_role_id = persist_info["cluster_id_to_role_id"]

        except Exception as exc:
            log.warning("analytics_clustering_failed", error=str(exc), correlation_id=event.correlation_id)
            extras["clustering_skip_reason"] = "exception"
            extras["clustering_error_class"] = type(exc).__name__
            payload = _merge_analytics_payload(
                correlation_id=event.correlation_id,
                triggered_by_batch_id=triggered_by_batch_id,
                extras=extras,
            )
            return EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload=payload,
            )

        if result is None:
            extras["clustering_skip_reason"] = "no_result"
            payload = _merge_analytics_payload(
                correlation_id=event.correlation_id,
                triggered_by_batch_id=triggered_by_batch_id,
                extras=extras,
            )
            return EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload=payload,
            )

        payload = _merge_analytics_payload(
            correlation_id=event.correlation_id,
            triggered_by_batch_id=triggered_by_batch_id,
            extras=extras,
        )
        out = EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )

        if _alert_bus is not None and result.emergence_candidates:
            for cand in result.emergence_candidates:
                try:
                    _alert_bus.publish(
                        build_emergence_alert_envelope(
                            cand,
                            correlation_id=event.correlation_id,
                            cluster_id_to_role_id=cluster_id_to_role_id,
                        )
                    )
                except Exception as exc:
                    log.warning(
                        "emergence_alert_publish_failed",
                        error=str(exc),
                        correlation_id=event.correlation_id,
                    )

        return out
