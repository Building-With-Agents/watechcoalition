"""Shared extraction eval logic: metrics, stub extractor, pipeline mode, artifacts."""

from __future__ import annotations

import json
import re
import subprocess
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

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
}


def normalize_tool_label_for_eval(label: str) -> str:
    """Map alternate spellings to one key for micro tool P/R (GT vs predicted tool_name)."""
    s = label.lower().strip()
    return _TOOL_LABEL_EQUIVALENCE.get(s, s)


def compute_metrics(pred: set[str], true: set[str]) -> tuple[float, float]:
    precision = 0.0 if len(pred) == 0 else len(pred & true) / len(pred)
    recall = 0.0 if len(true) == 0 else len(pred & true) / len(true)
    return precision, recall


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

    return {"skills": skills, "tools": tools}


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
    from agents.skills_extraction.prompts.skills_extraction_v1 import (
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
    from agents.skills_extraction.prompts.skills_extraction_v1 import SKILLS_PROMPT_VERSION

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


def _gt_sets(job: dict[str, Any]) -> tuple[set[str], set[str]]:
    skills_raw = job.get("skills") or []
    tools_raw = job.get("tools") or []
    gt_skills = normalize_list([str(s["skill_name"]) for s in skills_raw if isinstance(s, dict)])
    gt_tools_raw = normalize_list([str(t["tool_name"]) for t in tools_raw if isinstance(t, dict)])
    gt_tools = {normalize_tool_label_for_eval(t) for t in gt_tools_raw}
    return gt_skills, gt_tools


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
    total_pred_skills = 0
    total_true_skills = 0
    total_matched_skills = 0
    total_pred_tools = 0
    total_true_tools = 0
    total_matched_tools = 0

    total_tokens = 0
    total_cost = 0.0
    total_latency = 0
    llm_applicable = mode == "pipeline"

    prompt_exemplar: PromptExemplar | None = None
    console_lines: list[str] = []

    for idx, job in enumerate(rows):
        text = job_text_from_row(job)
        gt_skills, gt_tools = _gt_sets(job)

        if mode == "stub":
            pred = extract_from_text_testing(text)
            pred_skills = normalize_list([str(x) for x in pred.get("skills", [])])
            pred_tools = {
                normalize_tool_label_for_eval(t)
                for t in normalize_list([str(x) for x in pred.get("tools", [])])
            }
            pj = PerJobSnapshot(
                job_key=_job_key(job, idx),
                title=str(job.get("title") or ""),
                gt_skills=sorted(gt_skills),
                gt_tools=sorted(gt_tools),
                pred_skills=sorted(pred_skills),
                pred_tools=sorted(pred_tools),
            )
        else:
            from agents.skills_extraction.extractors.skills import extract_skills
            from agents.skills_extraction.extractors.tools import extract_tools

            jr = ground_truth_row_to_job_record(job)
            tools_recs = extract_tools(jr)
            pass1_names = [t.tool_name for t in tools_recs]
            if idx == 0:
                sys_p, usr_p = render_prompt_for_job(jr, pass1_names)
                prompt_exemplar = PromptExemplar(
                    skills_prompt_version=get_skills_prompt_version(),
                    system_prompt=sys_p,
                    user_prompt=usr_p,
                )

            skills_recs, meta = extract_skills(jr, pass1_tools=tools_recs)
            pred_skills = normalize_list([s.skill_name for s in skills_recs])
            pred_tools_raw = normalize_list([t.tool_name for t in tools_recs])
            pred_tools = {normalize_tool_label_for_eval(t) for t in pred_tools_raw}

            tok = int(meta.get("tokens_used") or 0)
            cost = float(meta.get("cost_usd") or 0.0)
            lat = int(meta.get("latency_ms") or 0)
            total_tokens += tok
            total_cost += cost
            total_latency += lat

            pj = PerJobSnapshot(
                job_key=_job_key(job, idx),
                title=str(job.get("title") or ""),
                gt_skills=sorted(gt_skills),
                gt_tools=sorted(gt_tools),
                pred_skills=sorted(pred_skills),
                pred_tools=sorted(pred_tools),
                tokens_used=tok,
                cost_usd=round(cost, 6),
                latency_ms=lat,
                extraction_failed=bool(meta.get("extraction_failed")),
                llm_error_reason=(str(meta.get("error_reason")) if meta.get("error_reason") else None),
            )

        ms = sorted(pred_skills & gt_skills)
        missed_s = sorted(gt_skills - pred_skills)
        fp_s = sorted(pred_skills - gt_skills)
        mt = sorted(pred_tools & gt_tools)
        missed_t = sorted(gt_tools - pred_tools)
        fp_t = sorted(pred_tools - gt_tools)

        p_s, r_s = compute_metrics(set(pred_skills), set(gt_skills))
        p_t, r_t = compute_metrics(set(pred_tools), set(gt_tools))

        pj.matched_skills = ms
        pj.missed_skills = missed_s
        pj.false_positive_skills = fp_s
        pj.matched_tools = mt
        pj.missed_tools = missed_t
        pj.false_positive_tools = fp_t
        pj.precision_skills = p_s
        pj.recall_skills = r_s
        pj.precision_tools = p_t
        pj.recall_tools = r_t

        per_job.append(pj)

        total_pred_skills += len(pred_skills)
        total_true_skills += len(gt_skills)
        total_matched_skills += len(set(pred_skills) & set(gt_skills))
        total_pred_tools += len(pred_tools)
        total_true_tools += len(gt_tools)
        total_matched_tools += len(set(pred_tools) & set(gt_tools))

        console_lines.append(f"\n--- {job.get('title', '')} ---")
        console_lines.append(f"GT Skills:   {gt_skills}")
        console_lines.append(f"Pred Skills: {pred_skills}")
        console_lines.append(f"Match:       {pred_skills & gt_skills}")
        console_lines.append(f"GT Tools:    {gt_tools}")
        console_lines.append(f"Pred Tools:  {pred_tools}")
        console_lines.append(f"Match:       {pred_tools & gt_tools}")
        console_lines.append(f"Skills P/R: {p_s:.2f} / {r_s:.2f}")
        console_lines.append(f"Tools  P/R: {p_t:.2f} / {r_t:.2f}")

    precision_skills = (
        total_matched_skills / total_pred_skills if total_pred_skills > 0 else 0.0
    )
    recall_skills = total_matched_skills / total_true_skills if total_true_skills > 0 else 0.0
    precision_tools = (
        total_matched_tools / total_pred_tools if total_pred_tools > 0 else 0.0
    )
    recall_tools = total_matched_tools / total_true_tools if total_true_tools > 0 else 0.0

    console_lines.append("\n=== FINAL METRICS ===")
    console_lines.append(f"Total GT Skills: {total_true_skills}")
    console_lines.append(f"Total Pred Skills: {total_pred_skills}")
    console_lines.append(f"Matched Skills: {total_matched_skills}")
    console_lines.append(f"Skills Precision: {precision_skills:.2f}")
    console_lines.append(f"Skills Recall:    {recall_skills:.2f}")
    console_lines.append("\n--- TOOLS ---")
    console_lines.append(f"Total GT Tools: {total_true_tools}")
    console_lines.append(f"Total Pred Tools: {total_pred_tools}")
    console_lines.append(f"Matched Tools: {total_matched_tools}")
    console_lines.append(f"Tools Precision: {precision_tools:.2f}")
    console_lines.append(f"Tools Recall:    {recall_tools:.2f}")

    aggregates = AggregateMetrics(
        total_gt_skills=total_true_skills,
        total_pred_skills=total_pred_skills,
        matched_skills=total_matched_skills,
        precision_skills=precision_skills,
        recall_skills=recall_skills,
        total_gt_tools=total_true_tools,
        total_pred_tools=total_pred_tools,
        matched_tools=total_matched_tools,
        precision_tools=precision_tools,
        recall_tools=recall_tools,
        total_tokens_used=total_tokens if llm_applicable else None,
        total_cost_usd=round(total_cost, 6) if llm_applicable else None,
        total_latency_ms=total_latency if llm_applicable else None,
        llm_applicable=llm_applicable,
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
        "## Aggregate metrics",
        "",
        f"- **Skills** — precision: {ag.precision_skills:.4f}, recall: {ag.recall_skills:.4f}",
        f"- **Skills counts** — GT: {ag.total_gt_skills}, pred: {ag.total_pred_skills}, matched: {ag.matched_skills}",
        f"- **Tools** — precision: {ag.precision_tools:.4f}, recall: {ag.recall_tools:.4f}",
        f"- **Tools counts** — GT: {ag.total_gt_tools}, pred: {ag.total_pred_tools}, matched: {ag.matched_tools}",
    ]
    if ag.llm_applicable:
        lines.extend(
            [
                f"- **Total tokens (skills LLM):** {ag.total_tokens_used}",
                f"- **Total cost USD (estimate):** {ag.total_cost_usd}",
                f"- **Total latency ms (sum per job):** {ag.total_latency_ms}",
            ]
        )
    else:
        lines.append("- **LLM tokens / cost:** N/A (stub mode — no skills LLM calls)")

    lines.extend(["", "## Skills prompt (exemplar)", ""])

    pe = snapshot.prompt_exemplar
    if pe and mode == "stub":
        lines.append(
            "_Stub mode: prompt below is a template for the first ground-truth job with no Pass-1 tools._"
        )
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
