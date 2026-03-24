from __future__ import annotations

"""
Context extraction (dimension 5 of 6) — Pass 1 pattern matching only.
Extracts contextual signals (remote_policy, team_size, reporting_structure,
growth_stage, ai_usage) from normalized job postings. Week 4: stub only,
returns empty list. Week 5: real implementation via pattern matching only
(no LLM, no tokens consumed). Reference: ARCHITECTURE_DEEP.md § 6-Dimension
Extraction Model.
"""
import structlog

from agents.common.types.extraction_types import ContextSignal

log = structlog.get_logger()


def extract_context(job_record: dict) -> list[ContextSignal]:
    """
    Extract context signals from a single normalized job record.

    Inputs
    ------
    job_record : dict
        A single normalized job record, e.g. from a NormalizationComplete
        payload or from normalized_jobs. Expected to contain at least
        title and description (or equivalent text fields) for pattern
        matching in the Week 5 implementation.
    Outputs
    -------
    list[ContextSignal]
        List of context signals. Each signal has signal_type, value,
        confidence, and optional source_span. This stub always returns
        an empty list.
    Extraction method
    ----------------
    Pass 1 pattern matching only. No LLM calls, no tokens consumed.
    Week 5 will add regex/keyword rules for the five signal types;
    optional LLM refinement may be added in a later pass.
    Week 4 stub
    -----------
    This stub returns an empty list and does not break the pipeline.
    Real implementation (pattern rules and source_span population)
    is delivered in Week 5.
    """
    count = 0
    log.info(
        "context_extraction_stub",
        job_record_keys=list(job_record.keys()) if job_record else [],
        context_signal_count=count,
    )
    return []
