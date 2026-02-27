"""
Streamlit dashboard: view scraped job postings from raw_scrape_sample.json.
Loads JSON from agents/data/staging/raw_scrape_sample.json. No print; no logging of content.
"""
import json
from pathlib import Path

import streamlit as st

# Path relative to repo: agents/dashboard/streamlit_app.py -> agents/data/staging/raw_scrape_sample.json
_agents_root = Path(__file__).resolve().parent.parent
RAW_SCRAPE_PATH = _agents_root / "data" / "staging" / "raw_scrape_sample.json"

RAW_TEXT_PREVIEW_LEN = 800


def _load_data():
    """Load and parse JSON. Returns (data dict, None) on success or (None, error_message)."""
    if not RAW_SCRAPE_PATH.exists():
        return None, f"File not found: {RAW_SCRAPE_PATH}"
    try:
        with open(RAW_SCRAPE_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"
    if not isinstance(data, dict):
        return None, "Expected a JSON object at root"
    postings = data.get("postings")
    if postings is not None and not isinstance(postings, list):
        return None, "Expected 'postings' to be a list"
    return data, None


def main() -> None:
    st.set_page_config(page_title="Scraped Job Postings", layout="wide")
    st.title("Scraped Job Postings")

    data, err = _load_data()
    if err is not None:
        st.error(err)
        st.stop()

    postings = data.get("postings") or []
    target_url = data.get("target_url") or ""
    scraped_at = data.get("scraped_at") or ""

    st.subheader("Dataset metadata")
    st.write("**Target URL:**", target_url if target_url else "—")
    st.write("**Scraped at:**", scraped_at if scraped_at else "—")
    st.divider()

    # Sidebar filters
    sources = sorted({(p.get("source") or "").strip() for p in postings if (p.get("source") or "").strip()})
    all_options = ["All"] + sources
    selected_sources = st.sidebar.multiselect(
        "Filter by source",
        options=all_options,
        default=["All"],
        key="source_filter",
    )
    search_query = (st.sidebar.text_input("Search in raw_text or URL", key="search_query") or "").strip().lower()
    show_full_raw = st.sidebar.checkbox("Show full raw_text", value=False, key="show_full_raw")

    # Apply source filter: "All" or empty -> show everything; else show only selected sources
    if not selected_sources or "All" in selected_sources:
        source_filtered = postings
    else:
        selected_set = set(selected_sources)
        source_filtered = [p for p in postings if (p.get("source") or "").strip() in selected_set]

    # Apply search filter
    if search_query:
        filtered = [
            p for p in source_filtered
            if search_query in ((p.get("raw_text") or "") + " " + (p.get("url") or "")).lower()
        ]
    else:
        filtered = source_filtered

    for i, p in enumerate(filtered):
        url = (p.get("url") or "").strip()
        source = (p.get("source") or "").strip()
        p_scraped_at = (p.get("scraped_at") or "").strip()
        header = f"{source} · {p_scraped_at}" + (f" · {url[:50]}…" if len(url) > 50 else f" · {url}" if url else "")

        with st.expander(header, expanded=(i == 0)):
            if url:
                st.markdown(f"**URL:** [{url}]({url})")
            st.write("**Listing URL:**", (p.get("listing_url") or "—"))
            raw_text = p.get("raw_text") or ""
            if show_full_raw or len(raw_text) <= RAW_TEXT_PREVIEW_LEN:
                display_text = raw_text
            else:
                display_text = raw_text[:RAW_TEXT_PREVIEW_LEN] + "…"
            st.code(display_text, language="text")

    if not filtered:
        st.info("No postings match the current filters.")


if __name__ == "__main__":
    main()
