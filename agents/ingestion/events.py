"""Event payload builders for the Ingestion Agent."""

from __future__ import annotations


def ingest_batch_payload(
    *,
    batch_id: str,
    source: str,
    region_id: str,
    total_fetched: int,
    staged_count: int,
    dedup_count: int,
    error_count: int,
) -> dict:
    """Build an ``IngestBatch`` event payload."""
    return {
        "event_type": "IngestBatch",
        "batch_id": batch_id,
        "source": source,
        "region_id": region_id,
        "total_fetched": total_fetched,
        "staged_count": staged_count,
        "dedup_count": dedup_count,
        "error_count": error_count,
    }


def source_failure_payload(
    *,
    run_id: str,
    source: str,
    error: str,
    error_type: str = "source_unreachable",
    severity: str = "critical",
    error_reason: str | None = None,
) -> dict:
    """Build a ``SourceFailure`` event payload.

    Runbook (Exercise 3.4): failure events must include error_type, severity,
    and error_reason for Orchestration Agent pattern-matching in Week 6.
    """
    return {
        "event_type": "SourceFailure",
        "run_id": run_id,
        "source": source,
        "error": error,
        "error_type": error_type,
        "severity": severity,
        "error_reason": error_reason if error_reason is not None else error,
    }
