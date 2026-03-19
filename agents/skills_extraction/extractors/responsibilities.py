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

from agents.common.types import JobRecord
from agents.common.types.extraction_types import ResponsibilityRecord


def extract_responsibilities(job_record: JobRecord) -> list[ResponsibilityRecord]:
    """Extract broader areas of ownership and responsibility from a normalized job posting.

    This dimension identifies high-level responsibilities (e.g. "Own the data
    platform roadmap", "Lead cross-functional initiatives") rather than
    discrete tasks. Week 5 implementation: LLM extraction using a Sonnet-class
    model. The current stub returns an empty list to be schema-valid and
    pipeline-safe for Week 4 integration.
    """
    return []
