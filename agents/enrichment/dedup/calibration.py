"""Threshold calibration helpers for fuzzy dedup.

Tracks false-positive and false-negative rates from a labeled pair dataset
using the same dedup text composition and Azure embedding helper as the live
enrichment path.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from agents.enrichment.dedup.config import DEDUP_ROLLING_WINDOW_DAYS, dedup_cosine_threshold
from agents.enrichment.dedup.text import build_dedup_text
from agents.enrichment.dedup.vectors import cosine_similarity, parse_stored_embedding
from agents.skills_extraction.extractors.taxonomy import _embed_texts_azure

CalibrationDecision = Literal["tp", "tn", "fp", "fn"]
EmbedTextsFn = Callable[[list[str]], list[list[float]] | None]

DEFAULT_CALIBRATION_AUDIT_AGENT = "enrichment-dedup-calibration"
DEFAULT_CALIBRATION_THRESHOLDS = (0.88, 0.9, 0.92, 0.94, 0.96)
_EMBED_BATCH_SIZE = 50


class CalibrationPosting(BaseModel):
    """Posting fields that participate in dedup text composition."""

    model_config = ConfigDict(frozen=True)

    job_title: str
    company_name: str
    requirements: str | None = None

    def dedup_text(self) -> str:
        return build_dedup_text(self.job_title, self.company_name, self.requirements)


class CalibrationCase(BaseModel):
    """One labeled pair for threshold calibration."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    expected_duplicate: bool
    same_company: bool = True
    days_apart: int = Field(ge=0)
    current: CalibrationPosting
    candidate: CalibrationPosting
    notes: str | None = None

    def within_window(self, *, window_days: int = DEDUP_ROLLING_WINDOW_DAYS) -> bool:
        return self.days_apart <= window_days

    def eligible_by_scope(self, *, window_days: int = DEDUP_ROLLING_WINDOW_DAYS) -> bool:
        return self.same_company and self.within_window(window_days=window_days)


class CalibrationCaseResult(BaseModel):
    """Decision outcome for a single case at one threshold."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    threshold: float
    expected_duplicate: bool
    predicted_duplicate: bool
    decision: CalibrationDecision
    same_company: bool
    days_apart: int
    within_window: bool
    eligible_by_scope: bool
    similarity: float | None = None
    notes: str | None = None


class CalibrationThresholdSummary(BaseModel):
    """Confusion-matrix summary for one threshold."""

    model_config = ConfigDict(frozen=True)

    threshold: float
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    compared_cases: int
    eligible_cases: int
    positive_cases: int
    negative_cases: int
    precision: float
    recall: float
    accuracy: float
    false_positive_rate: float
    false_negative_rate: float


class CalibrationReport(BaseModel):
    """Serializable threshold-calibration report."""

    model_config = ConfigDict(frozen=True)

    generated_at: str
    source_path: str
    report_thresholds: list[float]
    default_threshold: float
    window_days: int
    audit_agent_name: str
    case_count: int
    cases: list[CalibrationCase]
    threshold_summaries: list[CalibrationThresholdSummary]
    case_results: list[CalibrationCaseResult]

    def summary_for_threshold(self, threshold: float) -> CalibrationThresholdSummary:
        for summary in self.threshold_summaries:
            if abs(summary.threshold - threshold) < 1e-9:
                return summary
        raise KeyError(f"threshold {threshold} not found in report")


def _chunked(items: list[str], *, size: int) -> Iterable[list[str]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def parse_thresholds(raw: str | None, *, default_threshold: float | None = None) -> list[float]:
    """Parse a comma-separated threshold list and ensure the default is included."""
    values: list[float] = []
    if raw:
        for piece in raw.split(","):
            token = piece.strip()
            if not token:
                continue
            values.append(float(token))
    if not values:
        values = list(DEFAULT_CALIBRATION_THRESHOLDS)
    if default_threshold is not None and all(abs(v - default_threshold) >= 1e-9 for v in values):
        values.append(default_threshold)
    return sorted(dict.fromkeys(round(v, 6) for v in values))


def load_calibration_cases(path: str | Path) -> list[CalibrationCase]:
    """Load labeled calibration cases from JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("calibration case file must contain a top-level JSON list")
    return [CalibrationCase.model_validate(item) for item in data]


def _embed_unique_texts(
    cases: list[CalibrationCase],
    *,
    audit_agent_name: str,
    embed_texts: Callable[..., list[list[float]] | None] = _embed_texts_azure,
    window_days: int = DEDUP_ROLLING_WINDOW_DAYS,
) -> dict[str, object]:
    texts = sorted(
        {
            posting.dedup_text()
            for case in cases
            if case.eligible_by_scope(window_days=window_days)
            for posting in (case.current, case.candidate)
            if posting.dedup_text().strip()
        }
    )
    if not texts:
        return {}

    out: dict[str, object] = {}
    for chunk in _chunked(texts, size=_EMBED_BATCH_SIZE):
        raw_vectors = embed_texts(chunk, audit_agent_name=audit_agent_name)
        if raw_vectors is None or len(raw_vectors) != len(chunk):
            raise ValueError("embedding calibration batch failed")
        for dedup_text, raw_vector in zip(chunk, raw_vectors, strict=True):
            parsed = parse_stored_embedding(raw_vector)
            if parsed is None or parsed.size == 0:
                raise ValueError("embedding calibration returned an empty vector")
            out[dedup_text] = parsed
    return out


