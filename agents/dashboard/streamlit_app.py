"""
Raw Scrape Viewer: load staging JSON and show postings as filterable expander cards.
"""
import json
from pathlib import Path

import streamlit as st

STAGING_JSON = Path(__file__).resolve().parent / ".." / "data" / "staging" / "raw_scrape_sample.json"
PREVIEW_LENGTH = 300


@st.cache_data(ttl=30)
def load_raw_scrape(path: Path) -> list[dict] | None:
    """Load staging JSON; return list of postings or None if file missing."""
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    st.set_page_config(page_title="waifinder · Raw Scrape Viewer", layout="wide")

    data = load_raw_scrape(STAGING_JSON)

    if data is None:
        st.warning(
            "No staging data found. Run the scraper to generate "
            "`agents/data/staging/raw_scrape_sample.json`, e.g.: "
            "`python -m ingestion.sources.scraper_adapter` from the `agents` directory."
        )
        return

    postings: list[dict] = data
    all_sources = sorted({p.get("source") or "unknown" for p in postings})

    with st.sidebar:
        selected_sources = st.multiselect(
            "Source",
            options=all_sources,
            default=all_sources,
            help="Filter postings by source.",
        )
        st.metric("Total postings", len(postings))
        filtered = [p for p in postings if (p.get("source") or "unknown") in selected_sources]
        st.metric("Visible after filter", len(filtered))

    for p in filtered:
        source = p.get("source") or "unknown"
        source_url = p.get("source_url") or ""
        ts = p.get("ingestion_timestamp") or ""
        raw = p.get("raw_text") or ""
        preview = raw[:PREVIEW_LENGTH] + ("…" if len(raw) > PREVIEW_LENGTH else "")

        with st.expander(f"{source} — {source_url[:60]}{'…' if len(source_url) > 60 else ''}"):
            st.text("Source: " + source)
            st.text("Source URL: " + source_url)
            st.text("Ingestion timestamp: " + ts)
            st.divider()
            st.caption("Preview (first 300 chars)")
            st.text(preview)


if __name__ == "__main__":
    main()
