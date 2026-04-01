"""Persist Phase 1 enrichment columns to ``dbo.job_postings`` (Decision #8 gating).

Resolves the posting row via ``normalized_jobs.id`` + matching ``source`` /
``external_id``. **Rejected** spam tier (``spam_score > SPAM_REJECT_THRESHOLD``):
no ``UPDATE`` — the row may already exist from upstream ingestion; enrichment
columns are left unchanged.

**Uncertain / degraded** (no numeric ``spam_score``): updates ``quality_score``,
``overall_confidence``, and merged ``field_confidence`` only; does **not** change
``is_spam`` or ``spam_score`` so prior values are preserved.

Successful clean / flagged / uncertain promotions then run best-effort fuzzy
dedup in the same session. Dedup failures log and return without rolling back
the enrichment update.

Requires non-null ``company_id`` on the target row; otherwise skips with a log line.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from agents.enrichment.classifiers.spam_preview import apply_spam_tiers
from agents.enrichment.dedup import run_fuzzy_dedup
from agents.enrichment.dedup.types import FuzzyDedupResult

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

_UPDATE_FUZZY_DEDUP_SQL = text(
    """
    UPDATE dbo.job_postings SET
        is_duplicate = :is_duplicate,
        duplicate_cluster_id = :duplicate_cluster_id
    WHERE job_posting_id::text = :job_posting_id
    """
)

_LOAD_FUZZY_DEDUP_STATE_SQL = text(
    """
    SELECT
        jp.is_duplicate AS is_duplicate,
        jp.duplicate_cluster_id AS duplicate_cluster_id
    FROM dbo.job_postings jp
    WHERE jp.job_posting_id::text = :job_posting_id
    LIMIT 1
    """
)

_LIST_CLUSTER_MEMBER_IDS_SQL = text(
    """
    SELECT jp.job_posting_id::text AS job_posting_id
    FROM dbo.job_postings jp
    WHERE jp.duplicate_cluster_id = :duplicate_cluster_id
        AND jp.job_posting_id::text <> :job_posting_id
    ORDER BY jp.job_posting_id::text
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


def _load_existing_fuzzy_dedup_state(session: Session, job_posting_id: str) -> dict[str, Any]:
    row = session.execute(
        _LOAD_FUZZY_DEDUP_STATE_SQL,
        {"job_posting_id": job_posting_id},
    ).mappings().first()
    return dict(row) if row else {}


def _cluster_member_ids(session: Session, cluster_id: str, *, exclude_job_posting_id: str) -> list[str]:
    rows = session.execute(
        _LIST_CLUSTER_MEMBER_IDS_SQL,
        {
            "duplicate_cluster_id": cluster_id,
            "job_posting_id": exclude_job_posting_id,
        },
    ).mappings().all()
    return [str(row["job_posting_id"]) for row in rows]


