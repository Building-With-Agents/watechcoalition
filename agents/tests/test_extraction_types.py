"""Tests for Week 4 extraction schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agents.common.types import ExtractionMetadata, SkillRecord, SpanRecord, ToolRecord


def test_span_record_accepts_legacy_char_aliases() -> None:
    """Legacy scaffold field names still parse into the canonical span schema."""
    span = SpanRecord(
        text="Python",
        field_source="description",
        char_start=10,
        char_end=16,
    )

    assert span.start_char == 10
    assert span.end_char == 16


def test_span_record_auto_corrects_mismatched_offsets() -> None:
    """SpanRecord auto-corrects end_char to match start_char + len(text)."""
    span = SpanRecord(
        text="AWS",
        field_source="description",
        start_char=5,
        end_char=10,  # wrong — should be 8
    )
    assert span.end_char == 8  # auto-corrected: 5 + len("AWS") = 8


def test_tool_record_accepts_legacy_label_alias() -> None:
    """ToolRecord keeps compatibility with the scaffold's older `label` field."""
    record = ToolRecord(
        label="Docker",
        category="platform",
        confidence=0.98,
        source_span=SpanRecord(
            text="Docker",
            field_source="requirements",
            start_char=0,
            end_char=6,
        ),
    )

    assert record.tool_name == "Docker"
    assert record.is_genai_tool is False


def test_skill_record_requires_source_span() -> None:
    """Skill provenance is mandatory in the Week 4 contract."""
    with pytest.raises(ValidationError):
        SkillRecord(
            label="Leadership",
            type="Soft",
            confidence=0.85,
        )


def test_extraction_metadata_accepts_legacy_field_names() -> None:
    """Legacy scaffold metadata fields map onto the canonical Week 4 names."""
    metadata = ExtractionMetadata(
        extraction_version="0.1.0",
        extraction_model="gpt-4o-mini",
        extraction_tokens_used=321,
        extraction_cost_usd=0.012,
        pass1_pattern_matches=4,
    )

    assert metadata.model_used == "gpt-4o-mini"
    assert metadata.tokens_used == 321
    assert metadata.cost_usd == 0.012
    assert metadata.pass1_tool_count == 4
