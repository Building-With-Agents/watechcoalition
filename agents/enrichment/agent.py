"""
Enrichment Agent — Phase 1 lite (Pair C: classification + quality + spam; Pair D: resolvers).

When ``SkillsExtracted`` includes a non-empty ``records`` list, applies Pair C gating and
Pair D resolution per row, then emits one batch-level ``RecordEnriched`` (Week 5 counts +
Week 6 distributions) via :func:`build_record_enriched_event`.

Otherwise (flat single-record payloads), loads reference labels from ``technology_areas`` and
``industry_sectors`` when ``PYTHON_DATABASE_URL`` is set; uses
``classification.FALLBACK_TECH_AREA_LABELS`` for offline runs; emits a per-record
``RecordEnriched`` with role, seniority, quality, and spam preview fields.

When ``check_db_connection()`` is true, batch mode opens one ``session_scope()`` for the
whole batch so ``resolve_company`` / ``resolve_location`` use the real dbo session.

Agent ID (canonical): enrichment-agent
Emits:    RecordEnriched
          EnrichmentDegraded (alert bus, when registered)
Consumes: SkillsExtracted

When the inbound payload includes ``normalized_job_id`` (int) and ``PYTHON_DATABASE_URL``
is set, spam scoring loads the latest ``dbo.extracted_intelligence`` row and calls
``score_spam_preview``. Otherwise ``spam_score`` / ``is_spam`` come from the
walking-skeleton fixture keyed by ``posting_id``.

When the normalized job resolves to a ``job_postings`` row, the emitted
``RecordEnriched`` payload also includes ``temporal_period`` and
``borderplex_subregion`` derived from normalized-job context so the live
event output matches the promotion/write path.

With ``normalized_job_id`` and a resolvable ``job_postings`` row (join on
``source``/``external_id``), Phase 1 enrichment columns are persisted via
:mod:`agents.enrichment.job_postings_promotion`. **Rejected** spam tier skips
``UPDATE`` entirely. **Uncertain** (degraded classifier) updates quality fields
only and leaves ``is_spam``/``spam_score`` unchanged.

Fixture: agents/data/fixtures/fixture_enriched.json — supplies ``company`` /
``company_id`` / ``sector_id`` when not on the event; role, seniority, and
``quality_score`` are always computed (not taken from the fixture). Spam
scores use the fixture only when ``normalized_job_id`` is absent or DB is
unconfigured.

CLI: ``python -m agents.enrichment.agent --limit 50`` (loads repo-root ``.env`` via
python-dotenv, then requires ``PYTHON_DATABASE_URL``).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import structlog
from dotenv import load_dotenv
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from agents.common.base_agent import BaseAgent
from agents.common.data_store.database import check_db_connection, session_scope
from agents.common.data_store.models import IndustrySector, NormalizedJob, TechnologyArea
from agents.common.event_envelope import EventEnvelope
from agents.common.llm_client import invoke_skills_llm
from agents.common.types.job_profile import EmployerProfile
from agents.enrichment.adapters.facade import ExternalEnrichmentFacade
from agents.enrichment.async_bridge import run_coroutine
from agents.enrichment.classification import (
    FALLBACK_TECH_AREA_LABELS,
    classify_job,
)
from agents.enrichment.classifiers.employer_classifier import (
    build_employer_profile,
    persist_employer_metadata,
)
from agents.enrichment.classifiers.naics_classifier import classify_naics
from agents.enrichment.classifiers.quality import score_quality
from agents.enrichment.classifiers.soc_classifier import classify_soc
from agents.enrichment.classifiers.spam_preview import (
    SpamPreviewResult,
    apply_spam_tiers,
    score_spam_preview,
)
from agents.enrichment.job_postings_promotion import (
    apply_enrichment_to_job_postings,
    derive_enrichment_output_fields,
    resolve_job_posting_row,
)
from agents.enrichment.resolvers.company_resolver import resolve_company
from agents.enrichment.resolvers.confidence import (
    compute_field_confidence,
    compute_overall_confidence,
)
from agents.enrichment.resolvers.events import build_record_enriched_event
from agents.enrichment.resolvers.location_resolver import resolve_location
from agents.enrichment.resolvers.sector_resolver import resolve_sector
from agents.enrichment.schemas import EnrichedJobProfile
from agents.scripts.jsearch_enrichment_preview_lib import build_extraction_dict

log = structlog.get_logger()


def _enrichment_soc_llm() -> Callable[[str], str]:
    """Sync callable for :func:`classify_soc`; Azure OpenAI via :func:`invoke_skills_llm`."""

    def llm(prompt: str) -> str:
        try:
            text, meta = invoke_skills_llm(
                prompt,
                agent_name="enrichment-soc-classifier",
            )
        except TypeError as exc:
            if "api_key" in str(exc).lower() or "auth" in str(exc).lower():
                log.warning("soc_llm_auth_failed", error=str(exc))
                return "unclassified"
            raise
        if not meta.get("success") or meta.get("extraction_failed"):
            log.warning(
                "enrichment_soc_llm_call_failed",
                success=meta.get("success"),
                extraction_failed=meta.get("extraction_failed"),
                error_reason=meta.get("error_reason"),
            )
            return "unclassified"
        return (text or "").strip()

    return llm


_alert_bus: Any = None

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENV_PATH = _REPO_ROOT / ".env"


def _load_repo_dotenv() -> None:
    """Load repo-root ``.env`` once. Does not override variables already set in the OS env."""
    load_dotenv(_ENV_PATH, override=False)


_FIXTURE_PATH = Path(__file__).parent.parent / "data" / "fixtures" / "fixture_enriched.json"

_LATEST_EI_BY_NJ_ID_SQL = text(
    """
    SELECT
        skills,
        tools,
        tasks,
        responsibilities,
        context,
        COALESCE(extraction_failed, false) AS extraction_failed
    FROM dbo.extracted_intelligence
    WHERE normalized_job_id = :nj_id
    ORDER BY extracted_at DESC NULLS LAST, id DESC
    LIMIT 1
    """
)


_LATEST_EI_SQL = text(
    """
    WITH latest_ei AS (
        SELECT DISTINCT ON (normalized_job_id)
            normalized_job_id,
            skills,
            tools,
            tasks,
            responsibilities,
            context
        FROM dbo.extracted_intelligence
        WHERE normalized_job_id IS NOT NULL
        ORDER BY normalized_job_id, extracted_at DESC NULLS LAST, id DESC
    )
    SELECT
        jp.job_posting_id::text AS job_posting_id,
        jp.job_title,
        jp.job_description,
        jp.source,
        jp.external_id,
        COALESCE(jp.is_internship, false) AS is_internship,
        le.skills,
        le.tools,
        le.tasks,
        le.responsibilities,
        le.context
    FROM dbo.job_postings jp
    LEFT JOIN dbo.normalized_jobs nj
        ON jp.source IS NOT NULL
        AND jp.external_id IS NOT NULL
        AND nj.source = jp.source
        AND nj.external_id = jp.external_id
    LEFT JOIN latest_ei le ON le.normalized_job_id = nj.id
    ORDER BY jp.job_posting_id
    LIMIT :lim
    """
)


def _db_url_configured() -> bool:
    return bool(os.getenv("PYTHON_DATABASE_URL"))


def register_alert_bus(bus: Any | None) -> None:
    """Register the event bus so EnrichmentDegraded can be published."""
    global _alert_bus
    _alert_bus = bus


def _coerce_normalized_job_id(raw: Any) -> int | None:
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    return None


def _spam_from_preview_result(result: SpamPreviewResult) -> dict[str, Any]:
    out: dict[str, Any] = {
        "spam_score": result.spam_score,
        "is_spam": result.is_spam,
        "spam_tier": result.tier,
        "field_confidence": dict(result.field_confidence),
        "overall_confidence": result.overall_confidence,
        "spam_rationale": result.rationale,
        "spam_extraction_note": result.extraction_note,
        "spam_degraded": result.degraded,
        "spam_used_heuristic": result.used_heuristic,
    }
    return out


def _degraded_spam_result(*, extraction_note: str | None) -> SpamPreviewResult:
    return SpamPreviewResult(
        spam_score=None,
        is_spam=None,
        tier="uncertain",
        field_confidence={},
        overall_confidence=None,
        rationale=None,
        degraded=True,
        extraction_note=extraction_note,
        used_heuristic=False,
    )


def _emit_enrichment_degraded(
    *,
    correlation_id: str,
    posting_id: Any,
    normalized_job_id: int | None,
    triggered_by_event_type: Any,
    reason: str,
    extraction_note: str | None,
) -> None:
    message = "Spam classification degraded; record continued with null spam fields."
    log.warning(
        "EnrichmentDegraded",
        posting_id=posting_id,
        normalized_job_id=normalized_job_id,
        reason=reason,
        extraction_note=extraction_note,
        message=message,
    )
    if _alert_bus is None:
        return
    try:
        event = EventEnvelope(
            correlation_id=correlation_id,
            agent_id="enrichment-agent",
            payload={
                "event_type": "EnrichmentDegraded",
                "posting_id": posting_id,
                "normalized_job_id": normalized_job_id,
                "triggered_by_event_type": triggered_by_event_type,
                "classifier": "spam_preview",
                "reason": reason,
                "degraded_fields": [
                    "spam_score",
                    "is_spam",
                    "field_confidence",
                    "overall_confidence",
                ],
                "extraction_note": extraction_note,
                "message": message,
            },
        )
        _alert_bus.publish(event)
    except Exception as exc:
        log.warning(
            "EnrichmentDegraded_publish_failed",
            posting_id=posting_id,
            normalized_job_id=normalized_job_id,
            error=str(exc),
        )


SpamBucket = Literal["rejected", "flagged", "proceed"]


def _records_from_skills_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Rows from ``records`` only (batch path caller ensures non-empty list)."""
    raw = payload.get("records")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        out.append(dict(item) if isinstance(item, dict) else {})
    return out


