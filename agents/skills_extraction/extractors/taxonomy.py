"""Taxonomy resolution — 6-step linking pipeline.

Links extracted skill labels to the ESCO digital skills taxonomy using a
strict 6-step resolution order:
  1. Exact match → GenAI Extension Layer (10 predefined AI-era skills)
  2. Exact match → ESCO digital skills cluster
  3. Normalized match → ESCO digital skills cluster
  4. Embedding cosine similarity >= 0.92 → ESCO
  5. O*NET occupation code match
  6. Emit as raw_skill with esco_uri = null (Enrichment resolves in Phase 2)

Week 4 implementation (Angel + Fabian):
- Set up ESCO digital skills store (Decision #36)
- Build GenAI Extension Layer lookup table (10 skills → ESCO parent clusters)
- Implement resolve_taxonomy() with 6-step order
- Implement resolve_taxonomy_batch() with shared embedding computations
- Track per-step resolution statistics

Reference: ARCHITECTURE_DEEP.md § 6-Step Taxonomy Resolution.
"""

from __future__ import annotations

from agents.common.types import TaxonomyResult


def resolve_taxonomy(label: str) -> TaxonomyResult:
    """Resolve a single skill label against the taxonomy store.

    Parameters
    ----------
    label : str
        Raw skill label extracted from a job posting.

    Returns
    -------
    TaxonomyResult
        Resolution result with esco_uri, resolution_step, and confidence.
        Returns step-6 fallback (raw_skill) in stub mode.
    """
    # Stub — falls through to step 6 (raw_skill).
    # Week 4: Implement 6-step resolution with ESCO store + GenAI Extension Layer.
    return TaxonomyResult(
        original_label=label,
        esco_uri=None,
        is_genai_extension=False,
        resolution_step=6,
        confidence=0.0,
    )


def resolve_taxonomy_batch(labels: list[str]) -> list[TaxonomyResult]:
    """Resolve a batch of skill labels, sharing embedding computations.

    Parameters
    ----------
    labels : list[str]
        Raw skill labels to resolve.

    Returns
    -------
    list[TaxonomyResult]
        One TaxonomyResult per input label, in the same order.
    """
    # Stub — resolves each label individually.
    # Week 4: Share embedding computations across the batch for efficiency.
    return [resolve_taxonomy(label) for label in labels]
