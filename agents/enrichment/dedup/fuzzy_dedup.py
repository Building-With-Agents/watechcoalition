"""Fuzzy near-duplicate detection (embedding cosine similarity). IMP-018."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from agents.enrichment.dedup.completeness import completeness_score, publish_date_for_tiebreak
from agents.enrichment.dedup.config import DEDUP_ROLLING_WINDOW_DAYS, dedup_cosine_threshold
from agents.enrichment.dedup.text import build_dedup_text, dedup_text_hash, row_requirements_fallback
from agents.enrichment.dedup.types import FuzzyDedupResult
from agents.enrichment.dedup.vectors import cosine_similarity, parse_stored_embedding, vector_to_pg_cast_param
from agents.skills_extraction.extractors.taxonomy import _embed_texts_azure

log = structlog.get_logger()

_DEDUP_AUDIT_AGENT = "enrichment-dedup"

_LOAD_CURRENT_SQL = text(
    """
    SELECT
        jp.job_posting_id::text AS job_posting_id,
        jp.company_id::text AS company_id,
        jp.publish_date AS publish_date,
        jp.job_title AS job_title,
        jp.job_description AS job_description,
        jp.salary_range AS salary_range,
        jp.location AS location,
        jp.zip AS zip,
        jp.county AS county,
        jp.source AS source,
        jp.external_id AS external_id,
        jp.is_duplicate AS is_duplicate,
        jp.duplicate_cluster_id AS duplicate_cluster_id,
        jp.dedup_text_hash AS dedup_text_hash,
        jp.dedup_embedding::text AS dedup_embedding_text,
        c.company_name AS company_name,
        nj.requirements AS requirements
    FROM dbo.job_postings jp
    LEFT JOIN dbo.companies c ON c.company_id::text = jp.company_id::text
    LEFT JOIN dbo.normalized_jobs nj
        ON jp.source IS NOT NULL
        AND jp.external_id IS NOT NULL
        AND nj.source = jp.source
        AND nj.external_id = jp.external_id
    WHERE jp.job_posting_id::text = :job_posting_id
    LIMIT 1
    """
)

_LIST_SURVIVORS_SQL = text(
    """
    SELECT
        jp.job_posting_id::text AS job_posting_id,
        jp.duplicate_cluster_id AS duplicate_cluster_id,
        jp.dedup_embedding::text AS dedup_embedding_text,
        jp.salary_range AS salary_range,
        jp.location AS location,
        jp.zip AS zip,
        jp.county AS county,
        jp.job_description AS job_description,
        jp.publish_date AS publish_date
    FROM dbo.job_postings jp
    WHERE jp.company_id::text = :company_id
        AND (jp.is_duplicate IS NOT TRUE)
        AND jp.publish_date >= :window_start
        AND jp.publish_date < :anchor
        AND jp.job_posting_id::text <> :job_posting_id
        AND jp.dedup_embedding IS NOT NULL
    """
)

_UPDATE_DEDUP_CACHE_SQL = text(
    """
    UPDATE dbo.job_postings SET
        dedup_text_hash = :dedup_text_hash,
        dedup_embedding = CAST(:dedup_embedding AS vector)
    WHERE job_posting_id::text = :job_posting_id
    """
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _unique_result() -> FuzzyDedupResult:
    return FuzzyDedupResult(
        is_duplicate=False,
        duplicate_cluster_id=None,
        matched_job_posting_id=None,
        survivor_job_posting_id=None,
        stub=False,
    )


def _current_row_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Subset of keys used by completeness scoring for the anchor posting."""
    return {
        "salary_range": row.get("salary_range"),
        "location": row.get("location"),
        "zip": row.get("zip"),
        "county": row.get("county"),
        "job_description": row.get("job_description"),
        "publish_date": row.get("publish_date"),
    }


