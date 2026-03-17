"""Responsibilities extraction — dimension 4 of 6.

Extracts job responsibilities with scope classification from normalized
job postings.

Week 4: Stub only — returns empty valid results.
Week 5 implementation (Fatima + Nestor):
- LLM extraction using Sonnet-class model
- Produce ResponsibilityRecord per item with description, scope, source_span
- Schema: responsibility_description, scope, level, source_span

Reference: ARCHITECTURE_DEEP.md § 6-Dimension Extraction Model.
"""

from __future__ import annotations

from agents.common.types import JobRecord, ResponsibilityRecord


def extract_responsibilities(job_record: JobRecord) -> list[ResponsibilityRecord]:
    """Extract responsibilities from a normalized job record.

    Week 4 (Fatima + Nestor): Implement stub returning empty ResponsibilityRecord[]
    that passes schema validation and integrates with the pipeline runner.

    Week 5: Replace with Sonnet-class LLM extraction.

    Parameters
    ----------
    job_record : JobRecord
        A normalized job posting from the normalization pipeline.

    Returns
    -------
    list[ResponsibilityRecord]
        Extracted responsibilities with scope and source spans.
    """
    raise NotImplementedError("Week 4: implement stub returning empty list with schema validation")