def _spam_bucket(record: dict[str, Any]) -> SpamBucket:
    if "is_spam" in record:
        if record["is_spam"] is True:
            return "rejected"
        if record["is_spam"] is None:
            return "flagged"
    spam_score = record.get("spam_score")
    if spam_score is not None:
        try:
            s = float(spam_score)
        except (TypeError, ValueError):
            return "proceed"
        if s > 0.9:
            return "rejected"
        if s >= 0.7:
            return "flagged"
    return "proceed"


def _distribution_bucket(value: Any) -> str:
    if value is None:
        return "unknown"
    s = str(value).strip()
    return s if s else "unknown"


_EXTRA_POSTING_KEYS = frozenset(
    {
        "soc_code",
        "naics_code",
        "employer_metadata",
        "temporal_period",
        "borderplex_subregion",
        "is_duplicate",
        "duplicate_cluster_id",
        "matched_job_posting_id",
        "survivor_job_posting_id",
        "stub",
    }
)


def _rollup_fuzzy_dedup_signals(
    enriched: dict[str, Any],
    posting: dict[str, Any],
) -> tuple[int, int, int]:
    """Return (stub_inc, cluster_row_inc, matched_inc) per row, each 0 or 1."""
    stub_inc = int(
        enriched.get("stub") is True or enriched.get("fuzzy_dedup_stub") is True or posting.get("stub") is True
    )

    def _has_cluster(d: dict[str, Any]) -> bool:
        v = d.get("duplicate_cluster_id")
        return v is not None and bool(str(v).strip())

    cluster_inc = int(_has_cluster(enriched) or _has_cluster(posting))
    mid = enriched.get("matched_job_posting_id") or posting.get("matched_job_posting_id")
    matched_inc = int(mid is not None and bool(str(mid).strip()))
    return stub_inc, cluster_inc, matched_inc


