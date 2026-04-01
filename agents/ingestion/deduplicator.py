"""Deduplicator for the Ingestion Agent.

Two fingerprint types:
- **Content fingerprint** (``compute_fingerprint``): sha256(external_id | title | company | date_posted)
  — source-agnostic, used for in-batch cross-source dedup.
- **Storage fingerprint** (``compute_storage_hash``): sha256(source | external_id | title | company | date_posted)
  — source-specific, stored as ``raw_payload_hash`` in the DB for cross-batch dedup.

JSearch wins over crawl4ai when the same job appears in both sources (Product #9).

EXP-003 hook: ``compute_fingerprint()`` is the single method that Nestor's
dedup experiment results would replace.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.common.data_store.models import RawIngestedJob

log = structlog.get_logger()

# Source priority: lower number = higher priority (Product #9: JSearch wins)
_SOURCE_PRIORITY = {"jsearch": 0, "crawl4ai": 1, "web_scrape": 2}


@dataclass
class DedupResult:
    """Result of deduplication."""

    new_records: list[dict] = field(default_factory=list)
    duplicates_skipped: int = 0
    source_priority_resolved: int = 0


def _hash_parts(parts: list[str]) -> str:
    """SHA-256 hash of pipe-delimited, lowercased, stripped parts."""
    raw = "|".join(p.strip().lower() for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_fingerprint(record: dict) -> str:
    """Compute a source-agnostic content fingerprint for cross-source dedup.

    Fields used: external_id, title, company, date_posted.
    Excludes ``source`` so the same job from different sources matches.
    """
    return _hash_parts(
        [
            str(record.get("external_id", "")),
            str(record.get("title", "")),
            str(record.get("company", "")),
            str(record.get("date_posted", "")),
        ]
    )


def compute_storage_hash(record: dict) -> str:
    """Compute a source-specific hash stored as ``raw_payload_hash``.

    Includes ``source`` so records from different sources are distinct in the DB.
    Used for cross-batch dedup against existing rows.
    """
    return _hash_parts(
        [
            str(record.get("source", "")),
            str(record.get("external_id", "")),
            str(record.get("title", "")),
            str(record.get("company", "")),
            str(record.get("date_posted", "")),
        ]
    )


def deduplicate_batch(records: list[dict], session: Session) -> DedupResult:
    """Deduplicate a batch of records in two phases.

    Phase 1 — In-batch: detect duplicates using the content fingerprint
    (source-agnostic). When two records match, the higher-priority source wins
    (JSearch > crawl4ai > web_scrape).

    Phase 2 — Cross-batch: check against existing ``raw_ingested_jobs``
    rows by ``raw_payload_hash`` (source-specific storage hash).
    """
    result = DedupResult()

    # Phase 1: In-batch dedup using content fingerprint (no source)
    seen: dict[str, dict] = {}  # content_fingerprint -> best record
    for record in records:
        content_fp = compute_fingerprint(record)
        record["raw_payload_hash"] = compute_storage_hash(record)

        if content_fp in seen:
            existing = seen[content_fp]
            existing_priority = _SOURCE_PRIORITY.get(existing.get("source", ""), 99)
            new_priority = _SOURCE_PRIORITY.get(record.get("source", ""), 99)

            if new_priority < existing_priority:
                # New record has higher priority — replace
                seen[content_fp] = record
                result.source_priority_resolved += 1
                log.debug(
                    "dedup_source_priority",
                    fingerprint=content_fp[:12],
                    kept=record.get("source"),
                    dropped=existing.get("source"),
                )
            result.duplicates_skipped += 1
        else:
            seen[content_fp] = record

    # Phase 2: Cross-batch dedup using storage hash (with source)
    storage_hashes = [r["raw_payload_hash"] for r in seen.values()]
    existing_hashes: set[str] = set()

    if storage_hashes:
        stmt = select(RawIngestedJob.raw_payload_hash).where(RawIngestedJob.raw_payload_hash.in_(storage_hashes))
        rows = session.execute(stmt).scalars().all()
        existing_hashes = set(rows)

    for record in seen.values():
        if record["raw_payload_hash"] in existing_hashes:
            result.duplicates_skipped += 1
            log.debug("dedup_cross_batch", hash=record["raw_payload_hash"][:12], title=record.get("title"))
        else:
            result.new_records.append(record)

    log.info(
        "dedup_complete",
        total_input=len(records),
        new_records=len(result.new_records),
        duplicates_skipped=result.duplicates_skipped,
        source_priority_resolved=result.source_priority_resolved,
    )
    return result
