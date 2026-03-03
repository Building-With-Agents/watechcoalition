"""Streamlit dashboard — Exercise 1.3 raw scrape viewer.

Loads agents/data/staging/raw_scrape_sample.json and displays each posting in an
expandable card with source, URL, timestamp, and raw text preview. Sidebar filter by source.
Run with: streamlit run agents/dashboard/streamlit_app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

# Same path as scraper: agents/data/staging/raw_scrape_sample.json (relative to agents/)
_AGENTS_DIR = Path(__file__).resolve().parent.parent
RAW_SCRAPE_PATH = _AGENTS_DIR / "data" / "staging" / "raw_scrape_sample.json"

PREVIEW_LENGTH = 500


@st.cache_data(ttl=60)
def load_raw_scrape() -> dict | None:
    """Load raw_scrape_sample.json; return None if missing or invalid."""
    if not RAW_SCRAPE_PATH.exists():
        return None
    try:
        with open(RAW_SCRAPE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "jobs" not in data:
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def main() -> None:
    st.set_page_config(page_title="Job Intelligence Engine", page_icon="📊")
    st.title("Job Intelligence Engine")
    st.caption("Raw scrape viewer (Exercise 1.3)")

    data = load_raw_scrape()
    if data is None:
        st.warning(
            f"No data found at `{RAW_SCRAPE_PATH}`. Run the scraper first: "
            "`python -m agents.ingestion.sources.scraper_adapter`"
        )
        return

    jobs = data.get("jobs") or []
    if not jobs:
        st.info("The scrape file has no job postings yet. Run the scraper to populate it.")
        return

    # Unique source names for sidebar filter
    sources = sorted({str(j.get("source") or "unknown").strip() for j in jobs if j.get("source")})
    if not sources:
        sources = ["unknown"]

    # Sidebar: filter by source (actually filters the list)
    st.sidebar.subheader("Filter by source")
    selected_sources = st.sidebar.multiselect(
        "Source name",
        options=sources,
        default=sources,
        key="source_filter",
    )
    if not selected_sources:
        filtered_jobs = []
        st.sidebar.caption("Select at least one source to show postings.")
    else:
        selected_set = set(selected_sources)
        filtered_jobs = [j for j in jobs if str(j.get("source") or "").strip() in selected_set]

    st.sidebar.metric("Postings shown", len(filtered_jobs))
    st.sidebar.metric("Total in file", len(jobs))

    if not filtered_jobs:
        st.info("No postings match the selected source(s).")
        return

    st.subheader("Job postings")
    for i, job in enumerate(filtered_jobs):
        source = job.get("source") or ""
        url = job.get("url") or ""
        scraped_at = job.get("scraped_at") or ""
        raw_text = job.get("raw_text") or ""
        raw_text = str(raw_text)
        title = job.get("title") or ""
        index = job.get("index", i + 1)

        label = f"#{index}"
        if title:
            label = f"{label} — {title[:60]}{'…' if len(title) > 60 else ''}"
        elif url:
            label = f"{label} — {url[:50]}…" if len(url) > 50 else f"{label} — {url}"

        with st.expander(label, expanded=(i == 0)):
            st.markdown("**Source:** " + (source or "—"))
            if url:
                st.markdown("**URL scraped:**")
                st.markdown(f"[{url}]({url})")
            st.markdown("**Timestamp:** " + (scraped_at or "—"))
            st.markdown("**Raw text preview:**")
            preview = raw_text[:PREVIEW_LENGTH] + ("…" if len(raw_text) > PREVIEW_LENGTH else "")
            st.text(preview) if preview else st.caption("(no text)")


if __name__ == "__main__":
    main()
