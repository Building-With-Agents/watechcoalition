"""
Basic Streamlit dashboard — Exercise 1.3

Displays raw scraped job postings from agents/data/staging/raw_scrape_sample.json
with expandable cards and a sidebar source filter.

Usage:
    streamlit run agents/dashboard/streamlit_app.py
"""

import json
from pathlib import Path

import streamlit as st

RAW_SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "staging" / "raw_scrape_sample.json"

st.set_page_config(
    page_title="Job Intelligence Engine — Raw Scrape",
    page_icon="🔍",
    layout="wide",
)

st.title("Job Intelligence Engine")
st.subheader("Raw Scraped Job Postings")


def load_records() -> list[dict]:
    if not RAW_SAMPLE_PATH.exists():
        return []
    with RAW_SAMPLE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


records = load_records()

if not records:
    st.warning(
        f"No scraped data found at `{RAW_SAMPLE_PATH}`.\n\n"
        "Run the scraper first:\n```bash\npython -m agents.ingestion.sources.scraper_adapter\n```"
    )
    st.stop()

# --- Sidebar filter ---
all_sources = sorted({r.get("source", "unknown") for r in records})

with st.sidebar:
    st.header("Filters")
    selected_sources = st.multiselect(
        "Source",
        options=all_sources,
        default=all_sources,
        help="Filter postings by scrape source",
    )

filtered = [r for r in records if r.get("source", "unknown") in selected_sources]

st.caption(f"Showing {len(filtered)} of {len(records)} postings")

if not filtered:
    st.info("No postings match the selected filters.")
    st.stop()

# --- Posting cards ---
for i, record in enumerate(filtered, start=1):
    source = record.get("source", "unknown")
    url = record.get("url", "—")
    timestamp = record.get("timestamp", "—")
    raw_text = record.get("raw_text", "")
    preview = raw_text[:300] + ("…" if len(raw_text) > 300 else "")

    with st.expander(f"Posting {i} — {source} | {url}", expanded=False):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"**Source:** `{source}`")
            st.markdown(f"**URL:** {url}")
            st.markdown(f"**Scraped at:** {timestamp}")
        with col2:
            st.markdown("**Raw text preview:**")
            st.text(preview)
