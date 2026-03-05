"""
Streamlit dashboard: pipeline run summary, record journey, and batch insights.
Driven ONLY by agents/data/output/pipeline_run.json.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import streamlit as st

_agents_root = Path(__file__).resolve().parent.parent
PIPELINE_RUN_PATH = _agents_root / "data" / "output" / "pipeline_run.json"

EXPECTED_RECORDS = 10
EXPECTED_STAGES_PER_RECORD = 8


def load_events():
    """
    Load pipeline_run.json. Returns (list of event dicts, None) on success
    or (None, error_message) on failure.
    """
    if not PIPELINE_RUN_PATH.exists():
        return None, f"Pipeline output not found: {PIPELINE_RUN_PATH}. Run the pipeline first (e.g. python -m agents.pipeline_runner)."
    try:
        with open(PIPELINE_RUN_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in pipeline output: {e}"
    if not isinstance(data, list):
        return None, "Expected pipeline output to be a JSON array."
    return data, None


def events_to_dataframe(events: list[dict]) -> list[dict]:
    """
    Convert event list to rows suitable for display: correlation_id, agent_id,
    timestamp, payload_summary, phase2_skipped.
    """
    rows = []
    for e in events:
        payload = e.get("payload") or {}
        rows.append({
            "correlation_id": e.get("correlation_id", ""),
            "agent_id": e.get("agent_id", ""),
            "timestamp": e.get("timestamp", ""),
            "payload_summary": summarize_payload(e),
            "phase2_skipped": payload.get("phase2_skipped") is True,
        })
    return rows


def summarize_payload(entry: dict) -> str:
    """
    Return a short summary of the payload for display (no hardcoded metrics).
    """
    payload = entry.get("payload")
    if not payload:
        return "—"
    if payload.get("phase2_skipped") is True:
        return "Phase 2 skipped"
    postings = payload.get("postings")
    if isinstance(postings, list):
        n = len(postings)
        return f"{n} posting(s)"
    if "top_skills" in payload:
        skills = payload.get("top_skills") or []
        return f"top_skills: {len(skills)} item(s)"
    if "run_id" in payload or "total_postings" in payload:
        total = payload.get("total_postings", "—")
        return f"analytics run, total_postings={total}"
    keys = list(payload.keys())[:5]
    return ", ".join(keys) if keys else "—"


def _run_times(events: list[dict]) -> tuple[str | None, str | None, str | None]:
    """Return (min_ts, max_ts, duration_str) from event timestamps."""
    timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
    if not timestamps:
        return None, None, None
    try:
        parsed = [_parse_iso_safe(ts) for ts in timestamps]
        parsed = [p for p in parsed if p is not None]
        if not parsed:
            return None, None, None
        min_ts = min(parsed).isoformat()
        max_ts = max(parsed).isoformat()
        delta = max(parsed) - min(parsed)
        duration_str = str(delta)
        return min_ts, max_ts, duration_str
    except Exception:
        return timestamps[0], timestamps[-1], "—"


def _group_by_correlation(events: list[dict]) -> dict[str, list[dict]]:
    out = {}
    for e in events:
        cid = e.get("correlation_id", "")
        out.setdefault(cid, []).append(e)
    return out


def _parse_iso_safe(ts: str) -> datetime | None:
    """Parse ISO timestamp; return None on failure."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def page_summary(events: list[dict]) -> None:
    st.subheader("Pipeline Run Summary")
    run_start, run_end, duration = _run_times(events)
    st.write("**Run start:**", run_start or "—")
    st.write("**Run end:**", run_end or "—")
    st.write("**Duration:**", duration or "—")

    by_cid = _group_by_correlation(events)
    n_unique = len(by_cid)
    all_have_8 = all(len(g) == EXPECTED_STAGES_PER_RECORD for g in by_cid.values())
    all_complete = n_unique == EXPECTED_RECORDS and all_have_8
    if all_complete:
        st.write("**All 10 records completed all 8 stages:**", "Yes")
    else:
        reasons = []
        if n_unique != EXPECTED_RECORDS:
            reasons.append(f"expected {EXPECTED_RECORDS} unique correlation_ids, got {n_unique}")
        if not all_have_8:
            bad = [cid for cid, g in by_cid.items() if len(g) != EXPECTED_STAGES_PER_RECORD]
            reasons.append(f"some records have ≠8 stages: {bad[:3]}{'…' if len(bad) > 3 else ''}")
        st.write("**All 10 records completed all 8 stages:**", f"No ({'; '.join(reasons)})")

    by_cid = _group_by_correlation(events)
    table_rows = []
    for cid, group in sorted(by_cid.items()):
        table_rows.append({
            "correlation_id": cid[:8] + "…" if len(cid) > 8 else cid,
            "correlation_id_full": cid,
            "stage_count": len(group),
            "completed_all_stages": len(group) == EXPECTED_STAGES_PER_RECORD,
        })
    summary_table = [
        {"correlation_id": r["correlation_id"], "stage_count": r["stage_count"], "completed_all_stages": r["completed_all_stages"]}
        for r in table_rows
    ]
    st.dataframe(summary_table, use_container_width=True, hide_index=True)

    with st.expander("Debug / Sanity Checks"):
        st.write("**Total entries loaded:**", len(events))
        st.write("**Unique correlation_id values:**", len(by_cid))
        agent_ids_order = list(dict.fromkeys(e.get("agent_id", "") for e in events))
        st.write("**Agent IDs (order of appearance):**", agent_ids_order)


