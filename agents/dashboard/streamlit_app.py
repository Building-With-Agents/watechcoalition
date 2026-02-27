"""
Job Scrape Dashboard — Week 1 scope.
Loads postings from agents/data/staging/raw_scrape_sample.json and displays with sidebar filter.
"""
import json
from pathlib import Path

import streamlit as st

# Path to staging JSON (agents/data/staging/raw_scrape_sample.json)
STAGING_FILE = Path(__file__).resolve().parent.parent / "data" / "staging" / "raw_scrape_sample.json"
RAW_TEXT_PREVIEW_LEN = 650  # characters (within 500–800)


def load_postings(file_path: Path) -> list[dict]:
    """Load list of postings from JSON file. Returns empty list on missing/empty/invalid file."""
    if not file_path.exists():
        return []
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    # Keep only items that have the expected keys (source, scraped_url, timestamp, raw_text)
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "source" in item and "scraped_url" in item and "timestamp" in item and "raw_text" in item:
            out.append(item)
    return out


def short_url(url: str, max_len: int = 60) -> str:
    """Return a short display version of the URL (truncate with ellipsis if needed)."""
    if not url or len(url) <= max_len:
        return url or ""
    return url[: max_len - 3].rstrip("/") + "..."


def main() -> None:
    st.set_page_config(page_title="Job Scrape Dashboard", layout="wide")
    st.title("Job Scrape Dashboard")

    postings = load_postings(STAGING_FILE)

    if not postings:
        st.error(f"Could not load job postings. Check that the file exists and is valid JSON: `{STAGING_FILE}`")
        st.info("Run the scraper first: `python -m agents.ingestion.sources.scraper_adapter`")
        return

    # Unique source names for sidebar filter (sorted)
    sources = sorted({p.get("source") or "unknown" for p in postings})

    with st.sidebar:
        st.subheader("Filter by source")
        selected_sources = st.multiselect(
            "Source(s)",
            options=sources,
            default=[],
            help="Leave empty to show all postings.",
        )

    # Filter dataset: no selection => all; otherwise only selected sources
    if selected_sources:
        filtered = [p for p in postings if (p.get("source") or "unknown") in selected_sources]
    else:
        filtered = postings

    st.caption(f"Showing {len(filtered)} of {len(postings)} postings.")

    for p in filtered:
        source = p.get("source") or "unknown"
        url = p.get("scraped_url") or ""
        ts = p.get("timestamp") or ""
        raw = p.get("raw_text") or ""
    

        expander_title = f"{source} — {short_url(url)}"
        with st.expander(expander_title):
            st.write("**Source:**", source)
            st.write("**Scraped URL:**")
            if url:
                st.markdown(f"[{url}]({url})")
            else:
                st.write("—")
            st.write("**Timestamp:**", ts if ts else "—")
            st.write("**Raw text preview:**")
            st.text(raw if raw else "(empty)")


if __name__ == "__main__":
    main()