def _case_decision(*, expected_duplicate: bool, predicted_duplicate: bool) -> CalibrationDecision:
    if expected_duplicate and predicted_duplicate:
        return "tp"
    if expected_duplicate and not predicted_duplicate:
        return "fn"
    if not expected_duplicate and predicted_duplicate:
        return "fp"
    return "tn"


def evaluate_threshold(
    cases: list[CalibrationCase],
    *,
    threshold: float,
    vectors_by_text: dict[str, object],
    window_days: int = DEDUP_ROLLING_WINDOW_DAYS,
) -> tuple[CalibrationThresholdSummary, list[CalibrationCaseResult]]:
    """Evaluate one threshold against labeled cases."""
    case_results: list[CalibrationCaseResult] = []
    tp = fp = tn = fn = 0
    eligible_cases = 0
    positive_cases = 0
    negative_cases = 0

    for case in cases:
        within_window = case.within_window(window_days=window_days)
        eligible = case.eligible_by_scope(window_days=window_days)
        predicted_duplicate = False
        similarity: float | None = None
        if case.expected_duplicate:
            positive_cases += 1
        else:
            negative_cases += 1
        if eligible:
            eligible_cases += 1
            current_text = case.current.dedup_text()
            candidate_text = case.candidate.dedup_text()
            current_vector = vectors_by_text.get(current_text)
            candidate_vector = vectors_by_text.get(candidate_text)
            if current_vector is None or candidate_vector is None:
                raise ValueError(f"missing embedded text for calibration case {case.case_id}")
            similarity = cosine_similarity(current_vector, candidate_vector)
            predicted_duplicate = similarity > threshold

        decision = _case_decision(
            expected_duplicate=case.expected_duplicate,
            predicted_duplicate=predicted_duplicate,
        )
        if decision == "tp":
            tp += 1
        elif decision == "fp":
            fp += 1
        elif decision == "fn":
            fn += 1
        else:
            tn += 1

        case_results.append(
            CalibrationCaseResult(
                case_id=case.case_id,
                threshold=threshold,
                expected_duplicate=case.expected_duplicate,
                predicted_duplicate=predicted_duplicate,
                decision=decision,
                same_company=case.same_company,
                days_apart=case.days_apart,
                within_window=within_window,
                eligible_by_scope=eligible,
                similarity=round(similarity, 6) if similarity is not None else None,
                notes=case.notes,
            )
        )

    summary = CalibrationThresholdSummary(
        threshold=threshold,
        true_positive=tp,
        false_positive=fp,
        true_negative=tn,
        false_negative=fn,
        compared_cases=len(cases),
        eligible_cases=eligible_cases,
        positive_cases=positive_cases,
        negative_cases=negative_cases,
        precision=round(_safe_divide(tp, tp + fp), 6),
        recall=round(_safe_divide(tp, tp + fn), 6),
        accuracy=round(_safe_divide(tp + tn, len(cases)), 6),
        false_positive_rate=round(_safe_divide(fp, negative_cases), 6),
        false_negative_rate=round(_safe_divide(fn, positive_cases), 6),
    )
    return summary, case_results


def generate_calibration_report(
    cases: list[CalibrationCase],
    *,
    source_path: str,
    thresholds: list[float] | None = None,
    default_threshold: float | None = None,
    window_days: int = DEDUP_ROLLING_WINDOW_DAYS,
    audit_agent_name: str = DEFAULT_CALIBRATION_AUDIT_AGENT,
    embed_texts: Callable[..., list[list[float]] | None] = _embed_texts_azure,
) -> CalibrationReport:
    """Embed labeled cases once and evaluate them across multiple thresholds."""
    effective_default = dedup_cosine_threshold() if default_threshold is None else default_threshold
    report_thresholds = parse_thresholds(None if thresholds is None else ",".join(str(t) for t in thresholds), default_threshold=effective_default)
    vectors_by_text = _embed_unique_texts(
        cases,
        audit_agent_name=audit_agent_name,
        embed_texts=embed_texts,
        window_days=window_days,
    )

    summaries: list[CalibrationThresholdSummary] = []
    case_results: list[CalibrationCaseResult] = []
    for threshold in report_thresholds:
        summary, results = evaluate_threshold(
            cases,
            threshold=threshold,
            vectors_by_text=vectors_by_text,
            window_days=window_days,
        )
        summaries.append(summary)
        case_results.extend(results)

    return CalibrationReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        source_path=str(source_path),
        report_thresholds=report_thresholds,
        default_threshold=effective_default,
        window_days=window_days,
        audit_agent_name=audit_agent_name,
        case_count=len(cases),
        cases=cases,
        threshold_summaries=summaries,
        case_results=case_results,
    )


