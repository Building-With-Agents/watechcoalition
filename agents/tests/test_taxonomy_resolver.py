"""Tests for taxonomy resolution (6-step resolver, batch, resolution_stats).

Step 4 tests use pytest's monkeypatch to mock _embed_texts_azure so no live
Azure API calls are made (avoids cost, latency, and flakiness in CI).
"""

from __future__ import annotations

from agents.common.types import TaxonomyResult
from agents.skills_extraction.extractors.taxonomy import (
    resolution_stats,
    resolve_taxonomy,
    resolve_taxonomy_batch,
)

# Dummy embedding to simulate Azure OpenAI (text-embedding-3-small is 1536-dim)
def _mock_embed_texts_azure(texts: list[str]) -> list[list[float]] | None:
    if not texts:
        return []
    return [[0.01] * 1536 for _ in texts]


class TestResolveTaxonomy:
    """resolve_taxonomy returns TaxonomyResult with correct step and shape."""

    def test_returns_taxonomy_result(self) -> None:
        r = resolve_taxonomy("ABAP")
        assert isinstance(r, TaxonomyResult)
        assert r.original_label == "ABAP"
        assert r.resolution_step in (1, 2, 3, 4, 5, 6)
        assert 0 <= r.confidence <= 1

    def test_step1_genai_extension_match(self) -> None:
        """GenAI Extension Layer: skill name (or normalized) matches at step 1 when parent exists in ESCO."""
        # "Vector Database Management" -> "Database management" -> alias "manage database" (present in ESCO).
        # "Prompt Engineering" -> "Digital content creation" has no matching parent in esco_digital_skills.json.
        r = resolve_taxonomy("Vector Database Management")
        assert r.resolution_step == 1
        assert r.is_genai_extension is True
        assert r.esco_uri is not None
        assert r.esco_label is not None
        assert r.confidence == 1.0
        # Normalized form (lowercase) also matches
        r2 = resolve_taxonomy("vector database management")
        assert r2.resolution_step == 1
        assert r2.is_genai_extension is True

    def test_step2_exact_match_esco(self) -> None:
        """Known ESCO preferred_label matches at step 2."""
        r = resolve_taxonomy("ABAP")
        assert r.resolution_step == 2
        assert r.esco_uri is not None
        assert r.esco_label is not None
        assert r.is_genai_extension is False

    def test_step2_or_step3_case_insensitive(self) -> None:
        """Lowercase 'abap' can match at step 2 (case-insensitive exact) or step 3; both are correct."""
        r = resolve_taxonomy("abap")
        assert r.resolution_step in (2, 3)
        assert r.esco_uri is not None
        assert r.esco_label is not None

    def test_step3_normalized_match(self) -> None:
        """Input that matches only after normalization (e.g. collapsed spaces) resolves at step 3."""
        # "align  software  with  system  architectures" normalizes to "align software with system architectures";
        # step 2 compares raw lowercased string, so double spaces prevent step 2 match.
        r = resolve_taxonomy("align  software  with  system  architectures")
        assert r.resolution_step == 3
        assert r.esco_uri is not None
        assert r.esco_label is not None

    def test_step4_embedding_match(self, monkeypatch) -> None:
        """Label that does not match steps 1–3 resolves at step 4 via monkeypatched API."""
        monkeypatch.setattr(
            "agents.skills_extraction.extractors.taxonomy._esco_embedding_meta",
            None,
        )
        monkeypatch.setattr(
            "agents.skills_extraction.extractors.taxonomy._esco_normalized_matrix",
            None,
        )
        monkeypatch.setattr(
            "agents.skills_extraction.extractors.taxonomy._embed_texts_azure",
            _mock_embed_texts_azure,
        )
        monkeypatch.setenv("SKILL_TAXONOMY_SIMILARITY_THRESHOLD", "0.0")
        r = resolve_taxonomy("using ABAP for development")
        assert r.resolution_step == 4
        assert r.esco_uri is not None
        assert r.esco_label is not None
        assert r.is_genai_extension is False

    def test_step6_unknown_skill(self) -> None:
        """Unknown label falls through to step 6."""
        r = resolve_taxonomy("Some Unknown Skill XYZ 123")
        assert r.resolution_step == 6
        assert r.esco_uri is None
        assert r.esco_label is None
        assert r.is_genai_extension is False
        assert r.confidence == 0.0

    def test_empty_label_step6(self) -> None:
        r = resolve_taxonomy("")
        assert r.resolution_step == 6
        assert r.original_label == ""


class TestResolveTaxonomyBatch:
    """resolve_taxonomy_batch preserves order and dedupes."""

    def test_same_order_as_input(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "agents.skills_extraction.extractors.taxonomy._embed_texts_azure",
            _mock_embed_texts_azure,
        )
        labels = ["ABAP", "Unknown", "abap", "ABAP"]
        results = resolve_taxonomy_batch(labels)
        assert len(results) == 4
        assert results[0].original_label == "ABAP"
        assert results[1].original_label == "Unknown"
        assert results[2].original_label == "abap"
        assert results[3].original_label == "ABAP"

    def test_dedupe_same_result_for_same_label(self) -> None:
        labels = ["ABAP", "ABAP"]
        results = resolve_taxonomy_batch(labels)
        assert results[0].esco_uri == results[1].esco_uri
        assert results[0].resolution_step == results[1].resolution_step


class TestResolutionStats:
    """resolution_stats returns per-step counts."""

    def test_counts_all_steps(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "agents.skills_extraction.extractors.taxonomy._embed_texts_azure",
            _mock_embed_texts_azure,
        )
        labels = ["ABAP", "Unknown XYZ", "abap"]
        results = resolve_taxonomy_batch(labels)
        stats = resolution_stats(results)
        assert list(stats.keys()) == [1, 2, 3, 4, 5, 6]
        assert sum(stats.values()) == 3

    def test_coverage_formula(self, monkeypatch) -> None:
        monkeypatch.setattr(
            "agents.skills_extraction.extractors.taxonomy._embed_texts_azure",
            _mock_embed_texts_azure,
        )
        results = resolve_taxonomy_batch(["ABAP", "Unknown", "abap"])
        stats = resolution_stats(results)
        total = sum(stats.values())
        resolved_1_5 = total - stats.get(6, 0)
        coverage = (resolved_1_5 / total * 100) if total else 0
        assert 0 <= coverage <= 100
