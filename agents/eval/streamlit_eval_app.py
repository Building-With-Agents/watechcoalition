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
from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")

from agents.eval.extraction_eval_core import load_ground_truth, run_eval_dataset
from agents.eval.snapshot_schema import SNAPSHOT_SCHEMA_VERSION, ExtractionEvalSnapshot, load_snapshot

_EVAL_DIR = Path(__file__).resolve().parent
_DEFAULT_GT = _EVAL_DIR / "extraction_ground_truth.json"
_DEFAULT_RUNS = _EVAL_DIR / "runs"
_DEFAULT_BACKLOG = _EVAL_DIR / "prompt_backlog"


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


def _metrics_df(snap: ExtractionEvalSnapshot | None, name: str) -> pd.DataFrame:
    if snap is None:
        return pd.DataFrame()
    ag = snap.aggregates
    rows = {
        "Run": [name],
        "Mode": [snap.extractor_mode],
        "Skills P": [ag.precision_skills],
        "Skills R": [ag.recall_skills],
        "Tools P": [ag.precision_tools],
        "Tools R": [ag.recall_tools],
        "GT skills": [ag.total_gt_skills],
        "Pred skills": [ag.total_pred_skills],
        "Matched skills": [ag.matched_skills],
        "GT tools": [ag.total_gt_tools],
        "Pred tools": [ag.total_pred_tools],
        "Matched tools": [ag.matched_tools],
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
                "tools_P": j.precision_tools,
                "tools_R": j.recall_tools,
                "missed_skills": ", ".join(j.missed_skills[:12]),
                "fp_skills": ", ".join(j.false_positive_skills[:12]),
                "missed_tools": ", ".join(j.missed_tools[:8]),
                "fp_tools": ", ".join(j.false_positive_tools[:8]),
            }
        )
    return pd.DataFrame(rows)


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

snap2: ExtractionEvalSnapshot | None = (
    st.session_state.get("eval_snap2") if layout == "GT + two runs" else None
)

if snap1 is None:
    st.info("Configure **Run 1** (load a snapshot or click **Run eval**).")
    st.stop()

if snap1.schema_version != SNAPSHOT_SCHEMA_VERSION:
    st.warning(
        f"Run 1 snapshot schema is `{snap1.schema_version}`; "
        f"app expects `{SNAPSHOT_SCHEMA_VERSION}`."
    )

if snap2 and snap2.schema_version != SNAPSHOT_SCHEMA_VERSION:
    st.warning(
        f"Run 2 snapshot schema is `{snap2.schema_version}`; "
        f"app expects `{SNAPSHOT_SCHEMA_VERSION}`."
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
            "Δ Tools P": a2.precision_tools - a1.precision_tools,
            "Δ Tools R": a2.recall_tools - a1.recall_tools,
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
    tshort = j.title[:60] + ("…" if len(j.title) > 60 else "")
    with st.expander(f"{j.job_key} — {tshort}"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Skills**")
            st.caption("GT")
            st.write(j.gt_skills)
            st.caption("Predicted")
            st.write(j.pred_skills)
            st.caption("Matched / missed / FP")
            st.write({"matched": j.matched_skills, "missed": j.missed_skills, "fp": j.false_positive_skills})
        with c2:
            st.markdown("**Tools**")
            st.caption("GT")
            st.write(j.gt_tools)
            st.caption("Predicted")
            st.write(j.pred_tools)
            st.caption("Matched / missed / FP")
            st.write({"matched": j.matched_tools, "missed": j.missed_tools, "fp": j.false_positive_tools})
        st.caption(
            f"P/R skills {j.precision_skills:.2f} / {j.recall_skills:.2f} · "
            f"tools {j.precision_tools:.2f} / {j.recall_tools:.2f}"
        )

if snap2 is not None:
    st.subheader("Per-job diff (Run 2)")
    with st.expander("Table (Run 2)", expanded=False):
        st.dataframe(_per_job_df(snap2), use_container_width=True, height=400)

    st.subheader("Side-by-side by job_key (GT | Run1 | Run2)")
    by1 = {p.job_key: p for p in snap1.per_job}
    by2 = {p.job_key: p for p in snap2.per_job}
    keys = sorted(set(by1) | set(by2))
    for k in keys[:30]:
        j1 = by1.get(k)
        j2 = by2.get(k)
        with st.expander(k):
            st.markdown("**Skills**")
            st.json(
                {
                    "run1_pred": j1.pred_skills if j1 else None,
                    "run2_pred": j2.pred_skills if j2 else None,
                }
            )
            st.markdown("**Tools**")
            st.json(
                {
                    "run1_pred": j1.pred_tools if j1 else None,
                    "run2_pred": j2.pred_tools if j2 else None,
                }
            )
