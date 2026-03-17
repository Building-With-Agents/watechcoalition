from __future__ import annotations
"""Context extraction — dimension 5 of 6.
Extracts contextual signals (remote policy, team size, reporting structure,
growth stage, AI usage) from normalized job postings using pattern matching.
Week 4: Stub only — returns empty valid results.
Week 5 implementation (Fatima + Nestor):
- Pattern matching (Pass 1) — no LLM cost
- Produce ContextSignal per signal with signal_type, value, confidence
- Schema: signal_type, value, confidence, source_span
Reference: ARCHITECTURE_DEEP.md § 6-Dimension Extraction Model.
"""
import structlog
from agents.common.types import ContextSignal, JobRecord

log = structlog.get_logger()


def extract_context(job_record: JobRecord) -> list[ContextSignal]:
    """Extract context signals from a normalized job record.
    Week 4 (Fatima + Nestor): Stub returning empty list with schema validation.
    Week 5: Replace with pattern-matching extraction.

    Parameters
    ----------
    job_record : JobRecord
        A normalized job posting from the normalization pipeline.

    Returns
    -------
    list[ContextSignal]
        Extracted context signals with types and confidence.
    """
    log.info("context_extraction_stub", context_signal_count=0)
    return []