def run_fuzzy_dedup(
    session: Session,
    job_posting_id: str,
    *,
    threshold: float | None = None,
) -> FuzzyDedupResult:
    """
    Compare one posting's embedding against same-company survivors in the rolling window.

    Persists ``dedup_text_hash`` and ``dedup_embedding`` on success; duplicate flags are
    applied by ``job_postings_promotion.apply_fuzzy_dedup_result``.
    """
    effective_threshold = dedup_cosine_threshold() if threshold is None else threshold
    jid = (job_posting_id or "").strip()
    if not jid:
        log.warning("fuzzy_dedup_invalid_job_posting_id")
        return _unique_result()

    row = session.execute(_LOAD_CURRENT_SQL, {"job_posting_id": jid}).mappings().first()
    if not row:
        log.info("fuzzy_dedup_job_posting_not_found", job_posting_id=jid)
        return _unique_result()
    current: dict[str, Any] = dict(row)

    company_id = (current.get("company_id") or "").strip()
    if not company_id:
        log.warning("fuzzy_dedup_missing_company_id", job_posting_id=jid)
        return _unique_result()

    anchor_raw = current.get("publish_date")
    if anchor_raw is None:
        log.info("fuzzy_dedup_missing_publish_date", job_posting_id=jid)
        return _unique_result()
    if not isinstance(anchor_raw, datetime):
        log.info("fuzzy_dedup_publish_date_unexpected_type", job_posting_id=jid)
        return _unique_result()

    anchor = _ensure_utc(anchor_raw)
    window_start = anchor - timedelta(days=DEDUP_ROLLING_WINDOW_DAYS)

    body_source = row_requirements_fallback(current)
    dedup_plain = build_dedup_text(
        current.get("job_title"),
        current.get("company_name"),
        body_source,
    )
    if not dedup_plain.strip():
        log.info("fuzzy_dedup_empty_dedup_text", job_posting_id=jid)
        return _unique_result()

    text_hash = dedup_text_hash(dedup_plain)
    stored_hash = current.get("dedup_text_hash")
    stored_emb_text = current.get("dedup_embedding_text")
    current_vec = parse_stored_embedding(stored_emb_text)

    used_cache = (
        stored_hash == text_hash
        and current_vec is not None
        and current_vec.size > 0
    )

    if not used_cache:
        vectors = _embed_texts_azure([dedup_plain], audit_agent_name=_DEDUP_AUDIT_AGENT)
        if not vectors or len(vectors) != 1:
            log.warning("fuzzy_dedup_embedding_failed", job_posting_id=jid)
            return _unique_result()
        raw_vec = vectors[0]
        current_vec = parse_stored_embedding(raw_vec)
        if current_vec is None or current_vec.size == 0:
            log.warning("fuzzy_dedup_embedding_parse_failed", job_posting_id=jid)
            return _unique_result()
        try:
            session.execute(
                _UPDATE_DEDUP_CACHE_SQL,
                {
                    "job_posting_id": jid,
                    "dedup_text_hash": text_hash,
                    "dedup_embedding": vector_to_pg_cast_param([float(x) for x in current_vec.tolist()]),
                },
            )
        except Exception as exc:
            log.warning(
                "fuzzy_dedup_dedup_cache_update_failed",
                job_posting_id=jid,
                error=str(exc),
            )
            return _unique_result()

    survivors = session.execute(
        _LIST_SURVIVORS_SQL,
        {
            "company_id": company_id,
            "window_start": window_start,
            "anchor": anchor,
            "job_posting_id": jid,
        },
    ).mappings().all()

    best_sim = -1.0
    best_row: dict[str, Any] | None = None
    for srow in survivors:
        sd = dict(srow)
        svec = parse_stored_embedding(sd.get("dedup_embedding_text"))
        if svec is None or svec.size == 0:
            continue
        sim = cosine_similarity(current_vec, svec)
        if sim > best_sim:
            best_sim = sim
            best_row = sd

    log.info(
        "fuzzy_dedup_candidates_evaluated",
        job_posting_id=jid,
        candidates_compared=len(survivors),
        best_similarity=round(best_sim, 6) if best_row else None,
        threshold=effective_threshold,
        used_embedding_cache=used_cache,
    )

    if best_row is None or best_sim < effective_threshold:
        return _unique_result()

    cur_c = completeness_score(_current_row_dict(current))
    sur_c = completeness_score(best_row)
    cur_pd = publish_date_for_tiebreak(_current_row_dict(current))
    sur_pd = publish_date_for_tiebreak(best_row)

    current_wins = cur_c > sur_c or (
        cur_c == sur_c and cur_pd is not None and (sur_pd is None or cur_pd >= sur_pd)
    )

    matched_id = str(best_row["job_posting_id"])
    cluster_base = best_row.get("duplicate_cluster_id")
    cluster_id = str(cluster_base).strip() if cluster_base else None
    if not cluster_id:
        cluster_id = str(uuid.uuid4())

    if current_wins:
        log.info(
            "fuzzy_dedup_merge_outcome",
            job_posting_id=jid,
            outcome="current_survivor",
            matched_job_posting_id=matched_id,
            duplicate_cluster_id=cluster_id,
            best_similarity=round(best_sim, 6),
        )
        return FuzzyDedupResult(
            is_duplicate=False,
            duplicate_cluster_id=cluster_id,
            matched_job_posting_id=matched_id,
            survivor_job_posting_id=jid,
            stub=False,
        )

    log.info(
        "fuzzy_dedup_merge_outcome",
        job_posting_id=jid,
        outcome="matched_survivor",
        matched_job_posting_id=matched_id,
        duplicate_cluster_id=cluster_id,
        best_similarity=round(best_sim, 6),
    )
    return FuzzyDedupResult(
        is_duplicate=True,
        duplicate_cluster_id=cluster_id,
        matched_job_posting_id=matched_id,
        survivor_job_posting_id=matched_id,
        stub=False,
    )
