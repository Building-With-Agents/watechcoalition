"""Persist Phase 1 enrichment columns to ``dbo.job_postings`` (Decision #8 gating).

Resolves the posting row via ``normalized_jobs.id`` + matching ``source`` /
``external_id``. **Rejected** spam tier (``spam_score > SPAM_REJECT_THRESHOLD``):
no ``UPDATE`` — the row may already exist from upstream ingestion; enrichment
columns are left unchanged.

**Uncertain / degraded** (no numeric ``spam_score``): updates ``quality_score``,
``overall_confidence``, and merged ``field_confidence`` only; does **not** change
``is_spam`` or ``spam_score`` so prior values are preserved.

Requires non-null ``company_id`` on the target row; otherwise skips with a log line.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from agents.enrichment.classifiers.spam_preview import apply_spam_tiers

log = structlog.get_logger()

_RESOLVE_JOB_POSTING_SQL = text(
    """
    SELECT jp.job_posting_id::text AS job_posting_id,
           jp.company_id::text AS company_id
    FROM dbo.job_postings jp
    INNER JOIN dbo.normalized_jobs nj
        ON jp.source IS NOT NULL
        AND jp.external_id IS NOT NULL
        AND nj.source = jp.source
        AND nj.external_id = jp.external_id
    WHERE nj.id = :nj_id
    LIMIT 1
    """
)

_UPDATE_UNCERTAIN_SQL = text(
    """
    UPDATE dbo.job_postings SET
        quality_score = :quality_score,
        overall_confidence = :overall_confidence,
        field_confidence = CAST(:field_confidence AS jsonb)
    WHERE job_posting_id::text = :job_posting_id
    """
)

_UPDATE_CLEAN_SQL = text(
    """
    UPDATE dbo.job_postings SET
        quality_score = :quality_score,
        overall_confidence = :overall_confidence,
        field_confidence = CAST(:field_confidence AS jsonb),
        is_spam = FALSE,
        spam_score = :spam_score
    WHERE job_posting_id::text = :job_posting_id
    """
)

_UPDATE_FLAGGED_SQL = text(
    """
    UPDATE dbo.job_postings SET
        quality_score = :quality_score,
        overall_confidence = :overall_confidence,
        field_confidence = CAST(:field_confidence AS jsonb),
        is_spam = NULL,
        spam_score = :spam_score
    WHERE job_posting_id::text = :job_posting_id
    """
)


def resolve_job_posting_row(session: Session, normalized_job_id: int) -> dict[str, Any] | None:
    """Return ``job_posting_id`` and ``company_id`` text, or None if not found."""
    row = session.execute(_RESOLVE_JOB_POSTING_SQL, {"nj_id": normalized_job_id}).mappings().first()
    return dict(row) if row else None


def merge_field_confidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    """Merge spam ``field_confidence`` with ``quality_components`` for JSONB storage."""
    fc: dict[str, Any] = dict(payload.get("field_confidence") or {})
    qc = payload.get("quality_components") or {}
    if isinstance(qc, dict):
        for key, val in qc.items():
            try:
                fc[f"quality:{key}"] = float(val)
            except (TypeError, ValueError):
                continue
    return fc


def _overall_confidence_for_storage(payload: dict[str, Any]) -> float | None:
    oc = payload.get("overall_confidence")
    if oc is not None:
        try:
            return float(oc)
        except (TypeError, ValueError):
            pass
    qs = payload.get("quality_score")
    if qs is not None:
        try:
            return float(qs)
        except (TypeError, ValueError):
            pass
    return None


def apply_enrichment_to_job_postings(
    session: Session,
    normalized_job_id: int,
    record_enriched_payload: dict[str, Any],
) -> bool:
    """
    Apply enrichment columns to ``job_postings`` when tier allows.

    Returns True if an ``UPDATE`` ran, False if skipped (no row, no company_id,
    rejected tier, or missing quality score when needed).
    """
    resolved = resolve_job_posting_row(session, normalized_job_id)
    if not resolved:
        log.info(
            "enrichment_promotion_no_job_posting",
            normalized_job_id=normalized_job_id,
        )
        return False

    job_posting_id = resolved.get("job_posting_id")
    company_id = resolved.get("company_id")
    if not job_posting_id or not str(company_id).strip():
        log.warning(
            "enrichment_promotion_skipped_no_company_id",
            normalized_job_id=normalized_job_id,
        )
        return False

    raw_tier = record_enriched_payload.get("spam_tier")
    tier = (raw_tier or "").strip().lower() if isinstance(raw_tier, str) else ""
    spam_score = record_enriched_payload.get("spam_score")

    if isinstance(spam_score, (int, float)) and tier not in (
        "clean",
        "flagged",
        "rejected",
        "uncertain",
    ):
        _, derived = apply_spam_tiers(float(spam_score))
        tier = derived

    if tier == "rejected":
        log.info(
            "enrichment_promotion_skipped_rejected_spam",
            normalized_job_id=normalized_job_id,
            job_posting_id=job_posting_id,
        )
        return False

    quality_score = record_enriched_payload.get("quality_score")
    if quality_score is None:
        log.info(
            "enrichment_promotion_skipped_no_quality_score",
            normalized_job_id=normalized_job_id,
        )
        return False

    try:
        qs_f = float(quality_score)
    except (TypeError, ValueError):
        return False

    fc_merged = merge_field_confidence_for_storage(record_enriched_payload)
    fc_json = json.dumps(fc_merged)
    oc = _overall_confidence_for_storage(record_enriched_payload)

    params_base: dict[str, Any] = {
        "job_posting_id": str(job_posting_id),
        "quality_score": qs_f,
        "overall_confidence": oc,
        "field_confidence": fc_json,
    }

    if tier == "uncertain" or spam_score is None:
        session.execute(_UPDATE_UNCERTAIN_SQL, params_base)
        log.info(
            "enrichment_promotion_applied_uncertain_spam",
            normalized_job_id=normalized_job_id,
            job_posting_id=job_posting_id,
        )
        return True

    try:
        spam_f = float(spam_score)
    except (TypeError, ValueError):
        session.execute(_UPDATE_UNCERTAIN_SQL, params_base)
        log.info(
            "enrichment_promotion_applied_uncertain_spam_invalid_score",
            normalized_job_id=normalized_job_id,
            job_posting_id=job_posting_id,
        )
        return True

    params = {**params_base, "spam_score": spam_f}

    if tier == "flagged":
        session.execute(_UPDATE_FLAGGED_SQL, params)
        log.info(
            "enrichment_promotion_applied_flagged",
            normalized_job_id=normalized_job_id,
            job_posting_id=job_posting_id,
        )
        return True

    if tier == "clean":
        session.execute(_UPDATE_CLEAN_SQL, params)
        log.info(
            "enrichment_promotion_applied_clean",
            normalized_job_id=normalized_job_id,
            job_posting_id=job_posting_id,
        )
        return True

    log.warning(
        "enrichment_promotion_unhandled_tier",
        normalized_job_id=normalized_job_id,
        tier=tier or raw_tier,
    )
    return False
