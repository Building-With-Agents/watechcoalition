from __future__ import annotations

"""
APScheduler-based scheduler for the Job Intelligence Engine walking skeleton.

This module wires together the Ingestion and Normalization agents and runs
them on a fixed 60-second interval. Each cycle:
    1. Creates a new EventEnvelope with a fresh correlation_id.
    2. Invokes IngestionAgent.process(event).
    3. Passes the resulting event directly to NormalizationAgent.process(event).
    4. Logs correlation_id, record_count, valid_count, and quarantine_count.
    5. Logs when either agent returns a failure event type.

Run with:

    PYTHONPATH=. python3 agents/orchestration/scheduler.py
"""

import secrets
from typing import Any

import structlog
from apscheduler.schedulers.blocking import BlockingScheduler

from agents.common.event_envelope import EventEnvelope
from agents.ingestion.agent import IngestionAgent, SourceConfig
from agents.normalization.agent import NormalizationAgent

log = structlog.get_logger()


def _uuid4_str() -> str:
    """
    Generate a UUID4-compatible string without importing the stdlib uuid module.

    This avoids potential interference from misconfigured platform modules
    while still producing valid v4-style identifiers for correlation_ids.
    """
    random_bytes = bytearray(secrets.token_bytes(16))
    random_bytes[6] = (random_bytes[6] & 0x0F) | 0x40  # version 4
    random_bytes[8] = (random_bytes[8] & 0x3F) | 0x80  # variant 10xx
    hexed = random_bytes.hex()
    return (
        f"{hexed[0:8]}-"
        f"{hexed[8:12]}-"
        f"{hexed[12:16]}-"
        f"{hexed[16:20]}-"
        f"{hexed[20:32]}"
    )


def _is_failure_event(payload: dict[str, Any]) -> bool:
    """
    Determine whether an event payload represents a failure event.

    Checks for known failure event_type values such as SourceFailure and
    NormalizationFailed.
    """
    event_type = payload.get("event_type")
    return event_type in {"SourceFailure", "NormalizationFailed"}


def _run_cycle(ingestion: IngestionAgent, normalization: NormalizationAgent) -> None:
    """
    Execute a single ingestion + normalization cycle.

    Creates an EventEnvelope with a fresh correlation_id, runs the Ingestion
    agent, then passes the resulting event directly into the Normalization
    agent. Logs success metrics and any failure events observed.
    """
    correlation_id = _uuid4_str()

    log.info("scheduler_cycle_start", correlation_id=correlation_id)

    inbound = EventEnvelope(
        correlation_id=correlation_id,
        agent_id="orchestration_scheduler",
        payload={},
    )

    ingest_event = ingestion.process(inbound)
    ingest_payload = ingest_event.payload or {}

    if _is_failure_event(ingest_payload):
        log.error(
            "scheduler_ingestion_failure",
            correlation_id=correlation_id,
            event_type=ingest_payload.get("event_type"),
        )
        # Pass the failure event forward so downstream orchestration can react.
        current_event = ingest_event
        valid_count = 0
        quarantine_count = 0
    else:
        batch_id = ingest_payload.get("batch_id")
        record_count = ingest_payload.get("record_count", 0)
        dedup_count = ingest_payload.get("dedup_count", 0)

        log.info(
            "scheduler_ingestion_success",
            correlation_id=correlation_id,
            batch_id=batch_id,
            record_count=record_count,
            dedup_count=dedup_count,
        )

        current_event = ingest_event

    norm_event = normalization.process(current_event)
    norm_payload = norm_event.payload or {}

    if _is_failure_event(norm_payload):
        log.error(
            "scheduler_normalization_failure",
            correlation_id=correlation_id,
            event_type=norm_payload.get("event_type"),
        )
        valid_count = 0
        quarantine_count = 0
    else:
        valid_count = norm_payload.get("valid_count", 0)
        quarantine_count = norm_payload.get("quarantine_count", 0)

    log.info(
        "scheduler_cycle_complete",
        correlation_id=correlation_id,
        ingest_record_count=ingest_payload.get("record_count", 0),
        ingest_dedup_count=ingest_payload.get("dedup_count", 0),
        normalization_valid_count=valid_count,
        normalization_quarantine_count=quarantine_count,
    )


def main() -> None:
    """
    Configure and start the APScheduler BlockingScheduler for the pipeline.

    Schedules a job that runs every 60 seconds to trigger the ingestion and
    normalization agents in sequence. Handles graceful shutdown on
    KeyboardInterrupt.
    """
    source_cfg = SourceConfig(
        name="crawl4ai",
        type="web_scrape",
        url="fixture://fallback",
    )
    ingestion_agent = IngestionAgent(source=source_cfg)
    normalization_agent = NormalizationAgent()

    scheduler = BlockingScheduler()
    scheduler.add_job(
        _run_cycle,
        "interval",
        seconds=60,
        args=[ingestion_agent, normalization_agent],
        id="pipeline_cycle",
        max_instances=1,
        coalesce=True,
    )

    log.info("scheduler_started", interval_seconds=60)

    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("scheduler_shutdown_requested")
        scheduler.shutdown(wait=True)
        log.info("scheduler_stopped")


if __name__ == "__main__":
    main()

