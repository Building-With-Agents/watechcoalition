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

from agents.common.types import JobRecord
from agents.common.types.extraction_types import TaskRecord


def extract_tasks(job_record: JobRecord) -> list[TaskRecord]:
    """Extract specific, actionable tasks from a normalized job posting.
    This dimension identifies discrete duties and tasks (e.g. "Maintain CI/CD
    pipelines", "Review code for security issues") from the job text. Week 5
    implementation: LLM extraction using a Haiku-class model. The current
    stub returns an empty list to be schema-valid and pipeline-safe for
    Week 4 integration.
    """
    return []
