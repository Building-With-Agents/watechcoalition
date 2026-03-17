"""Tools extraction — Pass 1 (pattern matching) + optional LLM verification.

Extracts programming languages, frameworks, platforms, databases, and DevOps
tools from job posting text using regex/dictionary lookup. High-confidence
pattern matches incur zero LLM cost. Ambiguous matches are verified with a
Haiku-class LLM.

Week 4 implementation (Bryan + Emilio):
- Pattern matching (Pass 1) — regex/dictionary lookup against known tool lists
- Produce ToolRecord per tool with tool_name, category, confidence, source_span
- Verify with LLM (Haiku-class) only for ambiguous matches
- Zero LLM cost for high-confidence pattern matches

Reference: ARCHITECTURE_DEEP.md § Work Intelligence Agent — Hybrid Extraction.
"""

from __future__ import annotations

from agents.common.types import JobRecord, ToolRecord


def extract_tools(job_record: JobRecord) -> list[ToolRecord]:
    """Extract tools from a normalized job record using pattern matching.

    Parameters
    ----------
    job_record : JobRecord
        A normalized job posting from the normalization pipeline.

    Returns
    -------
    list[ToolRecord]
        Extracted tools with categories and source spans.
        Returns empty list in stub mode.
    """
    # Stub — returns empty valid result.
    # Week 4: Replace with regex/dictionary pattern matching + Haiku verification.
    return []
