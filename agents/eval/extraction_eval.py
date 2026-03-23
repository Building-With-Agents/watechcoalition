"""Evaluation harness for skills/tools extraction — Week 4.

Compares extraction output against hand-labeled ground truth. Supports both
extraction_ground_truth.json (skills with "label") and ground-truth-labeler
export (skills with "skill_name") for schema compatibility.
"""

import json
from pathlib import Path
from typing import Any

from agents.common.types import JobRecord
from agents.skills_extraction.extractors.skills import extract_skills
from agents.skills_extraction.extractors.tools import extract_tools

GROUND_TRUTH_PATH = Path(__file__).parent / "extraction_ground_truth.json"


def _gt_optional_text(value: object) -> str | None:
    """Ground-truth optional string: None if missing or blank after strip."""
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    return None


def ground_truth_row_to_job_record(job: dict) -> JobRecord:
    """Map a ground-truth JSON object to a normalized JobRecord for extractors.

    Required for JobRecord validation: non-empty title and company.
    Ground truth uses ``state``; JobRecord field is ``state_province``.
    """
    title = (job.get("title") or "").strip()
    company = (job.get("company") or "").strip()
    source = (job.get("source") or "eval").strip()
    external_id = (job.get("external_id") or job.get("ground_truth_id") or "unknown").strip()
    return JobRecord(
        raw_job_id=0,
        ingestion_run_id="",
        region_id="",
        source=source,
        external_id=external_id,
        title=title,
        company=company,
        description=_gt_optional_text(job.get("description")),
        requirements=_gt_optional_text(job.get("requirements")),
        responsibilities=_gt_optional_text(job.get("responsibilities")),
        city=_gt_optional_text(job.get("city")),
        state_province=_gt_optional_text(job.get("state")),
        country=_gt_optional_text(job.get("country")),
        mapper_used="eval-harness",
    )


def predict_skills_and_tools(job_record: JobRecord) -> dict[str, Any]:
    """Production-like Pass 1 + Pass 2; returns plain name lists plus skills metadata."""
    tools = extract_tools(job_record)
    skills, metadata = extract_skills(job_record, pass1_tools=tools)
    return {
        "skills": [s.skill_name for s in skills],
        "tools": [t.tool_name for t in tools],
        "metadata": metadata,
    }


def load_ground_truth(path: Path | str):
    path = Path(path) if isinstance(path, str) else path
    with open(path) as f:  # noqa: UP015
        return json.load(f)


def normalize_list(items):
    return {i.lower().strip() for i in items}


def compute_metrics(pred: set, true: set):
    precision = 0.0 if len(pred) == 0 else len(pred & true) / len(pred)
    recall = 0.0 if len(true) == 0 else len(pred & true) / len(true)
    f1 = (
        (2 * precision * recall / (precision + recall))
        if (precision + recall) > 0
        else 0.0
    )
    return precision, recall, f1


def _log(msg: str) -> None:
    """Print eval output — CLI reporting tool, not library code."""
    print(msg)  # noqa: T201


def _skill_label(s: dict) -> str:
    """Ground truth skill: support both 'label' (legacy) and 'skill_name' (labeler export)."""
    return s.get("label") or s.get("skill_name") or ""


def run_eval(ground_truth_path: str | Path) -> None:
    data = load_ground_truth(ground_truth_path)

    total_pred_skills = 0
    total_true_skills = 0
    total_matched_skills = 0

    total_pred_tools = 0
    total_true_tools = 0
    total_matched_tools = 0

    for job in data:
        job_record = ground_truth_row_to_job_record(job)
        pred = predict_skills_and_tools(job_record)

        gt_skills = normalize_list([_skill_label(s) for s in job["skills"] if _skill_label(s)])
        gt_tools = normalize_list([t.get("tool_name") or "" for t in job["tools"] if t.get("tool_name")])

        pred_skills = normalize_list(pred.get("skills", []))
        pred_tools = normalize_list(pred.get("tools", []))

        p_s, r_s, f_s = compute_metrics(pred_skills, gt_skills)
        p_t, r_t, f_t = compute_metrics(pred_tools, gt_tools)

        matched_skills = pred_skills & gt_skills
        matched_tools = pred_tools & gt_tools

        total_pred_skills += len(pred_skills)
        total_true_skills += len(gt_skills)
        total_matched_skills += len(matched_skills)

        total_pred_tools += len(pred_tools)
        total_true_tools += len(gt_tools)
        total_matched_tools += len(matched_tools)

        _log(f"\n--- {job['title']} ---")
        if pred.get("metadata", {}).get("extraction_failed"):
            _log("Skills pass: extraction_failed=true (see extractor metadata)")
        _log(f"GT Skills:   {gt_skills}")
        _log(f"Pred Skills: {pred_skills}")
        _log(f"Match:       {pred_skills & gt_skills}")
        _log(f"GT Tools:    {gt_tools}")
        _log(f"Pred Tools:  {pred_tools}")
        _log(f"Match:       {pred_tools & gt_tools}")
        _log(f"Skills P/R/F1: {p_s:.2f} / {r_s:.2f} / {f_s:.2f}")
        _log(f"Tools  P/R/F1: {p_t:.2f} / {r_t:.2f} / {f_t:.2f}")

    _log("\n=== FINAL METRICS ===")
    _log(f"Total GT Skills: {total_true_skills}")
    _log(f"Total Pred Skills: {total_pred_skills}")
    _log(f"Matched Skills: {total_matched_skills}")

    precision_skills = total_matched_skills / total_pred_skills if total_pred_skills > 0 else 0.0
    recall_skills = total_matched_skills / total_true_skills if total_true_skills > 0 else 0.0
    f1_skills = (
        (2 * precision_skills * recall_skills / (precision_skills + recall_skills))
        if (precision_skills + recall_skills) > 0
        else 0.0
    )

    _log(f"Skills Precision: {precision_skills:.2f}")
    _log(f"Skills Recall:    {recall_skills:.2f}")
    _log(f"Skills F1:        {f1_skills:.2f}")

    _log("\n--- TOOLS ---")
    _log(f"Total GT Tools: {total_true_tools}")
    _log(f"Total Pred Tools: {total_pred_tools}")
    _log(f"Matched Tools: {total_matched_tools}")

    precision_tools = total_matched_tools / total_pred_tools if total_pred_tools > 0 else 0.0
    recall_tools = total_matched_tools / total_true_tools if total_true_tools > 0 else 0.0
    f1_tools = (
        (2 * precision_tools * recall_tools / (precision_tools + recall_tools))
        if (precision_tools + recall_tools) > 0
        else 0.0
    )

    _log(f"Tools Precision: {precision_tools:.2f}")
    _log(f"Tools Recall:    {recall_tools:.2f}")
    _log(f"Tools F1:        {f1_tools:.2f}")


if __name__ == "__main__":
    run_eval(GROUND_TRUTH_PATH)
