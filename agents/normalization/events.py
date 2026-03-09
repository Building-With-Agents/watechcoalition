"""Event payload builders for the Normalization Agent."""

from __future__ import annotations


def normalization_complete_payload(
    *,
    batch_id: str,
    region_id: str,
    normalized_count: int,
    quarantined_count: int,
    normalization_status: str,
) -> dict:
    """Build a ``NormalizationComplete`` event payload."""
    return {
        "event_type": "NormalizationComplete",
        "batch_id": batch_id,
        "region_id": region_id,
        "normalized_count": normalized_count,
        "quarantined_count": quarantined_count,
        "normalization_status": normalization_status,
    }


def normalization_failed_payload(
    *,
    batch_id: str,
    error: str,
    error_type: str = "normalization_failed",
    severity: str = "critical",
    error_reason: str | None = None,
) -> dict:
    """Build a ``NormalizationFailed`` event payload.

    Runbook (Exercise 3.4): failure events must include error_type, severity,
    and error_reason for Orchestration Agent pattern-matching in Week 6.
    """
    return {
        "event_type": "NormalizationFailed",
        "batch_id": batch_id,
        "error": error,
        "error_type": error_type,
        "severity": severity,
        "error_reason": error_reason if error_reason is not None else error,
    }