def page_record_journey(events: list[dict]) -> None:
    st.subheader("Record Journey")
    by_cid = _group_by_correlation(events)
    correlation_ids = sorted(by_cid.keys())
    if not correlation_ids:
        st.info("No correlation IDs in run.")
        return
    selected = st.selectbox("Choose correlation_id", options=correlation_ids, key="journey_cid")
    st.write("**correlation_id:**", selected)

    group = by_cid[selected]
    group_sorted = sorted(group, key=lambda e: _parse_iso_safe(e.get("timestamp")) or datetime.min)
    rows = events_to_dataframe(group_sorted)
    display_rows = [
        {
            "event": (e.get("event_id") or "")[:8],
            "agent_id": r["agent_id"],
            "timestamp": r["timestamp"],
            "payload_summary": r["payload_summary"],
            "phase2_skipped": "Yes" if r["phase2_skipped"] else "No",
        }
        for e, r in zip(group_sorted, rows)
    ]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)
    if any(r["phase2_skipped"] for r in rows):
        st.caption("One or more stages show Phase 2 skipped (demand_analysis_agent not implemented).")


def _top_skills_from_analytics(events: list[dict]) -> Counter:
    """Aggregate top_skills from analytics_agent payloads. No hardcoding."""
    out = Counter()
    for e in events:
        if e.get("agent_id") != "analytics_agent":
            continue
        payload = e.get("payload") or {}
        for item in payload.get("top_skills") or []:
            name = (item.get("skill") or item.get("name") or "").strip()
            if name:
                out[name] += item.get("count", 1)
    return out


def _iter_postings(payload: dict) -> list[dict]:
    """Yield posting dicts from payload: either postings[] or single posting (has skills/seniority)."""
    postings = payload.get("postings")
    if isinstance(postings, list):
        return postings
    if isinstance(payload, dict) and (payload.get("skills") is not None or payload.get("seniority") is not None or "company" in payload or "location" in payload):
        return [payload]
    return []


def _top_skills_from_postings(events: list[dict]) -> Counter:
    """Compute skill counts from skills_extraction_agent / enrichment_agent; supports postings[] or single posting."""
    out = Counter()
    for e in events:
        if e.get("agent_id") not in ("skills_extraction_agent", "enrichment_agent"):
            continue
        payload = e.get("payload") or {}
        for p in _iter_postings(payload):
            for s in p.get("skills") or []:
                name = (s.get("name") or s.get("skill") or "").strip()
                if name:
                    out[name] += 1
    return out


