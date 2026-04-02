"""Enrichment fuzzy deduplication (IMP-018). Public API is :func:`run_fuzzy_dedup`."""

from __future__ import annotations

from agents.enrichment.dedup.config import (
    DEDUP_ROLLING_WINDOW_DAYS,
    DEFAULT_DEDUP_COSINE_THRESHOLD,
    ENV_DEDUP_COSINE_THRESHOLD,
    JOB_POSTING_DATE_COLUMN,
    dedup_cosine_threshold,
)
from agents.enrichment.dedup.fuzzy_dedup import run_fuzzy_dedup
from agents.enrichment.dedup.types import FuzzyDedupResult

__all__ = [
    "DEFAULT_DEDUP_COSINE_THRESHOLD",
    "DEDUP_ROLLING_WINDOW_DAYS",
    "ENV_DEDUP_COSINE_THRESHOLD",
    "FuzzyDedupResult",
    "JOB_POSTING_DATE_COLUMN",
    "dedup_cosine_threshold",
    "run_fuzzy_dedup",
]
