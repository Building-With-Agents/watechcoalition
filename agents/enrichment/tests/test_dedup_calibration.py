"""Unit tests for fuzzy dedup threshold calibration tooling."""

from __future__ import annotations

from math import sqrt

from agents.enrichment.dedup.calibration import (
    CalibrationCase,
    CalibrationPosting,
    generate_calibration_report,
    parse_thresholds,
    render_findings_markdown,
)


def _vec_for_cosine(value: float) -> list[float]:
    return [value, sqrt(max(0.0, 1.0 - (value * value)))]


def _cases() -> list[CalibrationCase]:
    return [
        CalibrationCase(
            case_id="tp-positive",
            expected_duplicate=True,
            same_company=True,
            days_apart=2,
            current=CalibrationPosting(
                job_title="Senior Data Engineer",
                company_name="Northwind Health",
                requirements="Build Airflow pipelines and SQL warehouse models.",
            ),
            candidate=CalibrationPosting(
                job_title="Senior Data Engineer",
                company_name="Northwind Health",
                requirements="Build Airflow pipelines and SQL warehouse models with analytics teams.",
            ),
        ),
        CalibrationCase(
            case_id="fp-negative",
            expected_duplicate=False,
            same_company=True,
            days_apart=3,
            current=CalibrationPosting(
                job_title="Operations Specialist",
                company_name="Evergreen Municipal Services",
                requirements="Coordinate procurement paperwork and vendor invoices.",
            ),
            candidate=CalibrationPosting(
                job_title="Operations Specialist",
                company_name="Evergreen Municipal Services",
                requirements="Dispatch field crews and emergency work orders.",
            ),
        ),
        CalibrationCase(
            case_id="fn-positive",
            expected_duplicate=True,
            same_company=True,
            days_apart=5,
            current=CalibrationPosting(
                job_title="Customer Success Manager",
                company_name="Summit Practice Software",
                requirements="Lead onboarding and drive renewal risk reviews.",
            ),
            candidate=CalibrationPosting(
                job_title="Customer Success Manager",
                company_name="Summit Practice Software",
                requirements="Drive adoption and lead onboarding plans.",
            ),
        ),
        CalibrationCase(
            case_id="tn-cross-company",
            expected_duplicate=False,
            same_company=False,
            days_apart=2,
            current=CalibrationPosting(
                job_title="Senior Data Engineer",
                company_name="Northwind Health",
                requirements="Build Airflow pipelines and SQL warehouse models.",
            ),
            candidate=CalibrationPosting(
                job_title="Senior Data Engineer",
                company_name="Harbor Retail Group",
                requirements="Build Airflow pipelines and SQL warehouse models.",
            ),
        ),
    ]


def test_generate_calibration_report_tracks_fp_and_fn_rates() -> None:
    cases = _cases()
    vectors = {
        cases[0].current.dedup_text(): [1.0, 0.0],
        cases[0].candidate.dedup_text(): _vec_for_cosine(0.96),
        cases[1].current.dedup_text(): [1.0, 0.0],
        cases[1].candidate.dedup_text(): _vec_for_cosine(0.93),
        cases[2].current.dedup_text(): [1.0, 0.0],
        cases[2].candidate.dedup_text(): _vec_for_cosine(0.91),
    }
    calls: list[tuple[tuple[str, ...], str]] = []

    def fake_embed(texts: list[str], *, audit_agent_name: str) -> list[list[float]]:
        calls.append((tuple(texts), audit_agent_name))
        return [vectors[text] for text in texts]

    report = generate_calibration_report(
        cases,
        source_path="agents/eval/dedup_threshold_calibration_cases.json",
        thresholds=[0.92],
        default_threshold=0.92,
        audit_agent_name="enrichment-dedup-calibration",
        embed_texts=fake_embed,
    )

    summary = report.summary_for_threshold(0.92)
    assert summary.true_positive == 1
    assert summary.false_positive == 1
    assert summary.true_negative == 1
    assert summary.false_negative == 1
    assert summary.eligible_cases == 3
    assert summary.compared_cases == 4
    assert summary.false_positive_rate == 0.5
    assert summary.false_negative_rate == 0.5
    assert summary.precision == 0.5
    assert summary.recall == 0.5
    assert summary.accuracy == 0.5

    decisions = {result.case_id: result for result in report.case_results}
    assert decisions["tp-positive"].decision == "tp"
    assert decisions["fp-negative"].decision == "fp"
    assert decisions["fn-positive"].decision == "fn"
    assert decisions["tn-cross-company"].decision == "tn"
    assert decisions["tn-cross-company"].similarity is None
    assert decisions["tn-cross-company"].eligible_by_scope is False

    assert len(calls) == 1
    embedded_texts, audit_name = calls[0]
    assert audit_name == "enrichment-dedup-calibration"
    assert cases[3].candidate.dedup_text() not in embedded_texts


def test_parse_thresholds_includes_default_and_dedupes() -> None:
    assert parse_thresholds("0.90,0.92,0.92", default_threshold=0.94) == [0.9, 0.92, 0.94]


def test_render_findings_markdown_includes_required_sections() -> None:
    cases = _cases()[:2]

    def fake_embed(texts: list[str], *, audit_agent_name: str) -> list[list[float]]:
        del audit_agent_name
        mapping = {
            cases[0].current.dedup_text(): [1.0, 0.0],
            cases[0].candidate.dedup_text(): _vec_for_cosine(0.96),
            cases[1].current.dedup_text(): [1.0, 0.0],
            cases[1].candidate.dedup_text(): _vec_for_cosine(0.89),
        }
        return [mapping[text] for text in texts]

    report = generate_calibration_report(
        cases,
        source_path="agents/eval/dedup_threshold_calibration_cases.json",
        thresholds=[0.9, 0.92],
        default_threshold=0.92,
        embed_texts=fake_embed,
    )

    out = render_findings_markdown(report)

    assert "## What I Tested" in out
    assert "## What I Found" in out
    assert "## Recommendation" in out
    assert "## Tradeoffs Acknowledged" in out
    assert "## Data / Evidence" in out
    assert "| Threshold | TP | FP | TN | FN | Precision | Recall | FPR | FNR |" in out
    assert "`0.92`" in out
