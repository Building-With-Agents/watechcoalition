"""Unit tests for deterministic quality scoring."""

from __future__ import annotations

from agents.enrichment.classifiers.quality import score_quality


def test_score_quality_empty_is_low_but_bounded() -> None:
    r = score_quality(
        job_title="",
        job_description=None,
        extraction=None,
        extraction_failed=False,
    )
    assert 0.0 <= r.quality_score <= 1.0
    assert r.components["completeness"] == 0.0


def test_score_quality_rich_posting_scores_higher() -> None:
    thin = score_quality(
        job_title="Job",
        job_description="Short.",
        extraction=None,
        extraction_failed=False,
    )
    rich = score_quality(
        job_title="Senior Machine Learning Engineer",
        job_description=(
            "Responsibilities:\n"
            "- Build ML pipelines on AWS\n"
            "- Partner with data science on deep learning models\n"
            "- Requirements: Python, PyTorch, SQL\n\n"
            "We use Kubernetes and TensorFlow in production."
        ),
        extraction={
            "skills": [{"skill_name": "Python"}],
            "tools": [{"tool_name": "Docker"}],
            "tasks": [],
            "responsibilities": [],
            "context": [],
        },
        extraction_failed=False,
    )
    assert rich.quality_score > thin.quality_score
    assert rich.components["structural_coherence"] >= thin.components["structural_coherence"]


def test_extraction_failed_soft_penalty() -> None:
    base = score_quality(
        job_title="Data Engineer",
        job_description="We need someone to build ETL pipelines with SQL and Spark.",
        extraction={"skills": [{"label": "SQL"}], "tools": [], "tasks": [], "responsibilities": [], "context": []},
        extraction_failed=False,
    )
    failed = score_quality(
        job_title="Data Engineer",
        job_description="We need someone to build ETL pipelines with SQL and Spark.",
        extraction={"skills": [{"label": "SQL"}], "tools": [], "tasks": [], "responsibilities": [], "context": []},
        extraction_failed=True,
    )
    assert failed.quality_score <= base.quality_score


def test_component_keys() -> None:
    r = score_quality(job_title="X", job_description="Y " * 50, extraction=None, extraction_failed=False)
    assert set(r.components.keys()) == {
        "completeness",
        "clarity",
        "ai_keyword_density",
        "structural_coherence",
    }
