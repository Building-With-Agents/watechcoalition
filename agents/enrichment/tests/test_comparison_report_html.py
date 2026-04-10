"""Tests for comparison_report_html."""

from __future__ import annotations

from agents.enrichment.comparison_report_html import render_enrichment_comparison_html


def test_render_contains_posting_and_enrichment() -> None:
    html = render_enrichment_comparison_html(
        [
            {
                "normalized_job_id": 7,
                "job_posting_id": None,
                "source": "jsearch",
                "external_id": "abc",
                "seniority": "senior",
                "role_classification": "Data Engineering",
                "quality_score": 0.8125,
                "quality_components": {"completeness": 0.5, "clarity": 0.5},
                "job_title": "Senior Data Engineer",
                "job_company": "Acme",
                "job_description": "Build pipelines.\nUse SQL.",
                "job_city": "Austin",
                "job_state": "TX",
                "job_url": "https://example.com/j/1",
            }
        ],
        page_title="Test report",
        subtitle="run-123",
    )
    assert "Senior Data Engineer" in html
    assert "Acme" in html
    assert "Build pipelines" in html
    assert "senior" in html
    assert "Data Engineering" in html
    assert "jsearch" in html
    assert "abc" in html
    assert "https://example.com/j/1" in html
    assert "0.8125" in html
    assert "completeness" in html


def test_render_escapes_xss_in_title() -> None:
    html = render_enrichment_comparison_html(
        [
            {
                "normalized_job_id": 1,
                "source": "x",
                "external_id": "y",
                "seniority": "mid",
                "role_classification": "A",
                "job_title": "<script>alert(1)</script>",
                "job_company": "",
                "job_description": "",
            }
        ]
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
