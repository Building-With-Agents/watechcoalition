"""Skills extraction — Pass 2 (LLM-based).

Extracts nuanced skills from normalized job postings using a Sonnet-class LLM.
Each skill is linked to the ESCO digital skills taxonomy via the 6-step
resolution order, with GenAI Extension Layer checked first.

Week 4 implementation (Bryan + Emilio):
- Consume normalized JobRecord documents
- Extract skills from title, description, requirements, responsibilities
- Produce SkillRecord per skill with esco_uri and source_span
- Use Sonnet-class model (configured via EXTRACTION_MODEL_SKILLS env var)
- Track tokens_used per extraction call
- Handle LLM timeout: retry once, then emit with skills=[] and extraction_failed=true
- Handle rate limit (429): exponential back-off with SkillsExtractionAlert

Reference: ARCHITECTURE_DEEP.md § Work Intelligence Agent — Hybrid Extraction.
"""

from __future__ import annotations

from agents.common.types import JobRecord, SkillRecord


def extract_skills(job_record: JobRecord) -> list[SkillRecord]:
    """Extract skills from a normalized job record using LLM inference.

    Parameters
    ----------
    job_record : JobRecord
        A normalized job posting from the normalization pipeline.

    Returns
    -------
    list[SkillRecord]
        Extracted skills with taxonomy linking and source spans.
        Returns empty list in stub mode.
    """
    # Stub — returns empty valid result.
    # Week 4: Replace with Sonnet-class LLM extraction + taxonomy linking.
    return []
