"""Frozen key sets for ``RecordEnriched`` interface stability.

Import these in tests so payload shape drift fails CI. Human-readable field
registry lives in ``.cursor/rules/integration-schema.mdc``.

**Two shapes** (both ``event_type`` == ``RecordEnriched``):

1. **Batch aggregate** — ``build_record_enriched_event()`` / batch ``process()`` when
   ``payload["records"]`` is a non-empty list (incoming ``SkillsExtracted`` shape). Includes
   ``record_enriched_schema_version``, ``freshness_records`` (per-row slice for analytics
   Step 10), and a nested ``dedup`` block (Pair fuzzy-dedup integration, schema v3+).

2. **Single-record** — flat per-posting payload from ``process()`` when there is no
   batch ``records`` list. Does **not** use ``record_enriched_schema_version`` (optional
   future). Use :data:`RECORD_ENRICHED_SINGLE_RECORD_CORE_KEYS` for stable core keys only;
   optional keys (e.g. ``normalized_job_id``, ``employer_metadata``, ``company_id`` for
   employer profile persistence, spam preview extensions) may appear.
"""

from __future__ import annotations

# Nested object under batch ``RecordEnriched`` (always present for batch shape).
RECORD_ENRICHED_DEDUP_BLOCK_KEYS = frozenset(
    {
        "cosine_threshold",
        "rolling_window_days",
        "stub_count",
        "rows_with_duplicate_cluster_id",
        "rows_with_matched_job_posting_id",
    }
)

# Top-level batch aggregate payload (exact key set).
RECORD_ENRICHED_BATCH_PAYLOAD_KEYS = frozenset(
    {
        "event_type",
        "record_enriched_schema_version",
        "batch_id",
        "enriched_count",
        "spam_rejected_count",
        "flagged_for_review_count",
        "temporal_period_distribution",
        "borderplex_subregion_distribution",
        "duplicate_count",
        "soc_classified_count",
        "naics_classified_count",
        "dedup",
        "freshness_records",
    }
)

# Single-record path: keys that are always set before optional spam / NJ promotions.
RECORD_ENRICHED_SINGLE_RECORD_CORE_KEYS = frozenset(
    {
        "event_type",
        "posting_id",
        "title",
        "company",
        "company_id",
        "sector_id",
        "role_classification",
        "seniority",
        "quality_score",
        "quality_components",
        "spam_score",
        "is_spam",
        "enrichment_status",
        "skills",
    }
)
