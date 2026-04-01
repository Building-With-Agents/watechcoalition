# ADR-008 — Enrichment Temporal Period and Borderplex Subregion Findings

**Status:** Accepted  
**Date:** 2026-04-01  
**Owner:** Angel  

## Context / Objective

Week 6 Pair A enrichment work added two deterministic enrichment outputs:
`temporal_period` and `borderplex_subregion`. The goal was to derive both
fields from existing normalized-job data, emit them on the live
`RecordEnriched` event payload, and persist them to `dbo.job_postings`
through the existing promotion path without introducing duplicate logic or
LLM dependence.

This ADR records what was implemented, what was validated in tests, and the
recommended Phase 1 approach.

These fields are derived within the Enrichment agent and integrated into both the event pipeline and database persistence layer.

---

## What I Tested

- Deterministic temporal classification from `date_posted` using UTC calendar
  date boundaries.
- Deterministic Borderplex subregion tagging from structured normalized
  location fields (`city`, `state_province`, `country`, remote signals).
- Shared runtime derivation for emitted `RecordEnriched` payload fields and
  `job_postings` promotion/write-path fields.
- Promotion behavior under the existing spam-tier semantics.
- DB-backed persistence for one live clean-tier enrichment flow.

---

## What I Found

- `temporal_period` is implemented as a deterministic classifier with fixed
  UTC-date boundaries and no LLM dependency. It maps postings into
  `pre_chatgpt`, `early_genai`, `post_gpt4`, or `agentic_era`.
- `borderplex_subregion` is implemented as a deterministic and conservative
  classifier using structured normalized location fields. It only returns a
  specific metro label when city, state/province, and country signals align;
  ambiguous, missing, conflicting, or remote cases fall back to `regional`.
- Both derived fields are produced through shared derivation logic in the
  enrichment runtime, then reused in both places that matter:
  - the emitted `RecordEnriched` payload
  - the `job_postings` promotion/write path
- This shared derivation reduces duplication and helps keep emitted event data
  aligned with persisted database values for the same normalized job context.
- Persistence follows the existing promotion semantics:
  - clean, flagged, and uncertain paths can write the derived fields
  - rejected tier skips the `UPDATE`, so no enrichment columns are changed for
    that row

---

## Recommendation

Adopt `temporal_period` and `borderplex_subregion` as deterministic Phase 1 enrichment outputs.

The current approach is appropriate because it is explainable, reusable in
both runtime and persistence paths, and validated by unit, runtime-path, and
DB-backed tests. Keep the conservative `regional` fallback as the Phase 1
default to reduce false-positive geo tagging.

This ensures consistent enrichment signals across downstream agents, analytics, and evaluation without introducing additional compute cost.

---

## Tradeoffs Acknowledged

- The conservative `regional` fallback reduces false positives, but it also
  lowers specificity when location data is incomplete or ambiguous.
- Rejected spam tier follows existing promotion semantics, so persistence of
  these fields is intentionally skipped in that path.
- Current E2E coverage validates one live persisted clean-tier scenario, not
  every edge case or every spam-tier/storage combination.

---

## Data / Evidence

- Implementation:
  - `agents/enrichment/classifiers/temporal_period.py`
  - `agents/enrichment/classifiers/borderplex_subregion.py`
  - `agents/enrichment/job_postings_promotion.py`
  - `agents/enrichment/agent.py`
- Temporal classifier tests: `agents/enrichment/tests/test_temporal_period.py`
  with **9 passed**, covering boundaries, mid-bucket behavior, `None`, and UTC
  calendar-date handling.
- Borderplex classifier tests:
  `agents/enrichment/tests/test_borderplex_subregion.py` with **20 passed**,
  covering positive metro labels, remote/regional fallback, normalization,
  conflicting signals, and allowed-output invariants.
- Runtime-path promotion tests:
  `agents/enrichment/tests/test_job_postings_promotion.py` passed, including
  derived temporal and subregion values bound into the promotion write path.
- Enrichment agent runtime tests:
  `agents/tests/test_enrichment_agent.py` passed, including emitted
  `RecordEnriched` payload coverage for `temporal_period`,
  `borderplex_subregion`, and the combined runtime derivation path.
- Clean-tier E2E persistence:
  `agents/tests/test_enrichment_job_postings_e2e.py` passed for the live
  persisted clean-tier scenario, verifying stored `temporal_period` and
  `borderplex_subregion` values on `dbo.job_postings`.