def _seniority_from_analytics(events: list[dict]) -> Counter:
    """Aggregate seniority_distribution from analytics_agent payloads."""
    out = Counter()
    for e in events:
        if e.get("agent_id") != "analytics_agent":
            continue
        dist = (e.get("payload") or {}).get("seniority_distribution")
        if isinstance(dist, dict):
            for k, v in dist.items():
                if isinstance(v, (int, float)):
                    out[k] += int(v)
    return out


def _seniority_from_postings(events: list[dict]) -> Counter:
    """Compute seniority counts from skills_extraction_agent / enrichment_agent; supports postings[] or single posting."""
    out = Counter()
    for e in events:
        if e.get("agent_id") not in ("skills_extraction_agent", "enrichment_agent"):
            continue
        payload = e.get("payload") or {}
        for p in _iter_postings(payload):
            s = (p.get("seniority") or "").strip()
            if s:
                out[s] += 1
    return out


def _locations_from_analytics(events: list[dict]) -> set:
    """Location names from analytics_agent payload.locations (dict keys)."""
    out = set()
    for e in events:
        if e.get("agent_id") != "analytics_agent":
            continue
        locs = (e.get("payload") or {}).get("locations")
        if isinstance(locs, dict):
            for k in locs.keys():
                if k:
                    out.add(str(k).strip())
    return out


def _companies_locations_from_postings(events: list[dict]) -> tuple[set, set]:
    """Companies and locations from ingestion_agent / normalization_agent; supports postings[] or single posting dict."""
    companies, locations = set(), set()
    for e in events:
        if e.get("agent_id") not in ("ingestion_agent", "normalization_agent"):
            continue
        payload = e.get("payload") or {}
        postings = payload.get("postings")
        if isinstance(postings, list):
            items = postings
        elif isinstance(payload, dict) and ("company" in payload or "location" in payload):
            items = [payload]
        else:
            items = []
        for p in items:
            c = (p.get("company") or "").strip()
            loc = (p.get("location") or "").strip()
            if c:
                companies.add(c)
            if loc:
                locations.add(loc)
    return companies, locations


def page_batch_insights(events: list[dict]) -> None:
    st.subheader("Batch Insights")
    real_events = [e for e in events if (e.get("payload") or {}).get("phase2_skipped") is not True]

    # Top skills: prefer analytics_agent top_skills, else compute from skills_extraction/enrichment postings
    skill_counts = _top_skills_from_analytics(real_events)
    if not skill_counts:
        skill_counts = _top_skills_from_postings(real_events)
    if skill_counts:
        top_skills = skill_counts.most_common(15)
        st.bar_chart({name: count for name, count in top_skills})
    else:
        st.caption("No skill data in payloads.")

    # Seniority: prefer analytics_agent seniority_distribution, else compute from postings
    seniority_counts = _seniority_from_analytics(real_events)
    if not seniority_counts:
        seniority_counts = _seniority_from_postings(real_events)
    if seniority_counts:
        st.bar_chart(dict(seniority_counts))
    else:
        st.caption("No seniority data in payloads.")

    # Companies: from ingestion/normalization only (analytics has no companies). Locations: prefer analytics.locations, else ingestion/normalization
    companies, locations_from_postings = _companies_locations_from_postings(real_events)
    locations = _locations_from_analytics(real_events)
    if not locations:
        locations = locations_from_postings
    st.write("**Companies represented:**", ", ".join(sorted(companies)) if companies else "—")
    st.write("**Locations represented:**", ", ".join(sorted(locations)) if locations else "—")


def main() -> None:
    st.set_page_config(page_title="Pipeline Dashboard", layout="wide")
    st.title("Pipeline Run Dashboard")

    events, err = load_events()
    if err is not None:
        st.error(err)
        st.stop()

    page = st.sidebar.radio(
        "Page",
        ["Pipeline Run Summary", "Record Journey", "Batch Insights"],
        key="page_radio",
    )

    if page == "Pipeline Run Summary":
        page_summary(events)
    elif page == "Record Journey":
        page_record_journey(events)
    else:
        page_batch_insights(events)


if __name__ == "__main__":
    main()
