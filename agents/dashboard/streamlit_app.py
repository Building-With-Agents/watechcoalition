"""
Streamlit dashboard — three-page journey: Pipeline Run Summary, Record Journey, Batch Insights.

Uses pipeline_run.json (Pages 1–2) and fixture files under agents/data/fixtures (Page 3).
Run from repo root: streamlit run agents/dashboard/streamlit_app.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

import streamlit as st

# Paths relative to this file: agents/dashboard/streamlit_app.py -> agents = parents[1]
AGENTS_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_RUN_PATH = AGENTS_ROOT / "data" / "output" / "pipeline_run.json"
FIXTURES_DIR = AGENTS_ROOT / "data" / "fixtures"


def _parse_ts_utc(s: str) -> datetime | None:
    """Parse ISO timestamp to UTC-aware datetime. Naive timestamps treated as UTC."""
    if not s:
        return None
    try:
        s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def load_pipeline_run():
    """
    Load pipeline_run.json. Supports: (1) list of runs, (2) single run object (legacy).
    Returns (aggregated_data, error_message). On success data has: run_log (combined), runs (list), latest_run.
    """
    if not PIPELINE_RUN_PATH.exists():
        return None, f"File not found: {PIPELINE_RUN_PATH}. Run the pipeline first."
    try:
        text = PIPELINE_RUN_PATH.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"Could not read file: {e}"
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"
    if isinstance(raw, list):
        runs = [r for r in raw if isinstance(r, dict) and isinstance(r.get("run_log"), list)]
    elif isinstance(raw, dict) and isinstance(raw.get("run_log"), list):
        runs = [raw]
    else:
        return None, "Expected JSON root to be a list of runs or a single run object with 'run_log'."
    if not runs:
        return None, "No valid runs in file."
    run_log = []
    for r in runs:
        run_log.extend(r.get("run_log") or [])
    return {
        "run_log": run_log,
        "runs": runs,
        "latest_run": runs[-1],
    }, None


def load_json_fixture(filename: str):
    """Load a JSON file from agents/data/fixtures. Returns (data, error_message)."""
    path = FIXTURES_DIR / filename
    if not path.exists():
        return None, f"File not found: {path}"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, str(e)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return None, str(e)
    return data, None


def page_pipeline_summary(data: dict):
    run_log = data.get("run_log", [])
    runs = data.get("runs", [])
    latest_run = data.get("latest_run") or {}

    # Summary: X of Y runs completed all 8 stages
    def _run_complete(r):
        if r.get("aborted"):
            return False
        rl = r.get("run_log") or []
        by_cid = {}
        for e in rl:
            cid = e.get("correlation_id") or ""
            by_cid[cid] = by_cid.get(cid, 0) + 1
        return all(count == 8 for count in by_cid.values()) if by_cid else False

    complete_count = sum(1 for r in runs if _run_complete(r))
    total_runs = len(runs)

    st.subheader("Did all records make it through all 8 stages?")
    if total_runs == 1 and latest_run.get("aborted"):
        st.warning("No. The pipeline aborted. " + (latest_run.get("reason", "") or ""))
    elif total_runs == 1:
        by_cid = {}
        for e in run_log:
            cid = e.get("correlation_id") or ""
            by_cid[cid] = by_cid.get(cid, 0) + 1
        if by_cid and all(count == 8 for count in by_cid.values()):
            st.success("Yes. All records completed all 8 stages.")
        else:
            st.warning("No. Some records did not complete all 8 stages (see table below).")
    else:
        st.success(f"{complete_count} of {total_runs} runs completed all 8 stages.")
        if complete_count < total_runs:
            st.caption("See Correlation ID table for per-run status.")

    st.subheader("Run timing (latest run)")
    lr_log = latest_run.get("run_log") or []
    timestamps = [e.get("timestamp") for e in lr_log if e.get("timestamp")]
    if len(timestamps) >= 2:
        t0 = _parse_ts_utc(timestamps[0])
        t1 = _parse_ts_utc(timestamps[-1])
        if t0 is not None and t1 is not None:
            duration = (t1 - t0).total_seconds()
            st.metric("First event", timestamps[0])
            st.metric("Last event", timestamps[-1])
            st.metric("Duration (seconds)", f"{duration:.2f}")
        else:
            st.metric("First event", timestamps[0])
            st.metric("Last event", timestamps[-1])
            st.caption("Duration: N/A (could not parse timestamps)")
    else:
        st.metric("Run timestamp", timestamps[0] if timestamps else "—")
        st.caption("Duration: N/A (single or no timestamps)")

    st.subheader("Correlation ID table")
    by_cid = {}
    for entry in run_log:
        cid = entry.get("correlation_id") or ""
        if cid not in by_cid:
            by_cid[cid] = 0
        by_cid[cid] += 1
    rows = []
    for cid, count in by_cid.items():
        status = "All complete" if count == 8 else "Incomplete"
        rows.append({"correlation_id": cid, "stages_completed": count, "status": status})
    if rows:
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No correlation IDs in run_log.")


def page_record_journey(data: dict):
    run_log = data.get("run_log", [])
    distinct_cids = sorted({e.get("correlation_id") or "" for e in run_log if e.get("correlation_id")})

    if not distinct_cids:
        st.info("No correlation IDs in run_log.")
        return

    selected = st.selectbox("Select record by correlation_id", options=distinct_cids, key="journey_cid")
    st.write("**Correlation ID:**", selected)

    filtered = [e for e in run_log if (e.get("correlation_id") or "") == selected]
    if not filtered:
        st.info("No entries for this correlation_id.")
        return

    # Order by timestamp if present, else keep run_log order
    has_ts = all(e.get("timestamp") for e in filtered)
    if has_ts:
        try:
            filtered = sorted(filtered, key=lambda e: e.get("timestamp", ""))
        except Exception:
            pass

    st.subheader("Timeline")
    for i, entry in enumerate(filtered, start=1):
        agent_id = entry.get("agent_id", "—")
        event_id = entry.get("event_id") or "(none)"
        ts = entry.get("timestamp", "—")
        payload_keys = entry.get("payload_keys", [])
        payload_summary = ", ".join(payload_keys) if payload_keys else "(no keys)"
        if len(payload_summary) > 100:
            payload_summary = payload_summary[:97] + "..."
        with st.expander(f"{i}. {agent_id}"):
            st.write("Event ID:", event_id)
            st.write("Timestamp:", ts)
            st.write("Payload summary:", payload_summary)


def page_batch_insights():
    # Skills from fixture_skills_extracted.json
    skills_data, err = load_json_fixture("fixture_skills_extracted.json")
    if err:
        st.error("Skills fixture: " + err)
        skill_counts = Counter()
    else:
        skill_counts = Counter()
        records = skills_data if isinstance(skills_data, list) else [skills_data]
        for rec in records:
            for s in rec.get("skills") or []:
                name = s.get("name") or s.get("label")
                if name:
                    skill_counts[name] += 1

    st.subheader("Top skills across postings")
    if skill_counts:
        top = skill_counts.most_common(15)
        import pandas as pd
        df = pd.DataFrame(top, columns=["Skill", "Count"])
        st.bar_chart(df.set_index("Skill"))
    else:
        st.info("No skill data in fixture.")

    # Seniority from fixture_skills_extracted or fixture_enriched
    seniority_counts = Counter()
    for fname in ("fixture_skills_extracted.json", "fixture_enriched.json"):
        data, _ = load_json_fixture(fname)
        if not data:
            continue
        records = data if isinstance(data, list) else [data]
        for rec in records:
            s = rec.get("seniority")
            if s:
                seniority_counts[s] += 1
        if seniority_counts:
            break

    st.subheader("Seniority distribution")
    if seniority_counts:
        import pandas as pd
        df = pd.DataFrame(list(seniority_counts.items()), columns=["Seniority", "Count"])
        st.bar_chart(df.set_index("Seniority"))
    else:
        st.info("No seniority data in fixtures.")

    # Companies and locations from fallback_scrape_sample or fixture_enriched
    companies = set()
    locations = set()
    for fname in ("fallback_scrape_sample.json", "fixture_enriched.json"):
        data, _ = load_json_fixture(fname)
        if not data:
            continue
        records = data if isinstance(data, list) else [data]
        for rec in records:
            if rec.get("company"):
                companies.add(rec["company"])
            if rec.get("location"):
                locations.add(rec["location"])
        if companies or locations:
            break

    st.subheader("Companies and locations represented")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Companies**")
        if companies:
            for c in sorted(companies):
                st.write("-", c)
        else:
            st.caption("None found in fixtures.")
    with col2:
        st.write("**Locations**")
        if locations:
            for loc in sorted(locations):
                st.write("-", loc)
        else:
            st.caption("None found in fixtures.")


def main():
    st.set_page_config(page_title="Pipeline Journey Dashboard", layout="wide")
    st.title("Pipeline Journey Dashboard")

    data, err = load_pipeline_run()
    if err:
        st.error(err)
        # Still allow Page 3 (fixtures only)
        data = None

    page = st.sidebar.radio(
        "Page",
        ["Pipeline Run Summary", "Record Journey", "Batch Insights"],
        index=0,
    )

    if page == "Pipeline Run Summary":
        if data is None:
            st.error("Load pipeline_run.json to view this page.")
        else:
            page_pipeline_summary(data)
    elif page == "Record Journey":
        if data is None:
            st.error("Load pipeline_run.json to view this page.")
        else:
            page_record_journey(data)
    else:
        page_batch_insights()


if __name__ == "__main__":
    main()
