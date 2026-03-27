"""
Skills enrichment: Pair D resolution plus Phase 1 classification, quality, and EI spam preview.

Consumes ``SkillsExtracted`` with optional ``batch_id`` and ``records`` (batch shape). Emits
exactly one ``RecordEnriched`` per invocation with batch counts and ``spam_tier_counts`` (issue #86).

When ``check_db_connection()`` is true, ``process()`` opens one ``session_scope()`` for the
whole batch. Resolution (``enrich_record``, ``resolve_sector``) and
``apply_enrichment_to_job_postings`` use that same session.

**Gating vs promotion (flagged rows)**

* **Rejected** (``is_spam`` True, or spam score above reject threshold): skip company or location
  resolution, skip sector resolution, and **do not** call ``apply_enrichment_to_job_postings``
  (rejected tier performs no UPDATE per ``job_postings_promotion``).

* **Flagged** (``is_spam`` None, or score in the uncertain band): skip resolution and sector
  lookup, but **still** call ``apply_enrichment_to_job_postings`` when ``normalized_job_id`` and
  DB allow, so quality and spam columns follow ``job_postings_promotion`` tier rules (flagged or
  uncertain UPDATE paths).

* **Proceed**: full ``enrich_record`` + ``resolve_sector``, then promotion when allowed.

Pair C bands when upstream only sends scores: score above 0.9 → rejected; 0.7–0.9 → flagged;
below 0.7 → proceed. When ``is_spam`` is set explicitly on the inbound row, EI
``score_spam_preview`` is skipped so upstream spam decisions stay authoritative.

Agent ID (canonical): enrichment-agent
Emits:    RecordEnriched, EnrichmentDegraded (optional alert bus)
Consumes: SkillsExtracted
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Literal

import structlog
from dotenv import load_dotenv
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from agents.common.base_agent import BaseAgent
from agents.common.data_store import check_db_connection, session_scope
from agents.common.data_store.models import IndustrySector, TechnologyArea
from agents.common.event_envelope import EventEnvelope
from agents.enrichment.classification import (
    FALLBACK_TECH_AREA_LABELS,
    classify_job,
)
from agents.enrichment.classifiers.quality import score_quality
from agents.enrichment.classifiers.spam_preview import (
    SpamPreviewResult,
    apply_spam_tiers,
    score_spam_preview,
)
from agents.enrichment.job_postings_promotion import apply_enrichment_to_job_postings
from agents.enrichment.resolvers.company_resolver import resolve_company
from agents.enrichment.resolvers.confidence import (
    compute_field_confidence,
    compute_overall_confidence,
)
from agents.enrichment.resolvers.events import build_record_enriched_event
from agents.enrichment.resolvers.location_resolver import resolve_location
from agents.enrichment.resolvers.sector_resolver import resolve_sector
from agents.scripts.jsearch_enrichment_preview_lib import build_extraction_dict

log = structlog.get_logger()

_alert_bus: Any = None

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENV_PATH = _REPO_ROOT / ".env"

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


def _load_repo_dotenv() -> None:
    load_dotenv(_ENV_PATH, override=False)


def _db_url_configured() -> bool:
    return bool(os.getenv("PYTHON_DATABASE_URL"))


def register_alert_bus(bus: Any | None) -> None:
    global _alert_bus
    _alert_bus = bus


def _coerce_normalized_job_id(raw: Any) -> int | None:
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    return None


def _spam_from_preview_result(result: SpamPreviewResult) -> dict[str, Any]:
    return {
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
    raw = payload.get("records")
    if isinstance(raw, list) and len(raw) > 0:
        out: list[dict[str, Any]] = []
        for item in raw:
            out.append(dict(item) if isinstance(item, dict) else {})
        return out
    return [payload]


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


def _ensure_spam_tier(working: dict[str, Any]) -> None:
    if working.get("spam_tier"):
        return
    ss = working.get("spam_score")
    if isinstance(ss, (int, float)):
        try:
            _, tier = apply_spam_tiers(float(ss))
            working["spam_tier"] = tier
        except (TypeError, ValueError):
            working["spam_tier"] = "uncertain"


def _spam_tier_counts_payload(counter: Counter[str]) -> dict[str, int]:
    keys = ("clean", "flagged", "rejected", "uncertain")
    return {k: int(counter.get(k, 0)) for k in keys}


def _count_row_spam_tier(working: dict[str, Any], counter: Counter[str]) -> None:
    tier = working.get("spam_tier")
    if isinstance(tier, str) and tier in ("clean", "flagged", "rejected", "uncertain"):
        counter[tier] += 1
        return
    ss = working.get("spam_score")
    if isinstance(ss, (int, float)):
        try:
            _, t = apply_spam_tiers(float(ss))
            counter[t] += 1
        except (TypeError, ValueError):
            counter["uncertain"] += 1
    else:
        counter["uncertain"] += 1


_EXTRA_POSTING_KEYS = frozenset({
    "soc_code",
    "naics_code",
    "temporal_period",
    "borderplex_subregion",
    "is_duplicate",
    "duplicate_cluster_id",
})


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
        "location": pick("location", "") or "",
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


def _pick_row_batch(row: dict[str, Any], batch: dict[str, Any], key: str, default: Any = None) -> Any:
    if key in row and row[key] is not None:
        return row[key]
    if key in batch and batch[key] is not None:
        return batch[key]
    return default


def _fetch_ei_row(session: Any | None, nj_id: int) -> tuple[dict[str, Any] | None, bool]:
    try:
        if session is not None:
            r = session.execute(_LATEST_EI_BY_NJ_ID_SQL, {"nj_id": nj_id}).mappings().first()
            return (dict(r) if r else None), False
        if _db_url_configured():
            with session_scope() as s:
                r = s.execute(_LATEST_EI_BY_NJ_ID_SQL, {"nj_id": nj_id}).mappings().first()
                return (dict(r) if r else None), False
    except Exception as exc:
        log.warning("enrichment_ei_load_failed", normalized_job_id=nj_id, error=str(exc))
        return None, True
    return None, False


def _promotion_payload_from_working(working: dict[str, Any], enriched: dict[str, Any] | None) -> dict[str, Any]:
    base = dict(enriched) if enriched is not None else {}
    for k in (
        "quality_score",
        "quality_components",
        "spam_score",
        "is_spam",
        "spam_tier",
        "role_classification",
        "seniority",
        "spam_rationale",
        "spam_degraded",
        "spam_used_heuristic",
    ):
        if working.get(k) is not None:
            base[k] = working[k]
    if enriched is None:
        fc = working.get("field_confidence")
        if fc:
            base["field_confidence"] = fc
        if working.get("overall_confidence") is not None:
            base["overall_confidence"] = working["overall_confidence"]
    return base


class EnrichmentAgent(BaseAgent):
    """Batch enrichment: pre-row classification and spam, then Pair D resolution and promotion."""

    @property
    def agent_id(self) -> str:
        return "enrichment-agent"

    def __init__(self) -> None:
        self._fixture: dict[int, dict] = {}
        self._refs: tuple[list[tuple[str, str]], list[tuple[str, str]]] | None = None

    def _ensure_fixture(self) -> None:
        if self._fixture or not _FIXTURE_PATH.exists():
            return
        try:
            records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
            self._fixture = {r["posting_id"]: r for r in records}
        except Exception:
            self._fixture = {}

    @staticmethod
    def _load_reference_labels(session: Session) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        tech_rows = session.execute(select(TechnologyArea.id, TechnologyArea.title)).all()
        technology_areas = [(str(r[0]), str(r[1])) for r in tech_rows]
        sec_rows = session.execute(
            select(IndustrySector.industry_sector_id, IndustrySector.sector_title)
        ).all()
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

    def _enrich_row_pre_resolution(
        self,
        raw_row: dict[str, Any],
        batch_payload: dict[str, Any],
        *,
        correlation_id: str,
        session: Any | None,
    ) -> dict[str, Any]:
        self._ensure_fixture()
        working = dict(raw_row)
        posting_id = _pick_row_batch(working, batch_payload, "posting_id")
        fx: dict = self._fixture.get(posting_id, {}) if posting_id is not None else {}

        title = (_pick_row_batch(working, batch_payload, "title") or fx.get("title") or "").strip()
        description = _pick_row_batch(working, batch_payload, "description")
        if description is None:
            description = fx.get("description")
        company = _pick_row_batch(working, batch_payload, "company")
        if company is None:
            company = fx.get("company")

        desc_str = description if isinstance(description, str) else None
        nj_id = _coerce_normalized_job_id(
            working.get("normalized_job_id") or batch_payload.get("normalized_job_id")
        )
        if nj_id is not None:
            working["normalized_job_id"] = nj_id

        tech, sectors = self._ensure_refs()
        ei_row, ei_fetch_error = (None, False)
        if nj_id is not None and _db_url_configured():
            ei_row, ei_fetch_error = _fetch_ei_row(session, nj_id)

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
                working.get("skills") or _pick_row_batch(working, batch_payload, "skills"),
                working.get("tools") or batch_payload.get("tools"),
                [],
                [],
                [],
            )

        is_internship = bool(
            working.get("is_internship", batch_payload.get("is_internship", False))
        )

        role_classification, seniority = classify_job(
            title,
            desc_str,
            ext,
            tech,
            sectors,
            is_internship=is_internship,
        )
        working["role_classification"] = role_classification
        working["seniority"] = seniority

        quality_res = score_quality(
            job_title=title,
            job_description=desc_str,
            extraction=ext,
            extraction_failed=extraction_failed,
        )
        working["quality_score"] = quality_res.quality_score
        working["quality_components"] = quality_res.components

        upstream_spam_locked = "is_spam" in raw_row
        spam_result: SpamPreviewResult | None = None
        degraded_reason: str | None = None

        if upstream_spam_locked:
            _ensure_spam_tier(working)
            if not working.get("spam_tier"):
                isp = working.get("is_spam")
                if isp is True:
                    working["spam_tier"] = "rejected"
                elif isp is None:
                    working["spam_tier"] = "uncertain"
                else:
                    working["spam_tier"] = "clean"
        elif nj_id is not None and _db_url_configured():
            if ei_fetch_error:
                spam_result = _degraded_spam_result(extraction_note=None)
                degraded_reason = "extracted_intelligence_unavailable"
                working.update(_spam_from_preview_result(spam_result))
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
                working.update(_spam_from_preview_result(spam_result))
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
                working.update(_spam_from_preview_result(spam_result))
        else:
            if working.get("spam_score") is None and fx.get("spam_score") is not None:
                working["spam_score"] = fx.get("spam_score")
            if "is_spam" not in raw_row and fx.get("is_spam") is not None:
                working["is_spam"] = fx.get("is_spam")
            _ensure_spam_tier(working)
            if not working.get("spam_tier"):
                isp = working.get("is_spam")
                if isp is True:
                    working["spam_tier"] = "rejected"
                elif isp is None:
                    working["spam_tier"] = "uncertain"
                else:
                    working["spam_tier"] = "clean"

        if degraded_reason is not None and spam_result is not None:
            _emit_enrichment_degraded(
                correlation_id=correlation_id,
                posting_id=posting_id,
                normalized_job_id=nj_id,
                triggered_by_event_type=batch_payload.get("event_type"),
                reason=degraded_reason,
                extraction_note=spam_result.extraction_note,
            )

        working["title"] = title or fx.get("title")
        if company is not None:
            working["company"] = company
        return working

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

    def process(self, event: EventEnvelope) -> EventEnvelope:
        payload = event.payload
        correlation_id = event.correlation_id
        batch_id = str(payload.get("batch_id") or "unknown")
        rows = _records_from_skills_payload(payload)

        enriched_count = 0
        spam_rejected_count = 0
        flagged_for_review_count = 0
        tier_counter: Counter[str] = Counter()

        def run_batch(db_session: Any | None) -> None:
            nonlocal enriched_count, spam_rejected_count, flagged_for_review_count
            for raw_row in rows:
                working = self._enrich_row_pre_resolution(
                    raw_row,
                    payload,
                    correlation_id=correlation_id,
                    session=db_session,
                )
                _count_row_spam_tier(working, tier_counter)

                bucket = _spam_bucket(working)
                nj_id = _coerce_normalized_job_id(working.get("normalized_job_id"))

                if bucket == "rejected":
                    spam_rejected_count += 1
                    continue

                if bucket == "flagged":
                    flagged_for_review_count += 1
                    if (
                        nj_id is not None
                        and db_session is not None
                        and check_db_connection()
                    ):
                        try:
                            apply_enrichment_to_job_postings(
                                db_session,
                                nj_id,
                                _promotion_payload_from_working(working, None),
                            )
                        except Exception as exc:
                            log.warning(
                                "enrichment_promotion_failed_flagged",
                                normalized_job_id=nj_id,
                                error=str(exc),
                            )
                    continue

                posting = _posting_for_enrichment(working, payload)
                try:
                    enriched = self.enrich_record(posting, session=db_session)
                    sector_id = resolve_sector(
                        posting.get("role_classification"),
                        session=db_session,
                    )
                    enriched["sector_id"] = sector_id

                    merged_fc = dict(enriched.get("field_confidence") or {})
                    for k, v in (working.get("field_confidence") or {}).items():
                        try:
                            merged_fc[k] = float(v)
                        except (TypeError, ValueError):
                            continue
                    enriched["field_confidence"] = merged_fc
                    enriched["overall_confidence"] = compute_overall_confidence(
                        field_confidence=merged_fc,
                        extraction_confidence=enriched.get("extraction_confidence"),
                        quality_score=enriched.get("quality_score"),
                        taxonomy_coverage=enriched.get("taxonomy_coverage"),
                    )
                    enriched_count += 1

                    if nj_id is not None and db_session is not None and check_db_connection():
                        try:
                            apply_enrichment_to_job_postings(
                                db_session,
                                nj_id,
                                _promotion_payload_from_working(working, enriched),
                            )
                        except Exception as exc:
                            log.warning(
                                "enrichment_promotion_failed",
                                normalized_job_id=nj_id,
                                error=str(exc),
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

        return build_record_enriched_event(
            correlation_id=correlation_id,
            batch_id=batch_id,
            enriched_count=enriched_count,
            spam_rejected_count=spam_rejected_count,
            flagged_for_review_count=flagged_for_review_count,
            spam_tier_counts=_spam_tier_counts_payload(tier_counter),
        )

    def enrich_record(self, posting: dict[str, Any], session: Any) -> dict[str, Any]:
        try:
            company_id, company_confidence = resolve_company(
                posting.get("company") or "", session
            )
            location_id, location_confidence, raw_location_text, borderplex_subregion = (
                resolve_location(posting.get("location", ""), session)
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
            return {
                **posting,
                "company_id": company_id,
                "location_id": location_id,
                "raw_location_text": raw_location_text,
                "borderplex_subregion": borderplex_subregion,
                "field_confidence": field_confidence,
                "overall_confidence": overall_confidence,
            }
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
            db_rows = session.execute(_LATEST_EI_SQL, {"lim": limit}).mappings().all()

        for row in db_rows:
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