def _posting_for_enrichment(
    record: dict[str, Any],
    batch_payload: dict[str, Any],
) -> dict[str, Any]:
    def pick(key: str, default: Any = None) -> Any:
        if key in record and record[key] is not None:
            return record[key]
        return batch_payload.get(key, default)

    base: dict[str, Any] = {
        "posting_id": pick("posting_id"),
        "title": pick("title"),
        "company": pick("company"),
        "description": pick("description", None),
        "location": pick("location", "") or "",
        "normalized_job_id": pick("normalized_job_id"),
        "source": pick("source"),
        "external_id": pick("external_id"),
        "quality_score": pick("quality_score"),
        "spam_score": pick("spam_score"),
        "is_spam": pick("is_spam"),
        "seniority": pick("seniority"),
        "role_classification": pick("role_classification"),
        "skills": pick("skills", []) or [],
        "seniority_confidence": 0.90 if pick("seniority") is not None else 0.0,
        "extraction_confidence": pick("extraction_confidence"),
        "taxonomy_coverage": pick("taxonomy_coverage"),
    }
    for k in _EXTRA_POSTING_KEYS:
        v = pick(k, None)
        if v is not None:
            base[k] = v
    return base


def _job_postings_promotion_payload(
    enriched: dict[str, Any],
    posting: dict[str, Any],
) -> dict[str, Any]:
    """Build a payload for :func:`apply_enrichment_to_job_postings` from batch enrichment output."""
    spam_score = enriched.get("spam_score")
    if spam_score is None:
        spam_score = posting.get("spam_score")
    spam_tier = enriched.get("spam_tier")
    if spam_tier is None:
        spam_tier = posting.get("spam_tier")
    if not spam_tier and isinstance(spam_score, (int, float)):
        _, spam_tier = apply_spam_tiers(float(spam_score))
    quality_score = enriched.get("quality_score")
    if quality_score is None:
        quality_score = posting.get("quality_score")
    return {
        "spam_tier": spam_tier,
        "spam_score": spam_score,
        "quality_score": quality_score,
        "overall_confidence": enriched.get("overall_confidence"),
        "field_confidence": enriched.get("field_confidence"),
        "naics_code": enriched.get("naics_code"),
        "soc_code": enriched.get("soc_code"),
    }


