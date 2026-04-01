"""Shared extraction eval logic: metrics, stub extractor, pipeline mode, artifacts."""

from __future__ import annotations

import json
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from agents.common.types import ContextSignal
from agents.common.types.job_record import JobRecord
from agents.eval.snapshot_schema import (
    SNAPSHOT_SCHEMA_VERSION,
    AggregateMetrics,
    ExtractionEvalSnapshot,
    PerJobSnapshot,
    PromptExemplar,
)

MT_ZONE = ZoneInfo("America/Denver")

TEXT_FIELDS = ("title", "description", "requirements", "responsibilities")


def load_ground_truth(path: Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("ground truth must be a JSON array")
    return data


def normalize_list(items: list[str]) -> set[str]:
    return {i.lower().strip() for i in items if i and str(i).strip()}


# Collapse equivalent product labels so eval recall/precision match human intent (GT vs Pass 1 naming).
_TOOL_LABEL_EQUIVALENCE: dict[str, str] = {
    "microsoft excel": "excel",
    "microsoft powerpoint": "powerpoint",
    "microsoft outlook": "outlook",
    "microsoft project": "microsoft projects",
    "splunk (es)": "splunk",
    "splunk es": "splunk",
    "fortinet firewall": "fortinet",
    "fortinet firewalls": "fortinet",
}


def normalize_tool_label_for_eval(label: str) -> str:
    """Map alternate spellings to one key for micro tool P/R (GT vs predicted tool_name)."""
    s = label.lower().strip()
    return _TOOL_LABEL_EQUIVALENCE.get(s, s)


def f1_from_precision_recall(precision: float, recall: float) -> float:
    if precision + recall <= 0.0:
        return 0.0
    return (2.0 * precision * recall) / (precision + recall)


def compute_metrics(pred: set[str], true: set[str]) -> tuple[float, float, float]:
    precision = 0.0 if len(pred) == 0 else len(pred & true) / len(pred)
    recall = 0.0 if len(true) == 0 else len(pred & true) / len(true)
    f1 = f1_from_precision_recall(precision, recall)
    return precision, recall, f1


def extract_from_text_testing(text: str) -> dict[str, list[str]]:
    text = text.lower()

    skills: list[str] = []
    tools: list[str] = []

    if "python" in text:
        skills.append("Python")
        tools.append("Python")

    if "sql" in text:
        skills.append("SQL")
        tools.append("SQL")

    if "machine learning" in text:
        skills.append("Machine Learning")

    if "aws" in text:
        tools.append("AWS")

    if "docker" in text:
        tools.append("Docker")

    if "sales" in text:
        skills.append("Sales")

    if "marketing" in text:
        skills.append("Marketing")

    if "communication" in text:
        skills.append("Communication")

    if "product" in text:
        skills.append("Product Management")

    if "analysis" in text:
        skills.append("Data Analysis")

    return {
        "skills": skills,
        "tools": tools,
        "tasks": [],
        "responsibilities": [],
        "context": [],
    }


def job_text_from_row(job: dict[str, Any]) -> str:
    return " ".join(str(job.get(f, "") or "") for f in TEXT_FIELDS)


def ground_truth_row_to_job_record(row: dict[str, Any]) -> JobRecord:
    company = (row.get("company") or "").strip() or "Unknown"
    title = (row.get("title") or "").strip() or "Untitled"
    return JobRecord(
        source=str(row.get("source") or "ground_truth"),
        external_id=str(row.get("external_id") or row.get("ground_truth_id") or "unknown"),
        title=title,
        company=company,
        description=row.get("description"),
        requirements=row.get("requirements"),
        responsibilities=row.get("responsibilities"),
        city=row.get("city"),
        state_province=row.get("state_province") or row.get("state"),
        country=row.get("country"),
    )


def render_prompt_for_job(
    job_record: JobRecord,
    pass1_tool_names: list[str],
) -> tuple[str, str]:
    from agents.skills_extraction.prompts import (
        SKILLS_PROMPT_VERSION,
        SKILLS_SYSTEM_PROMPT,
        SKILLS_USER_TEMPLATE,
    )

    tools_str = ", ".join(pass1_tool_names) if pass1_tool_names else "(none)"
    user = SKILLS_USER_TEMPLATE.format(
        already_extracted_tools=tools_str,
        title=job_record.title or "(none)",
        description=job_record.description or "(none)",
        requirements=job_record.requirements or "(none)",
        responsibilities=job_record.responsibilities or "(none)",
    )
    _ = SKILLS_PROMPT_VERSION  # re-export for callers
    return SKILLS_SYSTEM_PROMPT, user


def get_skills_prompt_version() -> str:
    from agents.skills_extraction.prompts import SKILLS_PROMPT_VERSION

    return SKILLS_PROMPT_VERSION


def now_mountain_iso() -> str:
    return datetime.now(MT_ZONE).isoformat(timespec="seconds")


def slugify_label(label: str) -> str:
    s = (label or "run").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "run"


def try_git_short_hash() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _job_key(row: dict[str, Any], index: int) -> str:
    return str(row.get("ground_truth_id") or row.get("external_id") or f"idx-{index}")


class RunEvalResult:
    """Outcome of run_eval_dataset + artifact paths."""

    def __init__(
        self,
        snapshot: ExtractionEvalSnapshot,
        console_lines: list[str],
        backlog_path: Path | None = None,
        snapshot_path: Path | None = None,
    ) -> None:
        self.snapshot = snapshot
        self.console_lines = console_lines
        self.backlog_path = backlog_path
        self.snapshot_path = snapshot_path


@dataclass(frozen=True, slots=True)
class EvalDimensionSpec:
    """One extraction dimension: stable id, GT reader, whether ESCO-style taxonomy applies."""

    key: str
    taxonomy_coverage: bool
    ground_truth_labels: Callable[[dict[str, Any]], set[str]]


def ground_truth_skill_labels(job: dict[str, Any]) -> set[str]:
    skills_raw = job.get("skills") or []
    return normalize_list([str(s["skill_name"]) for s in skills_raw if isinstance(s, dict) and s.get("skill_name")])


def ground_truth_tool_labels(job: dict[str, Any]) -> set[str]:
    tools_raw = job.get("tools") or []
    raw = normalize_list([str(t["tool_name"]) for t in tools_raw if isinstance(t, dict) and t.get("tool_name")])
    return {normalize_tool_label_for_eval(t) for t in raw}


def ground_truth_task_labels(job: dict[str, Any]) -> set[str]:
    tasks_raw = job.get("tasks") or []
    return normalize_list(
        [str(x["task_description"]) for x in tasks_raw if isinstance(x, dict) and x.get("task_description")]
    )


def ground_truth_responsibility_labels(job: dict[str, Any]) -> set[str]:
    rows = job.get("labeled_responsibilities") or []
    return normalize_list(
        [
            str(x["responsibility_description"])
            for x in rows
            if isinstance(x, dict) and x.get("responsibility_description")
        ]
    )


# Eval-only: align GT labeler enums with extractor ``ContextSignalType`` where needed.
# Types not listed (e.g. growth_stage) pass through lowercased for stable GT↔pred comparison later.
_CONTEXT_SIGNAL_TYPE_EVAL_ALIASES: dict[str, str] = {
    "ai_usage": "ai_adoption_signal",
}


def canonicalize_context_signal_type_for_eval(signal_type: object) -> str:
    """Normalized type token for context labels (aliases + lowercase)."""
    raw = str(signal_type or "").strip().lower()
    raw = "_".join(part for part in raw.replace("-", "_").split() if part)
    return _CONTEXT_SIGNAL_TYPE_EVAL_ALIASES.get(raw, raw)


def canonical_context_label(signal_type: object, value: object) -> str:
    """Single strict-eval token: canonical_signal_type + normalized value."""
    st = canonicalize_context_signal_type_for_eval(signal_type)
    v = str(value or "").lower().strip()
    v = " ".join(v.split())
    return f"{st}|{v}"


def ground_truth_context_labels(job: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for x in job.get("context") or []:
        if not isinstance(x, dict):
            continue
        val = x.get("value")
        if val is None or (isinstance(val, str) and not val.strip()):
            continue
        out.add(canonical_context_label(x.get("signal_type"), val))
    return out


def prediction_context_labels_from_signals(signals: list[ContextSignal]) -> set[str]:
    """Strict-eval labels from ``extract_context`` output (aligned with ``ground_truth_context_labels``)."""
    out: set[str] = set()
    for s in signals:
        val = s.value
        if isinstance(val, str) and not val.strip():
            continue
        out.add(canonical_context_label(s.signal_type, val))
    return out


def _sum_pipeline_meta_tokens_cost_latency(*metas: dict[str, Any]) -> tuple[int, float, int]:
    return (
        sum(int(m.get("tokens_used") or 0) for m in metas),
        sum(float(m.get("cost_usd") or 0.0) for m in metas),
        sum(int(m.get("latency_ms") or 0) for m in metas),
    )


def _first_error_reason(*metas: dict[str, Any]) -> str | None:
    for m in metas:
        er = m.get("error_reason")
        if er:
            return str(er)
    return None


EVAL_DIMENSIONS: tuple[EvalDimensionSpec, ...] = (
    EvalDimensionSpec("skills", True, ground_truth_skill_labels),
    EvalDimensionSpec("tools", False, ground_truth_tool_labels),
    EvalDimensionSpec("tasks", False, ground_truth_task_labels),
    EvalDimensionSpec("responsibilities", False, ground_truth_responsibility_labels),
    EvalDimensionSpec("context", False, ground_truth_context_labels),
)


def _dimension_title(key: str) -> str:
    return {
        "skills": "Skills",
        "tools": "Tools",
        "tasks": "Tasks",
        "responsibilities": "Responsibilities",
        "context": "Context",
    }.get(key, key.replace("_", " ").title())


def _fold_skill_record_taxonomy_counts(skill_recs: list[Any]) -> tuple[int, int, int]:
    """Returns (total_records, count_with_esco_uri, count_genai_extension)."""
    n = len(skill_recs)
    esco = sum(1 for s in skill_recs if getattr(s, "esco_uri", None))
    genai = sum(1 for s in skill_recs if getattr(s, "is_genai_extension", False))
    return n, esco, genai


def _per_job_fields_for_dimension(
    key: str, gt: set[str], pred: set[str], precision: float, recall: float, f1: float
) -> dict[str, Any]:
    matched = sorted(gt & pred)
    return {
        f"gt_{key}": sorted(gt),
        f"pred_{key}": sorted(pred),
        f"matched_{key}": matched,
        f"missed_{key}": sorted(gt - pred),
        f"false_positive_{key}": sorted(pred - gt),
        f"precision_{key}": precision,
        f"recall_{key}": recall,
        f"f1_{key}": f1,
    }


def run_eval_dataset(
    data: list[dict[str, Any]],
    *,
    mode: str,
    limit: int | None = None,
    ground_truth_path: str = "",
    run_label: str = "",
    write_artifacts: bool = False,
    output_runs_dir: Path | None = None,
    output_backlog_dir: Path | None = None,
) -> RunEvalResult:
    if mode not in ("stub", "pipeline"):
        raise ValueError("mode must be stub or pipeline")

    rows = data[:limit] if limit is not None else list(data)
    t0 = time.perf_counter()

    per_job: list[PerJobSnapshot] = []
    totals: dict[str, dict[str, int]] = {d.key: {"gt": 0, "pred": 0, "matched": 0} for d in EVAL_DIMENSIONS}

    total_tokens = 0
    total_cost = 0.0
    total_latency = 0
    llm_applicable = mode == "pipeline"

    prompt_exemplar: PromptExemplar | None = None
    console_lines: list[str] = []
    skill_pred_records_total = 0
    skill_pred_with_esco = 0
    skill_pred_genai = 0

    for idx, job in enumerate(rows):
        text = job_text_from_row(job)
        prediction_sets: dict[str, set[str]] = {d.key: set() for d in EVAL_DIMENSIONS}

        if mode == "stub":
            pred = extract_from_text_testing(text)
            prediction_sets["skills"] = normalize_list([str(x) for x in pred.get("skills", [])])
            prediction_sets["tools"] = {
                normalize_tool_label_for_eval(t) for t in normalize_list([str(x) for x in pred.get("tools", [])])
            }
            prediction_sets["tasks"] = normalize_list([str(x) for x in pred.get("tasks", [])])
            prediction_sets["responsibilities"] = normalize_list([str(x) for x in pred.get("responsibilities", [])])
            prediction_sets["context"] = normalize_list([str(x) for x in pred.get("context", [])])
            pj_base: dict[str, Any] = {
                "job_key": _job_key(job, idx),
                "title": str(job.get("title") or ""),
            }
        else:
            from agents.skills_extraction.extractors.context import extract_context
            from agents.skills_extraction.extractors.responsibilities import extract_responsibilities
            from agents.skills_extraction.extractors.skills import extract_skills
            from agents.skills_extraction.extractors.tasks import extract_tasks
            from agents.skills_extraction.extractors.tools import extract_tools

            jr = ground_truth_row_to_job_record(job)
            context_signals, ctx_meta = extract_context(jr)
            tools_recs = extract_tools(jr)
            pass1_names = [t.tool_name for t in tools_recs]
            if idx == 0:
                sys_p, usr_p = render_prompt_for_job(jr, pass1_names)
                prompt_exemplar = PromptExemplar(
                    skills_prompt_version=get_skills_prompt_version(),
                    system_prompt=sys_p,
                    user_prompt=usr_p,
                )

            skills_recs, skills_meta = extract_skills(jr, pass1_tools=tools_recs)
            _n_sk, _n_es, _n_gn = _fold_skill_record_taxonomy_counts(skills_recs)
            skill_pred_records_total += _n_sk
            skill_pred_with_esco += _n_es
            skill_pred_genai += _n_gn

            task_recs, tasks_meta = extract_tasks(jr, pass1_context=context_signals)
            resp_recs, resp_meta = extract_responsibilities(jr, pass1_context=context_signals)

            prediction_sets["context"] = prediction_context_labels_from_signals(context_signals)
            pred_tools_raw = normalize_list([t.tool_name for t in tools_recs])
            prediction_sets["tools"] = {normalize_tool_label_for_eval(t) for t in pred_tools_raw}
            prediction_sets["skills"] = normalize_list([s.skill_name for s in skills_recs])
            prediction_sets["tasks"] = normalize_list(
                [str(t.task_description) for t in task_recs if getattr(t, "task_description", None)]
            )
            prediction_sets["responsibilities"] = normalize_list(
                [str(r.responsibility_description) for r in resp_recs if getattr(r, "responsibility_description", None)]
            )

            tok, cost, lat = _sum_pipeline_meta_tokens_cost_latency(ctx_meta, skills_meta, tasks_meta, resp_meta)
            total_tokens += tok
            total_cost += cost
            total_latency += lat

            extraction_failed = bool(
                ctx_meta.get("extraction_failed")
                or skills_meta.get("extraction_failed")
                or tasks_meta.get("extraction_failed")
                or resp_meta.get("extraction_failed")
            )
            err_reason = _first_error_reason(skills_meta, tasks_meta, resp_meta, ctx_meta)

            pj_base = {
                "job_key": _job_key(job, idx),
                "title": str(job.get("title") or ""),
                "tokens_used": tok,
                "cost_usd": round(cost, 6),
                "latency_ms": lat,
                "extraction_failed": extraction_failed,
                "llm_error_reason": err_reason,
            }

        for spec in EVAL_DIMENSIONS:
            gt = spec.ground_truth_labels(job)
            pred = prediction_sets[spec.key]
            p, r, f1 = compute_metrics(pred, gt)
            pj_base.update(_per_job_fields_for_dimension(spec.key, gt, pred, p, r, f1))
            totals[spec.key]["gt"] += len(gt)
            totals[spec.key]["pred"] += len(pred)
            totals[spec.key]["matched"] += len(gt & pred)

        per_job.append(PerJobSnapshot(**pj_base))

        console_lines.append(f"\n--- {job.get('title', '')} ---")
        if mode == "pipeline" and pj_base.get("extraction_failed"):
            console_lines.append("Pipeline: extraction_failed=true (see llm_error_reason / extractor metadata)")
        for spec in EVAL_DIMENSIONS:
            gt = spec.ground_truth_labels(job)
            pred = prediction_sets[spec.key]
            p, r, _f1 = compute_metrics(pred, gt)
            title = _dimension_title(spec.key)
            tax_note = " (taxonomy: ESCO / GenAI on predicted skill records only)" if spec.taxonomy_coverage else ""
            console_lines.append(f"[{title}]{tax_note}")
            console_lines.append(f"  GT:   {gt}")
            console_lines.append(f"  Pred: {pred}")
            console_lines.append(f"  Match: {pred & gt}")
            console_lines.append(f"  P/R/F1: {p:.2f} / {r:.2f} / {_f1:.2f}")

    def _micro_agg(key: str) -> tuple[int, int, int, float, float, float]:
        m = totals[key]
        tg, tp, tm = m["gt"], m["pred"], m["matched"]
        prec = tm / tp if tp > 0 else 0.0
        rec = tm / tg if tg > 0 else 0.0
        f1 = f1_from_precision_recall(prec, rec)
        return tg, tp, tm, prec, rec, f1

    ts = _micro_agg("skills")
    tt = _micro_agg("tools")
    ttask = _micro_agg("tasks")
    tr = _micro_agg("responsibilities")
    tc = _micro_agg("context")

    console_lines.append("\n=== FINAL METRICS (micro, all dimensions) ===")
    _hdr = f"{'Dimension':<18} {'P':>7} {'R':>7} {'F1':>7}  {'GT':>5} {'Pred':>5} {'Mtch':>5}"
    console_lines.append(_hdr)
    console_lines.append("-" * len(_hdr))
    for spec in EVAL_DIMENSIONS:
        tg, tp, tm, prec, rec, f1 = _micro_agg(spec.key)
        name = _dimension_title(spec.key)
        console_lines.append(f"{name:<18} {prec:>7.2f} {rec:>7.2f} {f1:>7.2f}  {tg:>5} {tp:>5} {tm:>5}")
    console_lines.append("")
    for spec in EVAL_DIMENSIONS:
        tg, tp, tm, prec, rec, f1 = _micro_agg(spec.key)
        title = _dimension_title(spec.key)
        console_lines.append(f"--- {title} (detail) ---")
        console_lines.append(f"Total GT: {tg}  |  Total Pred: {tp}  |  Matched: {tm}")
        console_lines.append(f"Precision: {prec:.4f}  |  Recall: {rec:.4f}  |  F1: {f1:.4f}")

    skills_pred_count: int | None = None
    skills_esco_cov: float | None = None
    skills_genai_rate: float | None = None
    if llm_applicable:
        skills_pred_count = skill_pred_records_total
        if skill_pred_records_total > 0:
            skills_esco_cov = skill_pred_with_esco / skill_pred_records_total
            skills_genai_rate = skill_pred_genai / skill_pred_records_total
        console_lines.append("\n=== SKILLS TAXONOMY (predicted SkillRecords, pipeline only) ===")
        if skill_pred_records_total == 0:
            console_lines.append("No predicted skill records — ESCO / GenAI rates N/A.")
        else:
            console_lines.append(
                f"Predicted skill records: {skill_pred_records_total}  |  "
                f"ESCO-linked: {skill_pred_with_esco} "
                f"({100.0 * skills_esco_cov:.2f}%)  |  "
                f"GenAI extension: {skill_pred_genai} "
                f"({100.0 * skills_genai_rate:.2f}%)"
            )
    else:
        console_lines.append("\n=== SKILLS TAXONOMY ===")
        console_lines.append("N/A (stub mode — no SkillRecord objects).")

    aggregates = AggregateMetrics(
        total_gt_skills=ts[0],
        total_pred_skills=ts[1],
        matched_skills=ts[2],
        precision_skills=ts[3],
        recall_skills=ts[4],
        f1_skills=ts[5],
        total_gt_tools=tt[0],
        total_pred_tools=tt[1],
        matched_tools=tt[2],
        precision_tools=tt[3],
        recall_tools=tt[4],
        f1_tools=tt[5],
        total_gt_tasks=ttask[0],
        total_pred_tasks=ttask[1],
        matched_tasks=ttask[2],
        precision_tasks=ttask[3],
        recall_tasks=ttask[4],
        f1_tasks=ttask[5],
        total_gt_responsibilities=tr[0],
        total_pred_responsibilities=tr[1],
        matched_responsibilities=tr[2],
        precision_responsibilities=tr[3],
        recall_responsibilities=tr[4],
        f1_responsibilities=tr[5],
        total_gt_context=tc[0],
        total_pred_context=tc[1],
        matched_context=tc[2],
        precision_context=tc[3],
        recall_context=tc[4],
        f1_context=tc[5],
        total_tokens_used=total_tokens if llm_applicable else None,
        total_cost_usd=round(total_cost, 6) if llm_applicable else None,
        total_latency_ms=total_latency if llm_applicable else None,
        llm_applicable=llm_applicable,
        skills_pred_record_count=skills_pred_count,
        skills_esco_coverage=skills_esco_cov,
        skills_genai_extension_rate=skills_genai_rate,
    )

    if mode == "stub" and prompt_exemplar is None and rows:
        jr0 = ground_truth_row_to_job_record(rows[0])
        sys_p, usr_p = render_prompt_for_job(jr0, [])
        prompt_exemplar = PromptExemplar(
            skills_prompt_version=get_skills_prompt_version(),
            system_prompt=sys_p,
            user_prompt=usr_p,
        )

    runtime_s = time.perf_counter() - t0

    snapshot = ExtractionEvalSnapshot(
        schema_version=SNAPSHOT_SCHEMA_VERSION,
        mt_timestamp_iso=now_mountain_iso(),
        run_label=run_label,
        git_short_hash=try_git_short_hash(),
        ground_truth_path=ground_truth_path,
        record_count=len(rows),
        extractor_mode="stub" if mode == "stub" else "llm_skills_pattern_tools",
        aggregates=aggregates,
        per_job=per_job,
        prompt_exemplar=prompt_exemplar,
        runtime_seconds=round(runtime_s, 3),
    )

    backlog_path: Path | None = None
    snapshot_path: Path | None = None

    if write_artifacts and output_runs_dir and output_backlog_dir:
        output_runs_dir.mkdir(parents=True, exist_ok=True)
        output_backlog_dir.mkdir(parents=True, exist_ok=True)

        mt = datetime.now(MT_ZONE)
        ts_slug = mt.strftime("%Y%m%dT%H%M%S")
        # %z is +HHMM / -HHMM (no colons — safe for Windows filenames)
        tz_part = mt.strftime("%z") or ""
        label_slug = slugify_label(run_label)
        base = f"{ts_slug}{tz_part}_{label_slug}"

        snapshot_path = output_runs_dir / f"{base}.json"
        backlog_path = output_backlog_dir / f"{base}.md"

        snapshot_path.write_text(
            json.dumps(snapshot.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        backlog_path.write_text(
            format_prompt_backlog_markdown(snapshot, mode),
            encoding="utf-8",
        )

    return RunEvalResult(
        snapshot=snapshot,
        console_lines=console_lines,
        backlog_path=backlog_path,
        snapshot_path=snapshot_path,
    )


def format_prompt_backlog_markdown(snapshot: ExtractionEvalSnapshot, mode: str) -> str:
    ag = snapshot.aggregates
    lines = [
        f"# Extraction eval run — {snapshot.mt_timestamp_iso} (America/Denver)",
        "",
        "## Metadata",
        "",
        f"- **Run label:** {snapshot.run_label or '(none)'}",
        f"- **Git (short):** {snapshot.git_short_hash or '(unavailable)'}",
        f"- **Ground truth:** `{snapshot.ground_truth_path}`",
        f"- **Records evaluated:** {snapshot.record_count}",
        f"- **Extractor mode:** `{snapshot.extractor_mode}`",
        f"- **Snapshot schema:** `{snapshot.schema_version}`",
        f"- **Wall runtime (s):** {snapshot.runtime_seconds}",
        "",
        "## Aggregate metrics (micro)",
        "",
        "| Dimension | Precision | Recall | F1 | GT | Pred | Matched |",
        "|-----------|-----------|--------|----|----|------|---------|",
        f"| Skills | {ag.precision_skills:.4f} | {ag.recall_skills:.4f} | {ag.f1_skills:.4f} | {ag.total_gt_skills} | {ag.total_pred_skills} | {ag.matched_skills} |",
        f"| Tools | {ag.precision_tools:.4f} | {ag.recall_tools:.4f} | {ag.f1_tools:.4f} | {ag.total_gt_tools} | {ag.total_pred_tools} | {ag.matched_tools} |",
        f"| Tasks | {ag.precision_tasks:.4f} | {ag.recall_tasks:.4f} | {ag.f1_tasks:.4f} | {ag.total_gt_tasks} | {ag.total_pred_tasks} | {ag.matched_tasks} |",
        f"| Responsibilities | {ag.precision_responsibilities:.4f} | {ag.recall_responsibilities:.4f} | {ag.f1_responsibilities:.4f} | {ag.total_gt_responsibilities} | {ag.total_pred_responsibilities} | {ag.matched_responsibilities} |",
        f"| Context | {ag.precision_context:.4f} | {ag.recall_context:.4f} | {ag.f1_context:.4f} | {ag.total_gt_context} | {ag.total_pred_context} | {ag.matched_context} |",
        "",
        "### Skills taxonomy (predicted SkillRecords, pipeline only)",
        "",
    ]
    if ag.skills_pred_record_count is not None and (ag.skills_pred_record_count or 0) > 0:
        esco_pct = 100.0 * (ag.skills_esco_coverage or 0.0)
        genai_pct = 100.0 * (ag.skills_genai_extension_rate or 0.0)
        lines.extend(
            [
                f"- **Predicted skill records:** {ag.skills_pred_record_count}",
                f"- **ESCO-linked (predicted skills with esco_uri):** {esco_pct:.2f}%",
                f"- **GenAI extension layer:** {genai_pct:.2f}%",
                "",
            ]
        )
    elif ag.llm_applicable:
        lines.extend(
            [
                "- **Predicted skill records:** 0 — ESCO / GenAI rates N/A.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "- **Stub mode:** taxonomy metrics N/A (no SkillRecord objects).",
                "",
            ]
        )
    lines.extend(["## Pipeline cost / latency", ""])
    if ag.llm_applicable:
        lines.extend(
            [
                f"- **Total tokens (pipeline sum, context+skills+tasks+responsibilities):** {ag.total_tokens_used}",
                f"- **Total cost USD (estimate):** {ag.total_cost_usd}",
                f"- **Total latency ms (sum per job):** {ag.total_latency_ms}",
            ]
        )
    else:
        lines.append("- **LLM tokens / cost:** N/A (stub mode — no pipeline extractors)")

    lines.extend(["", "## Skills prompt (exemplar)", ""])

    pe = snapshot.prompt_exemplar
    if pe and mode == "stub":
        lines.append("_Stub mode: prompt below is a template for the first ground-truth job with no Pass-1 tools._")
        lines.append("")

    if pe:
        lines.extend(
            [
                f"- **Prompt version:** `{pe.skills_prompt_version}`",
                "",
                "### System",
                "",
                "```text",
                pe.system_prompt,
                "```",
                "",
                "### User (exemplar)",
                "",
                "```text",
                pe.user_prompt,
                "```",
                "",
                f"_{pe.note}_",
            ]
        )
    else:
        lines.append("_No prompt exemplar captured._")

    lines.extend(
        [
            "",
            "---",
            "",
            "_Copy sections into `agents/eval/prompt_iteration_log.md` manually as needed._",
            "",
        ]
    )
    return "\n".join(lines)


def print_console(lines: list[str], log: Callable[[str], None] = print) -> None:
    for line in lines:
        log(line)


def run_eval_legacy_console(
    ground_truth_path: str | Path,
    log: Callable[[str], None] = print,
) -> RunEvalResult:
    path = Path(ground_truth_path)
    data = load_ground_truth(path)
    result = run_eval_dataset(
        data,
        mode="stub",
        limit=None,
        ground_truth_path=str(path.resolve()),
        run_label="legacy-cli",
        write_artifacts=False,
    )
    print_console(result.console_lines, log)
    return result
