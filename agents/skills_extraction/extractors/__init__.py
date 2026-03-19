from __future__ import annotations

"""Extraction functions for the Work Intelligence Agent's 6-dimension model.
Week 4: Skills + Tools extraction (Bryan+Emilio), Taxonomy resolution (Angel+Fabian).
Week 5: Tasks + Responsibilities + Context extraction (full implementation).
"""
from agents.skills_extraction.extractors.context import extract_context
from agents.skills_extraction.extractors.responsibilities import extract_responsibilities
from agents.skills_extraction.extractors.skills import extract_skills
from agents.skills_extraction.extractors.tasks import extract_tasks
from agents.skills_extraction.extractors.taxonomy import (
    resolution_stats,
    resolve_taxonomy,
    resolve_taxonomy_batch,
)
from agents.skills_extraction.extractors.tools import extract_tools

__all__ = [
    "extract_context",
    "extract_responsibilities",
    "extract_skills",
    "extract_tasks",
    "extract_tools",
    "resolution_stats",
    "resolve_taxonomy",
    "resolve_taxonomy_batch",
]
