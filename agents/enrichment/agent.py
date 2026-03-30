"""
Enrichment Agent — Phase 1 lite (Pair C: classification + quality + spam; Pair D: resolvers in resolvers/).

Loads reference labels from ``technology_areas`` and ``industry_sectors`` when
``PYTHON_DATABASE_URL`` is set; otherwise uses
``classification.FALLBACK_TECH_AREA_LABELS`` for offline / walking-skeleton
runs.

Agent ID (canonical): enrichment-agent
Emits:    RecordEnriched
          EnrichmentDegraded (alert bus, when registered)
Consumes: SkillsExtracted

When the inbound ``SkillsExtracted``-shaped payload includes ``normalized_job_id``
(int) and ``PYTHON_DATABASE_URL`` is set, spam scoring loads the latest
``dbo.extracted_intelligence`` row for that id and calls
``score_spam_preview`` (Decision #8). Otherwise ``spam_score`` / ``is_spam``
come from the walking-skeleton fixture keyed by ``posting_id``.

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
from pathlib import Path
from typing import Any

import structlog
from dotenv import load_dotenv
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from agents.common.base_agent import BaseAgent
from agents.common.data_store.database import check_db_connection, session_scope
from agents.common.data_store.models import IndustrySector, TechnologyArea
from agents.common.event_envelope import EventEnvelope
from agents.enrichment.classification import (
    FALLBACK_TECH_AREA_LABELS,
    classify_job,
)
from agents.enrichment.classifiers.quality import score_quality
from agents.enrichment.classifiers.spam_preview import (
    SpamPreviewResult,
    score_spam_preview,
)
from agents.enrichment.job_postings_promotion import apply_enrichment_to_job_postings
from agents.scripts.jsearch_enrichment_preview_lib import build_extraction_dict

log = structlog.get_logger()

# Optional bus for emitting EnrichmentDegraded; set via register_alert_bus().
_alert_bus: Any = None

# agents/enrichment/agent.py -> parents[0]=enrichment, [1]=agents, [2]=repo root
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


class EnrichmentAgent(BaseAgent):
    """Deterministic enrichment: role + seniority from reference tables and text rules."""

    @property
    def agent_id(self) -> str:
        return "enrichment-agent"

    def __init__(self) -> None:
        self._fixture: dict[int, dict] = {}
        self._refs: tuple[list[tuple[str, str]], list[tuple[str, str]]] | None = None

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

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Emit RecordEnriched with deterministic role_classification and seniority.
        Other enrichment fields come from the walking-skeleton fixture when present.

        Spam: if ``normalized_job_id`` is set and DB is configured, scores from
        latest ``extracted_intelligence`` via ``score_spam_preview``; else fixture
        ``spam_score`` / ``is_spam`` only.

        Quality: deterministic composite via :func:`score_quality` (same title,
        description, and extraction blob as classification when EI is loaded).

        When ``normalized_job_id`` is set and the DB is configured, enrichment
        columns are written to ``job_postings`` (see
        :func:`agents.enrichment.job_postings_promotion.apply_enrichment_to_job_postings`).
        """
        if not self._fixture:
            if _FIXTURE_PATH.exists():
                records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
                self._fixture = {r["posting_id"]: r for r in records}
            else:
                self._fixture = {}

        posting_id = event.payload.get("posting_id")
        fx = self._fixture.get(posting_id, {})
        title = (event.payload.get("title") or fx.get("title") or "").strip()
        description = event.payload.get("description") or fx.get("description")
        company = event.payload.get("company") if event.payload.get("company") is not None else fx.get("company")

        tech, sectors = self._ensure_refs()

        nj_id = _coerce_normalized_job_id(event.payload.get("normalized_job_id"))
        desc_str = description if isinstance(description, str) else None

        ei_row: dict[str, Any] | None = None
        ei_fetch_error = False
        if nj_id is not None and _db_url_configured():
            try:
                with session_scope() as session:
                    ei_row = session.execute(_LATEST_EI_BY_NJ_ID_SQL, {"nj_id": nj_id}).mappings().first()
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

        base_payload: dict[str, Any] = {
            "event_type": "RecordEnriched",
            "posting_id": posting_id,
            "title": title or fx.get("title"),
            "company": company,
            "company_id": fx.get("company_id"),
            "sector_id": fx.get("sector_id"),
            "role_classification": role_classification,
            "seniority": seniority,
            "quality_score": quality_score,
            "quality_components": quality_components,
            "spam_score": payload_spam_score,
            "is_spam": payload_is_spam,
            "enrichment_status": fx.get("enrichment_status", "success"),
            "skills": event.payload.get("skills", []),
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
            ext = row.get("external_id") or ""
            line = (
                f"job_posting_id={jid}\tsource={src}\texternal_id={ext}\t"
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
