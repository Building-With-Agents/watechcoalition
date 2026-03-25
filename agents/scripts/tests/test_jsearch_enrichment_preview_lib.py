"""Unit tests for jsearch_enrichment_preview_lib (no DB)."""

from __future__ import annotations

from agents.scripts.jsearch_enrichment_preview_lib import (
    build_enrichment_output_record,
    build_extraction_dict,
)


def test_build_extraction_dict_empty() -> None:
    assert build_extraction_dict(None, None, None, None, None) is None
    assert build_extraction_dict([], [], [], [], []) is None


def test_build_extraction_dict_with_skills() -> None:
    d = build_extraction_dict([{"skill_name": "Python"}], [], [], [], [])
    assert d is not None
    assert d["skills"] == [{"skill_name": "Python"}]
    assert d["tools"] == []


def test_build_enrichment_output_record_uses_classify() -> None:
    tech = [("1", "Software Engineering")]
    rec = build_enrichment_output_record(
        normalized_job_id=42,
        source="jsearch",
        external_id="ext-1",
        job_title="Junior Software Engineer",
        job_description=None,
        skills=[],
        tools=[],
        tasks=[],
        responsibilities=[],
        context=[],
        technology_areas=tech,
        industry_sectors=[],
        job_posting_id=None,
        is_internship=False,
    )
    assert rec["normalized_job_id"] == 42
    assert rec["source"] == "jsearch"
    assert rec["external_id"] == "ext-1"
    assert rec["job_posting_id"] is None
    assert rec["seniority"] == "junior"
    assert rec["role_classification"] == "Software Engineering"
    assert "quality_score" in rec
    assert isinstance(rec["quality_score"], float)
    assert 0.0 <= rec["quality_score"] <= 1.0
    assert "quality_components" in rec


def test_build_enrichment_output_record_internship() -> None:
    rec = build_enrichment_output_record(
        normalized_job_id=1,
        source="jsearch",
        external_id="x",
        job_title="Engineer",
        job_description=None,
        skills=[],
        tools=[],
        tasks=[],
        responsibilities=[],
        context=[],
        technology_areas=[],
        industry_sectors=[],
        job_posting_id="jp-99",
        is_internship=True,
    )
    assert rec["seniority"] == "intern"
    assert rec["job_posting_id"] == "jp-99"
