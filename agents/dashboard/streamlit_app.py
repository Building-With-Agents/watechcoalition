# agents/dashboard/streamlit_app.py
"""Streamlit dashboard — Phase 1. Run: streamlit run agents/dashboard/streamlit_app.py"""

import json
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

# Default path from Exercise 1.2 (scraper_adapter writes to agents/data/staging/raw_scrape_sample.json)
def _default_raw_scrape_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "staging" / "raw_scrape_sample.json"


def _load_raw_scrape(path: Path) -> list[dict] | None:
    """Load list of raw job postings from JSON. Returns None on missing file or invalid JSON."""
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return None
    if not isinstance(data, list):
        return None
    return data


def _source_identifier(record: dict) -> str:
    """Derive a short source name from the record (e.g. hostname from source_url)."""
    url = record.get("source_url") or record.get("url") or ""
    if not url:
        return "Unknown"
    parsed = urlparse(url)
    netloc = (parsed.netloc or "").strip()
    if netloc:
        return netloc
    return url[:50] + ("..." if len(url) > 50 else "")


def _raw_text_preview(record: dict, max_chars: int = 280) -> str:
    """First ~200–300 chars of description or title+description for preview."""
    desc = record.get("description") or ""
    if desc:
        text = desc.strip()
    else:
        text = (record.get("title") or "").strip()
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def _timestamp_str(record: dict) -> str | None:
    """Return a timestamp string if present (e.g. date_posted or scraped_at)."""
    for key in ("scraped_at", "ingestion_timestamp", "date_posted", "timestamp"):
        val = record.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


st.set_page_config(page_title="Job Intelligence Engine", layout="wide")
st.title("Job Intelligence Engine — Dashboard")
st.caption(
    "Phase 1. Raw Scrape Viewer (Exercise 1.2) | "
    "Pages: Ingestion Overview | Normalization Quality | Skill Taxonomy | Weekly Insights | Ask the Data | Operations & Alerts."
)

# --- Raw Scrape Viewer ---
st.subheader("Raw Scrape Viewer")

default_path = _default_raw_scrape_path()
custom_path_str = st.sidebar.text_input(
    "JSON path (optional)",
    value="",
    help=f"Leave empty to use default: {default_path}",
)
data_path = Path(custom_path_str.strip()) if custom_path_str.strip() else default_path

postings = _load_raw_scrape(data_path)

if postings is None:
    if not data_path.exists():
        st.warning(f"File not found: `{data_path}`. Run the scraper (e.g. `python -m agents.ingestion.sources.scraper_adapter`) to generate it.")
    else:
        st.error(f"Could not load valid JSON from `{data_path}` (expected a list of job objects).")
    st.stop()

# Unique sources (hostnames) for sidebar filter
sources = sorted({_source_identifier(r) for r in postings})

st.sidebar.markdown("**Filter by source**")
show_all = st.sidebar.checkbox("All sources", value=True, key="show_all_sources")
if show_all:
    selected_sources = sources
else:
    selected_sources = st.sidebar.multiselect(
        "Sources",
        options=sources,
        default=sources[:1] if sources else [],
        key="source_filter",
    )

filtered = [p for p in postings if _source_identifier(p) in selected_sources]

st.sidebar.caption(f"Showing {len(filtered)} of {len(postings)} postings")

PREVIEW_CHARS = 280

for i, record in enumerate(filtered):
    source = _source_identifier(record)
    url_scraped = record.get("source_url") or record.get("url") or ""
    timestamp = _timestamp_str(record)
    preview = _raw_text_preview(record, max_chars=PREVIEW_CHARS)

    title_display = (record.get("title") or "Untitled").strip() or "Untitled"
    label = f"**{title_display[:60]}{'…' if len(title_display) > 60 else ''}** — {source}"

    with st.expander(label, expanded=False):
        st.markdown(f"**Source:** `{source}`")
        if url_scraped:
            st.markdown(f"**URL scraped:** [{url_scraped}]({url_scraped})")
        if timestamp:
            st.markdown(f"**Timestamp:** {timestamp}")
        st.markdown("**Raw text preview:**")
        st.text(preview if preview else "(no description or title)")
        st.markdown("---")
        st.markdown("**Full raw text:**")
        full_text = (record.get("description") or "").strip() or (record.get("title") or "").strip()
        st.text(full_text if full_text else "(empty)")
        # Optional: show full record as JSON
        with st.expander("View full record (JSON)", expanded=False):
            st.json(record)