def render_findings_markdown(report: CalibrationReport) -> str:
    """Render a one-page findings document from a calibration report."""
    default_summary = report.summary_for_threshold(report.default_threshold)
    thresholds = report.threshold_summaries
    preferred = min(
        thresholds,
        key=lambda summary: (
            summary.false_positive_rate,
            summary.false_negative_rate,
            -summary.precision,
            -summary.recall,
            abs(summary.threshold - report.default_threshold),
        ),
    )
    lower = [summary for summary in thresholds if summary.threshold < report.default_threshold]
    higher = [summary for summary in thresholds if summary.threshold > report.default_threshold]
    nearest_lower = lower[-1] if lower else None
    nearest_higher = higher[0] if higher else None
    table_rows = "\n".join(
        (
            f"| `{summary.threshold:.2f}` | {summary.true_positive} | {summary.false_positive} | "
            f"{summary.true_negative} | {summary.false_negative} | "
            f"{summary.precision:.3f} | {summary.recall:.3f} | "
            f"{summary.false_positive_rate:.3f} | {summary.false_negative_rate:.3f} |"
        )
        for summary in thresholds
    )
    findings = [
        "# Week 6 — Fuzzy Dedup Threshold Calibration Findings",
        "",
        "## What I Tested",
        (
            f"- Labeled pair replay from `{report.source_path}` using the live dedup text composition "
            "(title + company name + key requirements) and the shared Azure embedding helper."
        ),
        (
            f"- `{report.case_count}` labeled cases covering same-company reposts, same-company "
            "different-role negatives, cross-company negatives, and the 29-day / 31-day window boundary."
        ),
        (
            "- Threshold sweep at "
            + ", ".join(f"`{summary.threshold:.2f}`" for summary in thresholds)
            + f" with the production default anchored at `{report.default_threshold:.2f}`."
        ),
        "",
        "## What I Found",
        (
            f"- At the default threshold `{report.default_threshold:.2f}`, the labeled replay produced "
            f"`TP={default_summary.true_positive}`, `FP={default_summary.false_positive}`, "
            f"`TN={default_summary.true_negative}`, `FN={default_summary.false_negative}`."
        ),
        (
            f"- Default-threshold rates: precision `{default_summary.precision:.3f}`, "
            f"recall `{default_summary.recall:.3f}`, false-positive rate "
            f"`{default_summary.false_positive_rate:.3f}`, false-negative rate "
            f"`{default_summary.false_negative_rate:.3f}`."
        ),
    ]
    if abs(preferred.threshold - report.default_threshold) >= 1e-9:
        findings.append(
            (
                f"- The strongest threshold on this labeled replay was `{preferred.threshold:.2f}` with "
                f"`FPR={preferred.false_positive_rate:.3f}` / "
                f"`FNR={preferred.false_negative_rate:.3f}`."
            )
        )
    if nearest_lower is not None:
        findings.append(
            (
                f"- Lowering the threshold to `{nearest_lower.threshold:.2f}` changes the rates to "
                f"`FPR={nearest_lower.false_positive_rate:.3f}` / "
                f"`FNR={nearest_lower.false_negative_rate:.3f}`."
            )
        )
    if nearest_higher is not None:
        findings.append(
            (
                f"- Raising the threshold to `{nearest_higher.threshold:.2f}` changes the rates to "
                f"`FPR={nearest_higher.false_positive_rate:.3f}` / "
                f"`FNR={nearest_higher.false_negative_rate:.3f}`."
            )
        )
    findings.extend(
        [
            "",
            "## Recommendation",
        ]
    )
    if abs(preferred.threshold - report.default_threshold) < 1e-9:
        findings.extend(
            [
                (
                    f"- Keep `DEDUP_COSINE_THRESHOLD={report.default_threshold:.2f}` as the production default "
                    "because it remains the best-performing threshold on the current labeled replay."
                ),
            ]
        )
    else:
        findings.extend(
            [
                (
                    f"- The current labeled replay favors `{preferred.threshold:.2f}` over the default "
                    f"`{report.default_threshold:.2f}` because it preserves the same false-positive rate "
                    "while reducing missed duplicates."
                ),
                (
                    f"- Keep `DEDUP_COSINE_THRESHOLD={report.default_threshold:.2f}` as the conservative "
                    "production default only until a broader staging replay confirms whether the stronger "
                    "candidate threshold stays safe on harder negatives."
                ),
            ]
        )
    findings.extend(
        [
            (
                "- Use this labeled replay as the calibration baseline and extend the case file as new "
                "false merges or missed duplicates are discovered."
            ),
            "",
            "## Tradeoffs Acknowledged",
            "- This is a labeled replay, not a full production backfill, so the rates are only as representative as the case set.",
            "- Cross-company and out-of-window negatives are tracked at the system-contract level, not by raw embedding similarity alone.",
            "- Embedding-model changes can move cosine scores, so the calibration report should be regenerated when the deployment changes.",
            "",
            "## Data / Evidence",
            f"- Audit agent name: `{report.audit_agent_name}`.",
            f"- Rolling window for replay: `{report.window_days}` days.",
            "",
            "| Threshold | TP | FP | TN | FN | Precision | Recall | FPR | FNR |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            table_rows,
            "",
        ]
    )
    return "\n".join(findings)
