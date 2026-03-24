"""
Skills enrichment — Pair D (Week 5): company / location / sector resolution and confidence.

Consumes ``SkillsExtracted`` (after Pair C spam / quality / classification on each record).
Emits exactly one ``RecordEnriched`` per batch invocation (Week 5 lite payload, issue #87).

Agent ID (canonical): enrichment-agent
Emits:    RecordEnriched
Consumes: SkillsExtracted

Pair C applies spam bands: score > 0.9 → reject; 0.7–0.9 → flag (``is_spam is None``);
below 0.7 → proceed. When ``is_spam`` is set explicitly by upstream, it overrides ``spam_score``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

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

SpamBucket = Literal["rejected", "flagged", "proceed"]


def _records_from_skills_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Prefer ``records`` from SkillsExtracted; otherwise treat the payload as one logical row."""
    raw = payload.get("records")
    if isinstance(raw, list) and len(raw) > 0:
        out: list[dict[str, Any]] = []
        for item in raw:
            out.append(dict(item) if isinstance(item, dict) else {})
        return out
    return [payload]


def _spam_bucket(record: dict[str, Any]) -> SpamBucket:
    """Classify Pair C outcome: rejected / flagged / proceed to Pair D resolution."""
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
    """Build the posting dict passed to ``enrich_record`` (record fields + batch fallbacks)."""
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


class EnrichmentAgent(BaseAgent):
    """
    Enrichment Agent — Pair D resolution and batch-level ``RecordEnriched`` emission.

    Aggregates all rows from a ``SkillsExtracted`` payload (``records`` or flat single-record),
    applies Pair C gating, runs resolvers for each allowed row, then emits one event.
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
        Consume ``SkillsExtracted``; emit one ``RecordEnriched`` with batch-level counts (issue #87).
        """
        payload = event.payload
        correlation_id = event.correlation_id
        batch_id = str(payload.get("batch_id") or "unknown")

        rows = _records_from_skills_payload(payload)
        enriched_count = 0
        spam_rejected_count = 0
        flagged_for_review_count = 0

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
                enriched = self.enrich_record(posting, session=None)
                sector_id = resolve_sector(posting.get("role_classification"), session=None)
                enriched["sector_id"] = sector_id
                enriched_count += 1
            except Exception:
                log.warning("enrichment_process_degraded", agent=self.agent_id)

        return build_record_enriched_event(
            correlation_id=correlation_id,
            batch_id=batch_id,
            enriched_count=enriched_count,
            spam_rejected_count=spam_rejected_count,
            flagged_for_review_count=flagged_for_review_count,
        )

    def enrich_record(self, posting: dict[str, Any], session: Any) -> dict[str, Any]:
        """
        Resolve company/location and compute confidence for one posting dict.

        On failure, returns the posting with zeroed confidence and
        ``enrichment_status: degraded`` so the batch can continue.
        """
        try:
            company_id, company_confidence = resolve_company(posting.get("company"), session)
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
