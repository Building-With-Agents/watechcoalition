"""Fuzzy near-duplicate detection (embedding cosine similarity). Phase 0: stub implementation."""

from __future__ import annotations

import structlog
from sqlalchemy.orm import Session

from agents.enrichment.dedup.config import dedup_cosine_threshold
from agents.enrichment.dedup.types import FuzzyDedupResult

log = structlog.get_logger()


def run_fuzzy_dedup(
    session: Session,
    job_posting_id: str,
    *,
    threshold: float | None = None,
) -> FuzzyDedupResult:
    """
    Compare one posting's embedding against same-company survivors in the rolling window.

    **Phase 0:** Returns a safe default (not duplicate) and logs once. Replace the body
    with: load row, compose dedup text, embed, query candidates, cosine vs threshold,
    survivor selection, then UPDATE ``is_duplicate`` / ``duplicate_cluster_id``.

    Parameters
    ----------
    session
        SQLAlchemy session (caller manages transaction scope).
    job_posting_id
        ``dbo.job_postings.job_posting_id`` as string (UUID text).
    threshold
        Cosine similarity threshold; defaults to :func:`dedup_cosine_threshold` (env
        ``DEDUP_COSINE_THRESHOLD`` or 0.92).

    Notes
    -----
    - Compare only rows with the same ``company_id``.
    - Window: rolling ``DEDUP_ROLLING_WINDOW_DAYS`` from anchor ``publish_date`` (see CONTEXT.md).
    - Embedding + audit: reuse ``taxonomy._embed_texts_azure`` pattern; log via ``log_extraction_event``.
    """
    _ = session  # used in live implementation
    effective = dedup_cosine_threshold() if threshold is None else threshold
    log.info(
        "fuzzy_dedup_stub",
        job_posting_id=job_posting_id,
        threshold=effective,
        message="Phase 0 stub — no embedding or DB updates; implement in agents.enrichment.dedup.fuzzy_dedup",
    )
    return FuzzyDedupResult(
        is_duplicate=False,
        duplicate_cluster_id=None,
        survivor_job_posting_id=None,
        stub=True,
    )