class EnrichmentAgent(BaseAgent):
    """Deterministic enrichment: role + seniority; batch Pair D when ``records`` is set."""

    @property
    def agent_id(self) -> str:
        return "enrichment-agent"

    def __init__(self, external_facade: ExternalEnrichmentFacade | None = None) -> None:
        self._fixture: dict[int, dict] = {}
        self._refs: tuple[list[tuple[str, str]], list[tuple[str, str]]] | None = None
        self._external_facade = external_facade or ExternalEnrichmentFacade()

    @staticmethod
    def _load_reference_labels(session: Session) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        tech_rows = session.execute(select(TechnologyArea.id, TechnologyArea.title)).all()
        technology_areas = [(str(r[0]), str(r[1])) for r in tech_rows]
        sec_rows = session.execute(select(IndustrySector.industry_sector_id, IndustrySector.sector_title)).all()
        industry_sectors = [(str(r[0]), str(r[1])) for r in sec_rows]
        return technology_areas, industry_sectors

    def _ensure_refs(self) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        if self._refs is not None:
            return self._refs
        if not _db_url_configured():
            self._refs = (list(FALLBACK_TECH_AREA_LABELS), [])
            return self._refs
        try:
            with session_scope() as session:
                self._refs = self._load_reference_labels(session)
        except Exception as exc:
            log.warning("enrichment_reference_load_failed", error=str(exc))
            self._refs = (list(FALLBACK_TECH_AREA_LABELS), [])
        return self._refs

    def health_check(self) -> dict:
        metrics: dict = {}
        if not _db_url_configured():
            return {
                "status": "degraded",
                "agent": self.agent_id,
                "last_run": None,
                "metrics": {**metrics, "reason": "PYTHON_DATABASE_URL not set"},
            }
        if check_db_connection():
            return {
                "status": "ok",
                "agent": self.agent_id,
                "last_run": None,
                "metrics": metrics,
            }
        return {
            "status": "down",
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {**metrics, "reason": "database_unreachable"},
        }

    def _process_skills_extracted_batch(self, event: EventEnvelope) -> EventEnvelope:
        import json as _json
        from contextlib import nullcontext, suppress

        from agents.common.llm_adapter import get_tracer

        payload = event.payload
        correlation_id = event.correlation_id
        batch_id = str(payload.get("batch_id") or "batch-unknown")

        tracer = get_tracer()
        rows = _records_from_skills_payload(payload)

        # Serialize input EventEnvelope summary for Langfuse trace visibility
        _input_str: str | None = None
        if tracer:
            with suppress(Exception):
                _input_str = _json.dumps({
                    "event_type": payload.get("event_type", "SkillsExtracted"),
                    "correlation_id": correlation_id,
                    "batch_id": batch_id,
                    "record_count": len(rows),
                })

        span_ctx = (
            tracer.start_span(
                "enrichment",
                correlation_id=correlation_id,
                input=_input_str,
                metadata={"batch_id": batch_id, "record_count": len(rows)},
            )
            if tracer
            else nullcontext()
        )
        enriched_count = 0
        spam_rejected_count = 0
        flagged_for_review_count = 0
        temporal_period_distribution: dict[str, int] = defaultdict(int)
        borderplex_subregion_distribution: dict[str, int] = defaultdict(int)
        duplicate_count = 0
        soc_classified_count = 0
        naics_classified_count = 0
        dedup_stub_count = 0
        dedup_rows_with_duplicate_cluster_id = 0
        dedup_rows_with_matched_job_posting_id = 0

        def run_batch(session: Session | None) -> None:
            nonlocal enriched_count, spam_rejected_count, flagged_for_review_count
            nonlocal duplicate_count, soc_classified_count, naics_classified_count
            nonlocal dedup_stub_count, dedup_rows_with_duplicate_cluster_id
            nonlocal dedup_rows_with_matched_job_posting_id
            for row in rows:
                bucket = _spam_bucket(row)
                if bucket == "rejected":
                    spam_rejected_count += 1
                    continue
                if bucket == "flagged":
                    flagged_for_review_count += 1
                    continue

                posting = _posting_for_enrichment(row, payload)
                try:
                    enriched = self.enrich_record(posting, session=session)
                    sector_id = resolve_sector(posting.get("role_classification"), session=session)
                    enriched["sector_id"] = sector_id

                    # Score quality (deterministic — no LLM call)
                    extraction = build_extraction_dict(
                        row.get("skills"),
                        row.get("tools"),
                        row.get("tasks"),
                        row.get("responsibilities"),
                        row.get("context"),
                    )
                    q_res = score_quality(
                        job_title=posting.get("title") or "",
                        job_description=posting.get("description"),
                        extraction=extraction,
                        extraction_failed=bool(row.get("extraction_failed")),
                    )
                    enriched["quality_score"] = q_res.quality_score
                    enriched["quality_components"] = q_res.components

                    enriched_count += 1

                    tp = _distribution_bucket(enriched.get("temporal_period", posting.get("temporal_period")))
                    temporal_period_distribution[tp] += 1
                    bp = _distribution_bucket(enriched.get("borderplex_subregion"))
                    borderplex_subregion_distribution[bp] += 1
                    if enriched.get("is_duplicate") is True:
                        duplicate_count += 1
                    soc_raw = enriched.get("soc_code") or posting.get("soc_code")
                    if soc_raw is not None and str(soc_raw).strip():
                        soc_classified_count += 1
                    naics_raw = enriched.get("naics_code") or posting.get("naics_code")
                    naics_st = str(naics_raw).strip() if naics_raw is not None else ""
                    if naics_st and naics_st.lower() != "unknown":
                        naics_classified_count += 1
                    ds, dc, dm = _rollup_fuzzy_dedup_signals(enriched, posting)
                    dedup_stub_count += ds
                    dedup_rows_with_duplicate_cluster_id += dc
                    dedup_rows_with_matched_job_posting_id += dm
                    nj_promo = _coerce_normalized_job_id(
                        enriched.get("normalized_job_id") or posting.get("normalized_job_id")
                    )
                    if session is not None and nj_promo is not None:
                        try:
                            apply_enrichment_to_job_postings(
                                session,
                                nj_promo,
                                _job_postings_promotion_payload(enriched, posting),
                            )
                        except Exception as promo_exc:
                            log.warning(
                                "enrichment_batch_job_posting_promotion_failed",
                                normalized_job_id=nj_promo,
                                error=str(promo_exc),
                            )
                except Exception:
                    log.warning("enrichment_process_degraded", agent=self.agent_id)

        if check_db_connection():
            try:
                with session_scope() as db_session:
                    run_batch(db_session)
            except Exception as exc:
                log.warning(
                    "enrichment_session_scope_failed",
                    agent=self.agent_id,
                    error=str(exc),
                )
                run_batch(None)
        else:
            run_batch(None)

        # Log enrichment output EventEnvelope to Langfuse (inside span for visibility)
        with span_ctx:
            if tracer:
                try:
                    total_processed = enriched_count + spam_rejected_count + flagged_for_review_count
                    tracer.log_event("enrichment_complete", {
                        "output": _json.dumps({
                            "event_type": "RecordEnriched",
                            "batch_id": batch_id,
                            "enriched_count": enriched_count,
                            "spam_rejected_count": spam_rejected_count,
                            "flagged_for_review_count": flagged_for_review_count,
                            "soc_classified_count": soc_classified_count,
                            "naics_classified_count": naics_classified_count,
                            "duplicate_count": duplicate_count,
                        }),
                        "enriched_count": enriched_count,
                        "spam_rejected_count": spam_rejected_count,
                        "flagged_for_review_count": flagged_for_review_count,
                        "soc_classified_count": soc_classified_count,
                        "naics_classified_count": naics_classified_count,
                        "total_processed": total_processed,
                    })
                except Exception:
                    pass

        return build_record_enriched_event(
            correlation_id=correlation_id,
            batch_id=batch_id,
            enriched_count=enriched_count,
            spam_rejected_count=spam_rejected_count,
            flagged_for_review_count=flagged_for_review_count,
            temporal_period_distribution=dict(temporal_period_distribution),
            borderplex_subregion_distribution=dict(borderplex_subregion_distribution),
            duplicate_count=duplicate_count,
            soc_classified_count=soc_classified_count,
            naics_classified_count=naics_classified_count,
            dedup_stub_count=dedup_stub_count,
            dedup_rows_with_duplicate_cluster_id=dedup_rows_with_duplicate_cluster_id,
            dedup_rows_with_matched_job_posting_id=dedup_rows_with_matched_job_posting_id,
        )

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Single-record path: ``RecordEnriched`` with classification, quality, spam preview.
        Includes ``temporal_period`` and ``borderplex_subregion`` when normalized-job context
        is available.

        Batch path (non-empty ``records``): one aggregate ``RecordEnriched`` via
        :func:`build_record_enriched_event`.
        """
        if not self._fixture:
            if _FIXTURE_PATH.exists():
                records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
                self._fixture = {r["posting_id"]: r for r in records}
            else:
                self._fixture = {}

        raw_records = event.payload.get("records")
        if isinstance(raw_records, list) and len(raw_records) > 0:
            return self._process_skills_extracted_batch(event)

        posting_id = event.payload.get("posting_id")
        fx = self._fixture.get(posting_id, {})
        title = (event.payload.get("title") or fx.get("title") or "").strip()
        description = event.payload.get("description") or fx.get("description")
        company = event.payload.get("company") if event.payload.get("company") is not None else fx.get("company")

        tech, sectors = self._ensure_refs()

        nj_id = _coerce_normalized_job_id(event.payload.get("normalized_job_id"))
        desc_str = description if isinstance(description, str) else None

        ei_row: dict[str, Any] | None = None
        resolved_job_posting: dict[str, Any] | None = None
        ei_fetch_error = False
        if nj_id is not None and _db_url_configured():
            try:
                with session_scope() as session:
                    ei_row = session.execute(_LATEST_EI_BY_NJ_ID_SQL, {"nj_id": nj_id}).mappings().first()
                    resolved_job_posting = resolve_job_posting_row(session, nj_id)
            except Exception as exc:
                log.warning("enrichment_ei_load_failed", normalized_job_id=nj_id, error=str(exc))
                ei_fetch_error = True

        ext: dict[str, Any] | None = None
        extraction_failed = False
        if ei_row is not None:
            ext = build_extraction_dict(
                ei_row.get("skills"),
                ei_row.get("tools"),
                ei_row.get("tasks"),
                ei_row.get("responsibilities"),
                ei_row.get("context"),
            )
            extraction_failed = bool(ei_row.get("extraction_failed"))
        elif nj_id is None:
            ext = build_extraction_dict(
                event.payload.get("skills"),
                event.payload.get("tools"),
                [],
                [],
                [],
            )

        is_internship = bool(event.payload.get("is_internship", False))

        role_classification, seniority = classify_job(
            title,
            desc_str,
            ext,
            tech,
            sectors,
            is_internship=is_internship,
        )

        quality_res = score_quality(
            job_title=title,
            job_description=desc_str,
            extraction=ext,
            extraction_failed=extraction_failed,
        )
        quality_score = quality_res.quality_score
        quality_components = quality_res.components

        spam_block: dict[str, Any] = {}
        spam_result: SpamPreviewResult | None = None
        degraded_reason: str | None = None
        if nj_id is not None and _db_url_configured():
            if ei_fetch_error:
                spam_result = _degraded_spam_result(extraction_note=None)
                degraded_reason = "extracted_intelligence_unavailable"
                spam_block = _spam_from_preview_result(spam_result)
            elif ei_row is not None:
                extraction_empty = ext is None
                spam_result = score_spam_preview(
                    job_title=title,
                    job_description=desc_str,
                    extraction=ext or {},
                    extraction_failed=extraction_failed,
                    extraction_empty=extraction_empty,
                )
                if spam_result.degraded:
                    degraded_reason = "spam_classifier_unavailable"
                spam_block = _spam_from_preview_result(spam_result)
            else:
                spam_result = score_spam_preview(
                    job_title=title,
                    job_description=desc_str,
                    extraction={},
                    extraction_failed=False,
                    extraction_empty=True,
                )
                if spam_result.degraded:
                    degraded_reason = "spam_classifier_unavailable"
                spam_block = _spam_from_preview_result(spam_result)
            payload_spam_score = spam_block["spam_score"]
            payload_is_spam = spam_block["is_spam"]
        else:
            payload_spam_score = fx.get("spam_score")
            payload_is_spam = fx.get("is_spam")

        derived_output_fields = derive_enrichment_output_fields(resolved_job_posting)
        enriched_job_profile = EnrichedJobProfile(
            job_record={
                "posting_id": posting_id,
                "normalized_job_id": nj_id,
                "title": title or fx.get("title"),
                "company": company,
                "skills": event.payload.get("skills", []),
            },
            temporal_period=derived_output_fields.get("temporal_period"),
            borderplex_subregion=derived_output_fields.get("borderplex_subregion"),
        )
        pair_a_profile_fields = {
            "temporal_period": enriched_job_profile.temporal_period,
            "borderplex_subregion": enriched_job_profile.borderplex_subregion,
        }

        resolved_company_id: str | None = None
        if resolved_job_posting and resolved_job_posting.get("company_id") is not None:
            rc = str(resolved_job_posting["company_id"]).strip()
            resolved_company_id = rc or None
        fixture_company_id = fx.get("company_id")
        if fixture_company_id is not None and not isinstance(fixture_company_id, str):
            fixture_company_id = str(fixture_company_id).strip() or None
        elif isinstance(fixture_company_id, str):
            fixture_company_id = fixture_company_id.strip() or None
        effective_company_id = resolved_company_id or fixture_company_id

        base_payload: dict[str, Any] = {
            "event_type": "RecordEnriched",
            "posting_id": posting_id,
            "title": title or fx.get("title"),
            "company": company,
            "company_id": effective_company_id,
            "sector_id": fx.get("sector_id"),
            "role_classification": role_classification,
            "seniority": seniority,
            "quality_score": quality_score,
            "quality_components": quality_components,
            "spam_score": payload_spam_score,
            "is_spam": payload_is_spam,
            "enrichment_status": fx.get("enrichment_status", "success"),
            "skills": event.payload.get("skills", []),
            **pair_a_profile_fields,
        }
        if nj_id is not None:
            base_payload["normalized_job_id"] = nj_id
        if spam_block:
            base_payload.update(spam_block)
        if degraded_reason is not None and spam_result is not None:
            _emit_enrichment_degraded(
                correlation_id=event.correlation_id,
                posting_id=posting_id,
                normalized_job_id=nj_id,
                triggered_by_event_type=event.payload.get("event_type"),
                reason=degraded_reason,
                extraction_note=spam_result.extraction_note,
            )

        if nj_id is not None and _db_url_configured():
            try:
                with session_scope() as session:
                    raw_naics = classify_naics(title, desc_str, session)
                    base_payload["naics_code"] = (raw_naics or "unknown").strip() or "unknown"
                    try:
                        raw_soc = run_coroutine(
                            classify_soc(
                                title or "",
                                desc_str or "",
                                session,
                                _enrichment_soc_llm(),
                            )
                        )
                        base_payload["soc_code"] = None if raw_soc == "unclassified" else raw_soc
                        _soc = base_payload["soc_code"]
                        oc_value = _soc[:20] if _soc else None
                        session.execute(
                            update(NormalizedJob).where(NormalizedJob.id == nj_id).values(occupation_code=oc_value)
                        )
                    except Exception as soc_exc:
                        log.warning(
                            "enrichment_soc_failed",
                            normalized_job_id=nj_id,
                            error=str(soc_exc),
                        )
                        base_payload["soc_code"] = None
                    ep = build_employer_profile(desc_str, str(company or ""), session)
                    base_payload["employer_metadata"] = ep.model_dump(mode="json")
                    persist_employer_metadata(
                        session,
                        ep,
                        company_id=effective_company_id,
                        normalized_job_id=nj_id,
                        source=event.payload.get("source"),
                        external_id=event.payload.get("external_id"),
                    )
                    apply_enrichment_to_job_postings(session, nj_id, base_payload)
            except Exception as exc:
                log.warning(
                    "enrichment_promotion_failed",
                    normalized_job_id=nj_id,
                    error=str(exc),
                )

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=base_payload,
        )

    def enrich_record(
        self,
        posting: dict[str, Any],
        session: Session | None,
    ) -> dict[str, Any]:
        try:
            company_id, company_confidence = resolve_company(posting.get("company") or "", session)
            location_id, location_confidence, raw_location_text, borderplex_subregion = resolve_location(
                posting.get("location", ""), session
            )
            field_confidence = compute_field_confidence(
                company_confidence,
                location_confidence,
                sector_id=None,
                seniority_confidence=posting.get("seniority_confidence"),
            )
            overall_confidence = compute_overall_confidence(
                field_confidence=field_confidence,
                extraction_confidence=posting.get("extraction_confidence"),
                quality_score=posting.get("quality_score"),
                taxonomy_coverage=posting.get("taxonomy_coverage"),
            )
            merged: dict[str, Any] = {
                **posting,
                "company_id": company_id,
                "location_id": location_id,
                "raw_location_text": raw_location_text,
                "borderplex_subregion": borderplex_subregion,
                "field_confidence": field_confidence,
                "overall_confidence": overall_confidence,
            }
            try:
                ext = run_coroutine(self._external_facade.fetch_for_posting(merged))
                merged.update(ext)
            except RuntimeError as re_exc:
                log.warning(
                    "enrichment_external_adapters_skipped",
                    reason=str(re_exc),
                )
            except Exception as ext_exc:  # noqa: BLE001
                log.warning(
                    "enrichment_external_adapters_failed",
                    error=str(ext_exc),
                )
            if session is not None:
                desc_raw = posting.get("description")
                desc_str = desc_raw if isinstance(desc_raw, str) else None
                try:
                    raw_naics = classify_naics(posting.get("title") or "", desc_str, session)
                    merged["naics_code"] = (raw_naics or "unknown").strip() or "unknown"
                except Exception as naics_exc:
                    log.warning("enrich_record_naics_failed", error=str(naics_exc))
                    merged["naics_code"] = posting.get("naics_code")
                try:
                    raw_soc = run_coroutine(
                        classify_soc(
                            posting.get("title") or "",
                            desc_str or "",
                            session,
                            _enrichment_soc_llm(),
                        )
                    )
                    merged["soc_code"] = None if raw_soc == "unclassified" else raw_soc
                except Exception as soc_exc:
                    log.warning("enrich_record_soc_failed", error=str(soc_exc))
                    merged["soc_code"] = posting.get("soc_code")
                else:
                    nj_soc = _coerce_normalized_job_id(posting.get("normalized_job_id"))
                    sc = merged.get("soc_code")
                    if nj_soc is not None and isinstance(sc, str) and sc.strip():
                        try:
                            session.execute(
                                update(NormalizedJob)
                                .where(NormalizedJob.id == nj_soc)
                                .values(occupation_code=sc.strip()[:20])
                            )
                        except Exception as oc_exc:
                            log.warning(
                                "enrich_record_occupation_code_persist_failed",
                                error=str(oc_exc),
                            )
                try:
                    ep = build_employer_profile(desc_str, posting.get("company") or "", session)
                    merged["employer_metadata"] = ep.model_dump(mode="json")
                    cid_raw = merged.get("company_id")
                    persist_company_id = str(cid_raw).strip() if cid_raw is not None and str(cid_raw).strip() else None
                    persist_employer_metadata(
                        session,
                        ep,
                        company_id=persist_company_id,
                        normalized_job_id=_coerce_normalized_job_id(posting.get("normalized_job_id")),
                        source=posting.get("source"),
                        external_id=posting.get("external_id"),
                    )
                except Exception as emp_exc:
                    log.warning("enrich_record_employer_failed", error=str(emp_exc))
                    merged["employer_metadata"] = EmployerProfile().model_dump(mode="json")
            return merged
        except Exception:
            log.warning(
                "enrich_record_degraded",
                agent=self.agent_id,
                reason="resolver_exception",
            )
            return {
                **posting,
                "company_id": None,
                "location_id": None,
                "raw_location_text": None,
                "borderplex_subregion": None,
                "naics_code": posting.get("naics_code"),
                "employer_metadata": EmployerProfile().model_dump(mode="json"),
                "field_confidence": {
                    "company_id": 0.0,
                    "location_id": 0.0,
                    "sector_id": 0.0,
                    "seniority": 0.0,
                },
                "overall_confidence": 0.0,
                "enrichment_status": "degraded",
            }

    def run_cli_preview(self, limit: int) -> None:
        """Load jobs from DB and print role + seniority (stdout)."""
        _load_repo_dotenv()
        if not _db_url_configured():
            print("PYTHON_DATABASE_URL is required for CLI mode.", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        with session_scope() as session:
            technology_areas, industry_sectors = self._load_reference_labels(session)
            log.info(
                "enrichment_cli_start",
                limit=limit,
                tech_areas=len(technology_areas),
                sectors=len(industry_sectors),
            )
            rows = session.execute(_LATEST_EI_SQL, {"lim": limit}).mappings().all()

        for row in rows:
            extraction = {
                "skills": row.get("skills"),
                "tools": row.get("tools"),
                "tasks": row.get("tasks"),
                "responsibilities": row.get("responsibilities"),
                "context": row.get("context"),
            }
            role, seniority = classify_job(
                row.get("job_title") or "",
                row.get("job_description"),
                extraction,
                technology_areas,
                industry_sectors,
                is_internship=bool(row.get("is_internship")),
            )
            jid = row.get("job_posting_id") or ""
            src = row.get("source") or ""
            ext_id = row.get("external_id") or ""
            line = (
                f"job_posting_id={jid}\tsource={src}\texternal_id={ext_id}\t"
                f"seniority={seniority}\trole_classification={role}"
            )
            print(line)  # noqa: T201


def main() -> None:
    _load_repo_dotenv()
    parser = argparse.ArgumentParser(description="Print deterministic enrichment labels per job.")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max rows from job_postings to process (default 50).",
    )
    args = parser.parse_args()
    EnrichmentAgent().run_cli_preview(limit=args.limit)


if __name__ == "__main__":
    main()
