"""Evaluation harness for skills/tools extraction — Week 4.

Compares extraction output against hand-labeled ground truth. Supports both
extraction_ground_truth.json (skills with "label") and ground-truth-labeler
export (skills with "skill_name") for schema compatibility.

Matching strategy (issue #84)
---------------------------
**Strict metrics:** After ``_normalize_label``, labels are compared as sets
(exact string equality on the normalized form). This removes trivial noise
(case, whitespace, ``&`` vs ``and``, common long-form phrases → short tokens)
while still penalizing real semantic mismatches.

**Fuzzy metrics:** Pairs (pred, ground_truth) use ``rapidfuzz.fuzz.token_set_ratio``
(0-100). Token-set ratio ignores word order and is lenient when one string is
a subset of the other's token bag (e.g. ``ai ml`` vs ``ai ml lifecycle``),
which separates *measurement noise* from systematic extraction gaps.

**Assignment:** All pairs scoring ≥ ``EVAL_EXTRACTION_FUZZY_THRESHOLD`` are
sorted by score descending; a greedy **1:1** match picks each label at most
once per side so one prediction cannot credit multiple GT items (and vice
versa).

**Threshold default (85):** Token-set is already permissive; 85 balances
near-equivalent phrasing against false positives. Raise for stricter fuzzy
eval; lower when exploring prompt changes and recall matters more. Override via
``EVAL_EXTRACTION_FUZZY_THRESHOLD``.

**Abbreviations:** Only unambiguous multi-word phrases are mapped to canonical
tokens (longest match first). We do not alias product names (e.g. Power BI) or
single-token skills (e.g. SQL) to avoid collapsing distinct labels.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

from agents.common.types import JobRecord
from agents.eval.extraction_eval_core import (
    compute_metrics,
    f1_from_precision_recall,
    normalize_tool_label_for_eval,
)
from agents.skills_extraction.extractors.skills import extract_skills
from agents.skills_extraction.extractors.tools import extract_tools

GROUND_TRUTH_PATH = Path(__file__).parent / "extraction_ground_truth.json"

# Full phrase -> canonical token. Applied after lowercasing and padding; longest
# keys first so e.g. "natural language processing" wins before inner subphrases.
_ABBREV_PHRASE_TO_TOKEN: tuple[tuple[str, str], ...] = tuple(
    sorted(
        (
            ("natural language processing", "nlp"),
            ("machine learning", "ml"),
            ("artificial intelligence", "ai"),
            ("business intelligence", "bi"),
            ("continuous integration and continuous deployment", "cicd"),
            ("continuous integration", "ci"),
            ("continuous deployment", "cd"),
            ("large language model", "llm"),
        ),
        key=lambda x: len(x[0]),
        reverse=True,
    )
)


def _fuzzy_threshold() -> int:
    raw = os.getenv("EVAL_EXTRACTION_FUZZY_THRESHOLD", "85")
    try:
        return max(0, min(100, int(raw)))
    except ValueError:
        return 85


def _normalize_label(text: str) -> str:
    """Lowercase, collapse whitespace, normalize ``&`` and slashes, apply conservative abbreviations."""
    if not isinstance(text, str):
        return ""
    s = text.lower().strip()
    if not s:
        return ""
    s = s.replace("&", " and ")
    s = re.sub(r"[/+]+", " ", s)
    s = " ".join(s.split())
    s = f" {s} "
    for phrase, token in _ABBREV_PHRASE_TO_TOKEN:
        needle = f" {phrase} "
        if needle in s:
            s = s.replace(needle, f" {token} ")
    return " ".join(s.split())


def normalize_list(items: Any) -> set[str]:
    """Normalize each non-empty string label and return a deduped set."""
    out: set[str] = set()
    for i in items:
        if not isinstance(i, str):
            continue
        n = _normalize_label(i)
        if n:
            out.add(n)
    return out


def fuzzy_match_count(pred: set[str], true: set[str], threshold: int) -> int:
    """Greedy 1:1 maximum matching on pairs with token_set_ratio >= threshold (highest scores first)."""
    if not pred or not true:
        return 0
    t = float(threshold)
    pairs: list[tuple[float, str, str]] = []
    for p in pred:
        for g in true:
            score = float(fuzz.token_set_ratio(p, g))
            if score >= t:
                pairs.append((score, p, g))
    pairs.sort(key=lambda x: x[0], reverse=True)
    used_p: set[str] = set()
    used_g: set[str] = set()
    matches = 0
    for _score, p, g in pairs:
        if p in used_p or g in used_g:
            continue
        used_p.add(p)
        used_g.add(g)
        matches += 1
    return matches


def compute_fuzzy_metrics(pred: set[str], true: set[str], threshold: int) -> tuple[float, float, float]:
    m = fuzzy_match_count(pred, true, threshold)
    precision = 0.0 if len(pred) == 0 else m / len(pred)
    recall = 0.0 if len(true) == 0 else m / len(true)
    f1 = f1_from_precision_recall(precision, recall)
    return precision, recall, f1


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
    """Production-like Pass 1 + Pass 2; returns plain name lists, full skill records, and metadata."""
    tools = extract_tools(job_record)
    skills, metadata = extract_skills(job_record, pass1_tools=tools)
    return {
        "skills": [s.skill_name for s in skills],
        "tools": [t.tool_name for t in tools],
        "skill_records": skills,
        "metadata": metadata,
    }


def load_ground_truth(path: Path | str):
    path = Path(path) if isinstance(path, str) else path
    with open(path) as f:  # noqa: UP015
        return json.load(f)


def _log(msg: str) -> None:
    """Print eval output — CLI reporting tool, not library code."""
    print(msg)  # noqa: T201


def _skill_label(s: dict) -> str:
    """Ground truth skill: support both 'label' (legacy) and 'skill_name' (labeler export)."""
    return s.get("label") or s.get("skill_name") or ""


def run_eval(ground_truth_path: str | Path) -> None:
    data = load_ground_truth(ground_truth_path)
    fuzzy_threshold = _fuzzy_threshold()

    all_skill_records: list = []

    total_pred_skills = 0
    total_true_skills = 0
    total_matched_skills = 0

    total_pred_tools = 0
    total_true_tools = 0
    total_matched_tools = 0

    total_fuzzy_matched_skills = 0
    total_fuzzy_matched_tools = 0

    _log(f"Eval fuzzy threshold: token_set_ratio >= {fuzzy_threshold} (EVAL_EXTRACTION_FUZZY_THRESHOLD)")

    for job in data:
        job_record = ground_truth_row_to_job_record(job)
        pred = predict_skills_and_tools(job_record)
        all_skill_records.extend(pred.get("skill_records", []))

        gt_skills = normalize_list([_skill_label(s) for s in job["skills"] if _skill_label(s)])
        gt_tools = {
            normalize_tool_label_for_eval(t)
            for t in normalize_list(
                [t.get("tool_name") or "" for t in job["tools"] if t.get("tool_name")]
            )
        }

        pred_skills = normalize_list(pred.get("skills", []))
        pred_tools = {
            normalize_tool_label_for_eval(t) for t in normalize_list(pred.get("tools", []))
        }

        p_s, r_s, f_s = compute_metrics(pred_skills, gt_skills)
        p_t, r_t, f_t = compute_metrics(pred_tools, gt_tools)

        p_sf, r_sf, f_sf = compute_fuzzy_metrics(pred_skills, gt_skills, fuzzy_threshold)
        p_tf, r_tf, f_tf = compute_fuzzy_metrics(pred_tools, gt_tools, fuzzy_threshold)

        matched_skills = pred_skills & gt_skills
        matched_tools = pred_tools & gt_tools
        fuzzy_ms = fuzzy_match_count(pred_skills, gt_skills, fuzzy_threshold)
        fuzzy_mt = fuzzy_match_count(pred_tools, gt_tools, fuzzy_threshold)

        total_pred_skills += len(pred_skills)
        total_true_skills += len(gt_skills)
        total_matched_skills += len(matched_skills)
        total_fuzzy_matched_skills += fuzzy_ms

        total_pred_tools += len(pred_tools)
        total_true_tools += len(gt_tools)
        total_matched_tools += len(matched_tools)
        total_fuzzy_matched_tools += fuzzy_mt

        _log(f"\n--- {job['title']} ---")
        if pred.get("metadata", {}).get("extraction_failed"):
            _log("Skills pass: extraction_failed=true (see extractor metadata)")
        _log(f"GT Skills:   {gt_skills}")
        _log(f"Pred Skills: {pred_skills}")
        _log(f"Match (strict): {pred_skills & gt_skills}")
        _log(f"GT Tools:    {gt_tools}")
        _log(f"Pred Tools:  {pred_tools}")
        _log(f"Match (strict): {pred_tools & gt_tools}")
        _log(
            f"Skills strict P/R/F1: {p_s:.2f} / {r_s:.2f} / {f_s:.2f}  |  "
            f"fuzzy P/R/F1: {p_sf:.2f} / {r_sf:.2f} / {f_sf:.2f}"
        )
        _log(
            f"Tools  strict P/R/F1: {p_t:.2f} / {r_t:.2f} / {f_t:.2f}  |  "
            f"fuzzy P/R/F1: {p_tf:.2f} / {r_tf:.2f} / {f_tf:.2f}"
        )

    _log("\n=== FINAL METRICS (strict — normalized exact set overlap) ===")
    _log(f"Total GT Skills: {total_true_skills}")
    _log(f"Total Pred Skills: {total_pred_skills}")
    _log(f"Matched Skills: {total_matched_skills}")

    precision_skills = total_matched_skills / total_pred_skills if total_pred_skills > 0 else 0.0
    recall_skills = total_matched_skills / total_true_skills if total_true_skills > 0 else 0.0
    f1_skills = f1_from_precision_recall(precision_skills, recall_skills)

    _log(f"Skills Precision: {precision_skills:.2f}")
    _log(f"Skills Recall:    {recall_skills:.2f}")
    _log(f"Skills F1:        {f1_skills:.2f}")

    _log("\n--- TOOLS (strict) ---")
    _log(f"Total GT Tools: {total_true_tools}")
    _log(f"Total Pred Tools: {total_pred_tools}")
    _log(f"Matched Tools: {total_matched_tools}")

    precision_tools = total_matched_tools / total_pred_tools if total_pred_tools > 0 else 0.0
    recall_tools = total_matched_tools / total_true_tools if total_true_tools > 0 else 0.0
    f1_tools = f1_from_precision_recall(precision_tools, recall_tools)

    _log(f"Tools Precision: {precision_tools:.2f}")
    _log(f"Tools Recall:    {recall_tools:.2f}")
    _log(f"Tools F1:        {f1_tools:.2f}")

    _log(f"\n=== FINAL METRICS (fuzzy — token_set_ratio >= {fuzzy_threshold}, greedy 1:1) ===")
    _log(f"Total GT Skills: {total_true_skills}")
    _log(f"Total Pred Skills: {total_pred_skills}")
    _log(f"Fuzzy-matched Skills: {total_fuzzy_matched_skills}")

    fp_s = (
        total_fuzzy_matched_skills / total_pred_skills if total_pred_skills > 0 else 0.0
    )
    fr_s = (
        total_fuzzy_matched_skills / total_true_skills if total_true_skills > 0 else 0.0
    )
    ff_s = f1_from_precision_recall(fp_s, fr_s)
    _log(f"Skills Precision: {fp_s:.2f}")
    _log(f"Skills Recall:    {fr_s:.2f}")
    _log(f"Skills F1:        {ff_s:.2f}")

    _log("\n--- TOOLS (fuzzy) ---")
    _log(f"Total GT Tools: {total_true_tools}")
    _log(f"Total Pred Tools: {total_pred_tools}")
    _log(f"Fuzzy-matched Tools: {total_fuzzy_matched_tools}")

    fp_t = (
        total_fuzzy_matched_tools / total_pred_tools if total_pred_tools > 0 else 0.0
    )
    fr_t = (
        total_fuzzy_matched_tools / total_true_tools if total_true_tools > 0 else 0.0
    )
    ff_t = f1_from_precision_recall(fp_t, fr_t)
    _log(f"Tools Precision: {fp_t:.2f}")
    _log(f"Tools Recall:    {fr_t:.2f}")
    _log(f"Tools F1:        {ff_t:.2f}")

    # Taxonomy and GenAI Extension (skills only)
    _log("\n--- TAXONOMY (skills) ---")
    if all_skill_records:
        taxonomy_covered = sum(1 for s in all_skill_records if s.esco_uri)
        genai_count = sum(1 for s in all_skill_records if s.is_genai_extension)
        taxonomy_coverage = taxonomy_covered / len(all_skill_records)
        genai_extension_rate = genai_count / len(all_skill_records)
        _log(f"Total predicted skills: {len(all_skill_records)}")
        _log(f"Taxonomy coverage: {taxonomy_coverage:.2%} ({taxonomy_covered} with esco_uri)")
        _log(f"GenAI Extension detection rate: {genai_extension_rate:.2%} ({genai_count} with is_genai_extension)")
    else:
        _log("No predicted skills — taxonomy metrics N/A")


if __name__ == "__main__":
    run_eval(GROUND_TRUTH_PATH)