def apply_fuzzy_dedup_result(
    session: Session,
    job_posting_id: str,
    result: FuzzyDedupResult,
) -> bool:
    """
    Persist fuzzy-dedup state for the current row and any matched survivor row.

    ``run_fuzzy_dedup`` may write ``dedup_text_hash`` / ``dedup_embedding`` (cache
    for the anchor and lazily backfilled survivors). This helper is the **only**
    path that updates ``is_duplicate`` and ``duplicate_cluster_id``.
    """
    if result.stub:
        log.info("fuzzy_dedup_persistence_skipped_stub", job_posting_id=job_posting_id)
        return False

    cluster_id = result.duplicate_cluster_id
    matched_id = result.matched_job_posting_id
    survivor_id = result.survivor_job_posting_id

    if cluster_id is None:
        existing = _load_existing_fuzzy_dedup_state(session, job_posting_id)
        prior_cluster_id = existing.get("duplicate_cluster_id")
        prior_cluster = str(prior_cluster_id).strip() if prior_cluster_id else None
        prior_was_survivor = existing.get("is_duplicate") is False and prior_cluster is not None
        if result.is_duplicate:
            raise ValueError("duplicate fuzzy dedup results must include duplicate_cluster_id")
        if matched_id or survivor_id:
            raise ValueError("non-duplicate fuzzy dedup results may not include cluster or survivor metadata")
        session.execute(
            _UPDATE_FUZZY_DEDUP_SQL,
            {
                "job_posting_id": job_posting_id,
                "is_duplicate": False,
                "duplicate_cluster_id": None,
            },
        )
        cleared_peer_count = 0
        if prior_was_survivor:
            peer_ids = _cluster_member_ids(
                session,
                prior_cluster,
                exclude_job_posting_id=job_posting_id,
            )
            for peer_id in peer_ids:
                session.execute(
                    _UPDATE_FUZZY_DEDUP_SQL,
                    {
                        "job_posting_id": peer_id,
                        "is_duplicate": False,
                        "duplicate_cluster_id": None,
                    },
                )
            cleared_peer_count = len(peer_ids)
        log.info(
            "fuzzy_dedup_persisted_unique",
            job_posting_id=job_posting_id,
            cleared_prior_cluster=prior_was_survivor,
            cleared_peer_count=cleared_peer_count,
        )
        return True

    effective_survivor_id = survivor_id or (job_posting_id if not result.is_duplicate else None)
    if effective_survivor_id is None:
        raise ValueError("duplicate fuzzy dedup results must include survivor_job_posting_id")
    if result.is_duplicate and effective_survivor_id == job_posting_id:
        raise ValueError("duplicate fuzzy dedup results cannot mark the current row as survivor")
    if not result.is_duplicate and effective_survivor_id != job_posting_id:
        raise ValueError("non-duplicate clustered results must keep the current row as survivor")

    session.execute(
        _UPDATE_FUZZY_DEDUP_SQL,
        {
            "job_posting_id": job_posting_id,
            "is_duplicate": result.is_duplicate,
            "duplicate_cluster_id": cluster_id,
        },
    )

    peer_ids = {peer_id for peer_id in (matched_id, effective_survivor_id) if peer_id and peer_id != job_posting_id}
    for peer_id in sorted(peer_ids):
        session.execute(
            _UPDATE_FUZZY_DEDUP_SQL,
            {
                "job_posting_id": peer_id,
                "is_duplicate": peer_id != effective_survivor_id,
                "duplicate_cluster_id": cluster_id,
            },
        )

    log.info(
        "fuzzy_dedup_persisted_cluster",
        job_posting_id=job_posting_id,
        duplicate_cluster_id=cluster_id,
        is_duplicate=result.is_duplicate,
        survivor_job_posting_id=effective_survivor_id,
        matched_job_posting_id=matched_id,
        updated_peer_count=len(peer_ids),
    )
    return True


def _apply_fuzzy_dedup_after_promotion(
    session: Session,
    *,
    normalized_job_id: int,
    job_posting_id: str,
) -> None:
    """Best-effort fuzzy dedup: isolate failures so promotion writes still commit."""
    try:
        # Keep dedup best-effort by containing all reads/writes in a savepoint.
        # A dedup SQLAlchemy/DB error should roll back only the dedup work, not
        # poison the outer promotion transaction managed by ``session_scope``.
        with session.begin_nested():
            result = run_fuzzy_dedup(session, job_posting_id)
            apply_fuzzy_dedup_result(session, job_posting_id, result)
    except Exception as exc:
        log.warning(
            "fuzzy_dedup_after_promotion_failed",
            normalized_job_id=normalized_job_id,
            job_posting_id=job_posting_id,
            error=str(exc),
        )


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
    else:
        try:
            spam_f = float(spam_score)
        except (TypeError, ValueError):
            session.execute(_UPDATE_UNCERTAIN_SQL, params_base)
            log.info(
                "enrichment_promotion_applied_uncertain_spam_invalid_score",
                normalized_job_id=normalized_job_id,
                job_posting_id=job_posting_id,
            )
        else:
            params = {**params_base, "spam_score": spam_f}

            if tier == "flagged":
                session.execute(_UPDATE_FLAGGED_SQL, params)
                log.info(
                    "enrichment_promotion_applied_flagged",
                    normalized_job_id=normalized_job_id,
                    job_posting_id=job_posting_id,
                )
            elif tier == "clean":
                session.execute(_UPDATE_CLEAN_SQL, params)
                log.info(
                    "enrichment_promotion_applied_clean",
                    normalized_job_id=normalized_job_id,
                    job_posting_id=job_posting_id,
                )
            else:
                log.warning(
                    "enrichment_promotion_unhandled_tier",
                    normalized_job_id=normalized_job_id,
                    tier=tier or raw_tier,
                )
                return False

    _apply_fuzzy_dedup_after_promotion(
        session,
        normalized_job_id=normalized_job_id,
        job_posting_id=str(job_posting_id),
    )
    return True
