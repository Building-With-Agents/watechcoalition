"""
Enrichment Agent — Phase 1 lite (deterministic role + seniority).

Loads reference labels from ``technology_areas`` and ``industry_sectors`` when
``PYTHON_DATABASE_URL`` is set; otherwise uses
``classification.FALLBACK_TECH_AREA_LABELS`` for offline / walking-skeleton
runs.

Agent ID (canonical): enrichment-agent
Emits:    RecordEnriched
Consumes: SkillsExtracted

Fixture: agents/data/fixtures/fixture_enriched.json — supplies non-classification
fields (company, scores) for ``process()``; role and seniority are always
computed deterministically.

CLI: ``python -m agents.enrichment.agent --limit 50`` (requires DB URL).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import structlog
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

log = structlog.get_logger()

_FIXTURE_PATH = (
    Path(__file__).parent.parent / "data" / "fixtures" / "fixture_enriched.json"
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

        tech, sectors = self._ensure_refs()
        role_classification, seniority = classify_job(
            title,
            description if isinstance(description, str) else None,
            None,
            tech,
            sectors,
        )

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "RecordEnriched",
                "posting_id": posting_id,
                "title": title or fx.get("title"),
                "company": fx.get("company"),
                "company_id": fx.get("company_id"),
                "sector_id": fx.get("sector_id"),
                "role_classification": role_classification,
                "seniority": seniority,
                "quality_score": fx.get("quality_score"),
                "spam_score": fx.get("spam_score"),
                "is_spam": fx.get("is_spam"),
                "enrichment_status": fx.get("enrichment_status", "success"),
                "skills": event.payload.get("skills", []),
            },
        )

    def run_cli_preview(self, limit: int) -> None:
        """Load jobs from DB and print role + seniority (stdout)."""
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
