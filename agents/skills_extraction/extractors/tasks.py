"""Tasks extraction — dimension 3 of 6.

Extracts discrete job tasks and duties from normalized job postings.

Week 4: Stub only — returns empty valid results.
Week 5 implementation (Fatima + Nestor):
- LLM extraction using Haiku-class model
- Produce TaskRecord per task with description, complexity, source_span
- Schema: task_description, category, frequency, complexity, source_span

Reference: ARCHITECTURE_DEEP.md § 6-Dimension Extraction Model.
"""

from __future__ import annotations

from agents.common.types import JobRecord, TaskRecord


def extract_tasks(job_record: JobRecord) -> list[TaskRecord]:
    """Extract tasks from a normalized job record.

    Week 4 (Fatima + Nestor): Implement stub returning empty TaskRecord[]
    that passes schema validation and integrates with the pipeline runner.

    Week 5: Replace with Haiku-class LLM extraction.

    Parameters
    ----------
    job_record : JobRecord
        A normalized job posting from the normalization pipeline.

    Returns
    -------
    list[TaskRecord]
        Extracted tasks with complexity and source spans.
    """
    raise NotImplementedError("Week 4: implement stub returning empty list with schema validation")
