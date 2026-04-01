"""Compare ground truth vs one or two extraction eval snapshots (run now or load JSON).

Usage (repo root):
    streamlit run agents/eval/streamlit_eval_app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Repo root must be on sys.path so `import agents` works when Streamlit runs this file.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd
import streamlit as st

from agents.eval.extraction_eval_core import load_ground_truth, run_eval_dataset
from agents.eval.snapshot_schema import SNAPSHOT_SCHEMA_VERSION, ExtractionEvalSnapshot, load_snapshot

_EVAL_DIR = Path(__file__).resolve().parent
_DEFAULT_GT = _EVAL_DIR / "extraction_ground_truth.json"
_DEFAULT_RUNS = _EVAL_DIR / "runs"
_DEFAULT_BACKLOG = _EVAL_DIR / "prompt_backlog"

# 1.1: five dimensions on aggregates/per_job; 1.2: + skills taxonomy summary fields.
_SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS = frozenset({SNAPSHOT_SCHEMA_VERSION, "1.1"})


def _list_run_snapshots() -> list[Path]:
    if not _DEFAULT_RUNS.is_dir():
        return []
    return sorted(_DEFAULT_RUNS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def _run_snapshot(
    gt_path: Path,
    mode: str,
    label: str,
    limit: int | None,
    write_artifacts: bool,
) -> ExtractionEvalSnapshot:
    data = load_ground_truth(gt_path)
    result = run_eval_dataset(
        data,
        mode=mode,
        limit=limit,
        ground_truth_path=str(gt_path.resolve()),
        run_label=label,
        write_artifacts=write_artifacts,
        output_runs_dir=_DEFAULT_RUNS if write_artifacts else None,
        output_backlog_dir=_DEFAULT_BACKLOG if write_artifacts else None,
    )
    if write_artifacts and result.snapshot_path:
        st.success(f"Wrote `{result.snapshot_path.name}` and backlog entry.")
    return result.snapshot


def _load_snapshot_ui(key: str) -> ExtractionEvalSnapshot | None:
    st.caption("Load a JSON file from `agents/eval/runs/` or upload.")
    snap_paths = _list_run_snapshots()
    options = ["(Upload file…)"] + [p.name for p in snap_paths]
    choice = st.selectbox(f"Saved snapshot ({key})", options, key=f"sel_{key}")
    if choice and choice != "(Upload file…)":
        path = _DEFAULT_RUNS / choice
        return load_snapshot(path)
    up = st.file_uploader(f"Upload snapshot JSON ({key})", type=["json"], key=f"up_{key}")
    if up is not None:
        data = json.loads(up.read().decode("utf-8"))
        return ExtractionEvalSnapshot.model_validate(data)
    return None


def _run_panel(key: str, session_key: str) -> None:
    mode = st.selectbox("Extractor mode", ["stub", "pipeline"], key=f"m_{key}")
    label = st.text_input("Run label (filename slug)", value=key, key=f"l_{key}")
    limit = st.number_input("Job limit (0 = all)", min_value=0, value=0, key=f"n_{key}")
    lim = None if limit == 0 else int(limit)
    write = st.checkbox("Write snapshot + prompt_backlog to disk", value=False, key=f"w_{key}")
    if st.button(f"Run eval ({key})", key=f"b_{key}"):
        gt = Path(st.session_state.get("gt_path_str", str(_DEFAULT_GT)))
        if not gt.exists():
            st.error(f"Ground truth not found: {gt}")
            return
        with st.spinner("Running…"):
            try:
                st.session_state[session_key] = _run_snapshot(gt, mode, label, lim, write)
            except Exception as e:
                st.exception(e)


def _taxonomy_display(ag) -> tuple[str, str, str]:
    """Human-readable taxonomy columns for aggregate row."""
    if not ag.llm_applicable:
        return "N/A", "N/A", "N/A"
    n = ag.skills_pred_record_count
    if n is None or n == 0:
        return "0", "N/A", "N/A"
    esco = ag.skills_esco_coverage
    genai = ag.skills_genai_extension_rate
    esco_s = f"{100.0 * esco:.2f}%" if esco is not None else "N/A"
    genai_s = f"{100.0 * genai:.2f}%" if genai is not None else "N/A"
    return str(n), esco_s, genai_s


def _metrics_df(snap: ExtractionEvalSnapshot | None, name: str) -> pd.DataFrame:
    if snap is None:
        return pd.DataFrame()
    ag = snap.aggregates
    pred_n, esco_pct, genai_pct = _taxonomy_display(ag)
    rows = {
        "Run": [name],
        "Mode": [snap.extractor_mode],
        "Skills P": [ag.precision_skills],
        "Skills R": [ag.recall_skills],
        "Skills F1": [ag.f1_skills],
        "Tools P": [ag.precision_tools],
        "Tools R": [ag.recall_tools],
        "Tools F1": [ag.f1_tools],
        "Tasks P": [ag.precision_tasks],
        "Tasks R": [ag.recall_tasks],
        "Tasks F1": [ag.f1_tasks],
        "Resp P": [ag.precision_responsibilities],
        "Resp R": [ag.recall_responsibilities],
        "Resp F1": [ag.f1_responsibilities],
        "Ctx P": [ag.precision_context],
        "Ctx R": [ag.recall_context],
        "Ctx F1": [ag.f1_context],
        "GT skills": [ag.total_gt_skills],
        "Pred skills": [ag.total_pred_skills],
        "Mtch skills": [ag.matched_skills],
        "GT tools": [ag.total_gt_tools],
        "Pred tools": [ag.total_pred_tools],
        "Mtch tools": [ag.matched_tools],
        "GT tasks": [ag.total_gt_tasks],
        "Pred tasks": [ag.total_pred_tasks],
        "Mtch tasks": [ag.matched_tasks],
        "GT resp": [ag.total_gt_responsibilities],
        "Pred resp": [ag.total_pred_responsibilities],
        "Mtch resp": [ag.matched_responsibilities],
        "GT ctx": [ag.total_gt_context],
        "Pred ctx": [ag.total_pred_context],
        "Mtch ctx": [ag.matched_context],
        "SkillRec #": [pred_n],
        "ESCO %": [esco_pct],
        "GenAI %": [genai_pct],
        "Tokens": [ag.total_tokens_used if ag.llm_applicable else "N/A"],
        "Cost USD": [ag.total_cost_usd if ag.llm_applicable else "N/A"],
        "Latency ms (sum)": [ag.total_latency_ms if ag.llm_applicable else "N/A"],
        "Wall s": [snap.runtime_seconds],
        "MT time": [snap.mt_timestamp_iso],
    }
    return pd.DataFrame(rows)


def _per_job_df(snap: ExtractionEvalSnapshot) -> pd.DataFrame:
    rows = []
    for j in snap.per_job:
        rows.append(
            {
                "job_key": j.job_key,
                "title": j.title[:80] + ("…" if len(j.title) > 80 else ""),
                "skills_P": j.precision_skills,
                "skills_R": j.recall_skills,
                "skills_F1": j.f1_skills,
                "tools_P": j.precision_tools,
                "tools_R": j.recall_tools,
                "tools_F1": j.f1_tools,
                "tasks_P": j.precision_tasks,
                "tasks_R": j.recall_tasks,
                "tasks_F1": j.f1_tasks,
                "resp_P": j.precision_responsibilities,
                "resp_R": j.recall_responsibilities,
                "resp_F1": j.f1_responsibilities,
                "ctx_P": j.precision_context,
                "ctx_R": j.recall_context,
                "ctx_F1": j.f1_context,
                "missed_skills": ", ".join(j.missed_skills[:10]),
                "fp_skills": ", ".join(j.false_positive_skills[:10]),
                "missed_tools": ", ".join(j.missed_tools[:8]),
                "fp_tools": ", ".join(j.false_positive_tools[:8]),
                "missed_tasks": ", ".join(j.missed_tasks[:6]),
                "fp_tasks": ", ".join(j.false_positive_tasks[:6]),
                "missed_resp": ", ".join(j.missed_responsibilities[:6]),
                "fp_resp": ", ".join(j.false_positive_responsibilities[:6]),
                "missed_ctx": ", ".join(j.missed_context[:6]),
                "fp_ctx": ", ".join(j.false_positive_context[:6]),
            }
        )
    return pd.DataFrame(rows)


def _render_dimension_block(j, dim_key: str, title: str, missed_limit: int) -> None:
    st.markdown(f"**{title}**")
    gt = getattr(j, f"gt_{dim_key}")
    pred = getattr(j, f"pred_{dim_key}")
    st.caption("GT")
    st.write(gt)
    st.caption("Predicted")
    st.write(pred)
    st.caption("Matched / missed / FP")
    st.write(
        {
            "matched": getattr(j, f"matched_{dim_key}"),
            "missed": getattr(j, f"missed_{dim_key}")[:missed_limit],
            "fp": getattr(j, f"false_positive_{dim_key}")[:missed_limit],
        }
    )
    p = getattr(j, f"precision_{dim_key}")
    r = getattr(j, f"recall_{dim_key}")
    f1 = getattr(j, f"f1_{dim_key}")
    st.caption(f"P / R / F1: {p:.2f} / {r:.2f} / {f1:.2f}")


def _job_expander(j) -> None:
    tshort = j.title[:60] + ("…" if len(j.title) > 60 else "")
    with st.expander(f"{j.job_key} — {tshort}"):
        if j.extraction_failed:
            st.warning("extraction_failed=true on this job (see pipeline metadata).")
        _render_dimension_block(j, "skills", "Skills", 20)
        _render_dimension_block(j, "tools", "Tools", 12)
        _render_dimension_block(j, "tasks", "Tasks", 12)
        _render_dimension_block(j, "responsibilities", "Responsibilities", 12)
        _render_dimension_block(j, "context", "Context", 12)


st.set_page_config(page_title="Extraction eval compare", layout="wide")
st.title("Extraction eval — compare runs")

for k in ("eval_snap1", "eval_snap2"):
    if k not in st.session_state:
        st.session_state[k] = None

gt_path_str = st.text_input("Ground truth JSON path", value=str(_DEFAULT_GT))
st.session_state["gt_path_str"] = gt_path_str

layout = st.radio("Layout", ["GT + one run", "GT + two runs"], horizontal=True)

st.subheader("Run 1")
src1 = st.radio("Run 1 source", ["Run now", "Load snapshot"], horizontal=True, key="src1")
if src1 == "Run now":
    _run_panel("run1", "eval_snap1")
else:
    loaded = _load_snapshot_ui("run1")
    if loaded is not None:
        st.session_state["eval_snap1"] = loaded

snap1: ExtractionEvalSnapshot | None = st.session_state.get("eval_snap1")

if layout == "GT + two runs":
    st.subheader("Run 2")
    src2 = st.radio("Run 2 source", ["Run now", "Load snapshot"], horizontal=True, key="src2")
    if src2 == "Run now":
        _run_panel("run2", "eval_snap2")
    else:
        loaded2 = _load_snapshot_ui("run2")
        if loaded2 is not None:
            st.session_state["eval_snap2"] = loaded2

snap2: ExtractionEvalSnapshot | None = st.session_state.get("eval_snap2") if layout == "GT + two runs" else None

if snap1 is None:
    st.info("Configure **Run 1** (load a snapshot or click **Run eval**).")
    st.stop()

if snap1.schema_version not in _SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS:
    st.warning(
        f"Run 1 snapshot schema is `{snap1.schema_version}`; "
        f"supported: {', '.join(sorted(_SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS))}."
    )

if snap2 and snap2.schema_version not in _SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS:
    st.warning(
        f"Run 2 snapshot schema is `{snap2.schema_version}`; "
        f"supported: {', '.join(sorted(_SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS))}."
    )

st.divider()
st.subheader("Aggregate metrics")

if layout == "GT + one run":
    st.dataframe(_metrics_df(snap1, "Run 1"), use_container_width=True)
else:
    df = pd.concat(
        [_metrics_df(snap1, "Run 1"), _metrics_df(snap2, "Run 2")],
        ignore_index=True,
    )
    st.dataframe(df, use_container_width=True)
    if snap2 is not None:
        st.subheader("Delta (Run 2 − Run 1)")
        a1, a2 = snap1.aggregates, snap2.aggregates
        d = {
            "Δ Skills P": a2.precision_skills - a1.precision_skills,
            "Δ Skills R": a2.recall_skills - a1.recall_skills,
            "Δ Skills F1": a2.f1_skills - a1.f1_skills,
            "Δ Tools P": a2.precision_tools - a1.precision_tools,
            "Δ Tools R": a2.recall_tools - a1.recall_tools,
            "Δ Tools F1": a2.f1_tools - a1.f1_tools,
            "Δ Tasks P": a2.precision_tasks - a1.precision_tasks,
            "Δ Tasks R": a2.recall_tasks - a1.recall_tasks,
            "Δ Tasks F1": a2.f1_tasks - a1.f1_tasks,
            "Δ Resp P": a2.precision_responsibilities - a1.precision_responsibilities,
            "Δ Resp R": a2.recall_responsibilities - a1.recall_responsibilities,
            "Δ Resp F1": a2.f1_responsibilities - a1.f1_responsibilities,
            "Δ Ctx P": a2.precision_context - a1.precision_context,
            "Δ Ctx R": a2.recall_context - a1.recall_context,
            "Δ Ctx F1": a2.f1_context - a1.f1_context,
        }
        if a1.llm_applicable and a2.llm_applicable:
            d["Δ Tokens"] = (a2.total_tokens_used or 0) - (a1.total_tokens_used or 0)
            d["Δ Cost USD"] = (a2.total_cost_usd or 0.0) - (a1.total_cost_usd or 0.0)
            d["Δ Latency ms"] = (a2.total_latency_ms or 0) - (a1.total_latency_ms or 0)
        st.json(d)

st.subheader("Per-job diff (Run 1)")
with st.expander("Table", expanded=False):
    st.dataframe(_per_job_df(snap1), use_container_width=True, height=400)

for j in snap1.per_job[:50]:
    _job_expander(j)

if snap2 is not None:
    st.subheader("Per-job diff (Run 2)")
    with st.expander("Table (Run 2)", expanded=False):
        st.dataframe(_per_job_df(snap2), use_container_width=True, height=400)

    st.subheader("Side-by-side by job_key (pred only: Run1 | Run2)")
    by1 = {p.job_key: p for p in snap1.per_job}
    by2 = {p.job_key: p for p in snap2.per_job}
    keys = sorted(set(by1) | set(by2))
    for k in keys[:30]:
        j1 = by1.get(k)
        j2 = by2.get(k)
        with st.expander(k):
            for dim, label in (
                ("skills", "Skills"),
                ("tools", "Tools"),
                ("tasks", "Tasks"),
                ("responsibilities", "Responsibilities"),
                ("context", "Context"),
            ):
                st.markdown(f"**{label}**")
                st.json(
                    {
                        "run1_pred": getattr(j1, f"pred_{dim}", None) if j1 else None,
                        "run2_pred": getattr(j2, f"pred_{dim}", None) if j2 else None,
                    }
                )
