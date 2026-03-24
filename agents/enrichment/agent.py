"""
Enrichment Agent stub — Week 2 Walking Skeleton.

Real implementation: Phase 1 lite (refined in Week 5+).

In the walking skeleton this agent returns a pre-computed fixture payload
instead of classifying role/seniority and scoring quality via LLM.

Agent ID (canonical): enrichment-agent
Emits:    RecordEnriched
Consumes: SkillsExtracted

Fixture: agents/data/fixtures/fixture_enriched.json

Phase 1 lite replaces this stub with:
- Role classification (Software Engineering, Data Science, ML, etc.)
- Seniority classification (junior / mid / senior / lead)
- Quality score [0-1]: completeness + clarity + AI keyword density + structural coherence
- Spam detection: score < 0.7 -> proceed | 0.7-0.9 -> flag (is_spam=null) | > 0.9 -> reject
- Company resolution: match companies table by name, create placeholder if missing
- Sector mapping: map to industry_sectors table
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.enrichment.resolvers.company_resolver import resolve_company
from agents.enrichment.resolvers.confidence import (
    compute_field_confidence,
    compute_overall_confidence,
)
from agents.enrichment.resolvers.events import build_record_enriched_event
from agents.enrichment.resolvers.location_resolver import resolve_location
from agents.enrichment.resolvers.sector_resolver import resolve_sector

log = structlog.get_logger()

_FIXTURE_PATH = (
    Path(__file__).parent.parent / "data" / "fixtures" / "fixture_enriched.json"
)


class EnrichmentAgent(BaseAgent):
    """
    Stub for the Enrichment Agent (Phase 1 lite).

    Week 2: returns fixture data indexed by posting_id.
    Week 5+: replaces this with real role/seniority classification,
             quality scoring, spam detection, and company resolution.
    """

    @property
    def agent_id(self) -> str:
        return "enrichment-agent"

    def __init__(self) -> None:
        self._fixture: dict[int, dict] = {}

    def health_check(self) -> dict:
        """Return ok status if the fixture file is present and loadable."""
        if not _FIXTURE_PATH.exists():
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}
        try:
            records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
            self._fixture = {r["posting_id"]: r for r in records}
            return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}
        except Exception:
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept upstream job payload (spam/quality from Pair C), enrich when allowed,
        emit one ``RecordEnriched`` event per invocation (batch-style counts).
        """
        payload = event.payload
        correlation_id = event.correlation_id
        batch_id = payload.get("batch_id", "unknown")

        if "is_spam" in payload:
            if payload["is_spam"] is True:
                return build_record_enriched_event(
                    correlation_id=correlation_id,
                    batch_id=batch_id,
                    enriched_records=[],
                    spam_rejected=1,
                    flagged_count=0,
                )
            if payload["is_spam"] is None:
                return build_record_enriched_event(
                    correlation_id=correlation_id,
                    batch_id=batch_id,
                    enriched_records=[],
                    spam_rejected=0,
                    flagged_count=1,
                )

        try:
            posting = {
                "posting_id": payload.get("posting_id"),
                "title": payload.get("title"),
                "company": payload.get("company"),
                "location": payload.get("location", ""),
                "quality_score": payload.get("quality_score"),
                "spam_score": payload.get("spam_score"),
                "is_spam": payload.get("is_spam"),
                "seniority": payload.get("seniority"),
                "role_classification": payload.get("role_classification"),
                "skills": payload.get("skills", []),
                "seniority_confidence": 0.90 if payload.get("seniority") is not None else 0.0,
                "extraction_confidence": payload.get("extraction_confidence"),
                "taxonomy_coverage": payload.get("taxonomy_coverage"),
            }
            enriched = self.enrich_record(posting, session=None)
            sector_id = resolve_sector(posting.get("role_classification"), session=None)
            enriched["sector_id"] = sector_id
            return build_record_enriched_event(
                correlation_id=correlation_id,
                batch_id=batch_id,
                enriched_records=[enriched],
                spam_rejected=0,
                flagged_count=0,
            )
        except Exception:
            log.warning("enrichment_process_degraded", agent=self.agent_id)
            return EventEnvelope(
                correlation_id=correlation_id,
                agent_id=self.agent_id,
                payload={
                    "event_type": "RecordEnriched",
                    "batch_id": batch_id,
                    "enriched_count": 0,
                    "spam_rejected_count": 0,
                    "flagged_for_review_count": 0,
                    "process_status": "degraded",
                },
            )

    def enrich_record(self, posting: dict[str, Any], session: Any) -> dict[str, Any]:
        """
        Resolve company/location and compute confidence for one posting dict.

        On failure, returns the posting with zeroed confidence and
        ``enrichment_status: degraded`` so the batch can continue.
        """
        try:
            company_id, company_confidence = resolve_company(posting["company"], session)
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
