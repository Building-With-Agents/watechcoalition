"""
Streamlit dashboard for scraped job data (Exercise 1.3).
Loads JSON from the scraper output (Exercise 1.2), displays each posting in an
expandable card (full content, no truncation), and provides a sidebar filter by source.
Run from repo root: streamlit run agents/dashboard/streamlit_app.py
"""
import json
from datetime import datetime
from pathlib import Path
import streamlit as st

# Path resolution: same layout as scraper (agents/data/staging/)
_THIS_FILE = Path(__file__).resolve()
_AGENTS_ROOT = _THIS_FILE.parents[1]  # agents/
_STAGING_DIR = _AGENTS_ROOT / "data" / "staging"
_JSON_PATH = _STAGING_DIR / "raw_scrape_sample.json"

# Extra sidebar option with no postings, so you can test that the list depopulates
TEST_SOURCE_NO_DATA = "jsearch"


def _load_postings() -> list[dict]:
    """Load postings from raw_scrape_sample.json. Return [] on missing or invalid file."""
    if not _JSON_PATH.exists():
        return []
    try:
        with open(_JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return data


def _safe_get(record: dict, key: str, default: str = "") -> str:
    """Return record[key] or default; coerce to str for display."""
    val = record.get(key, default)
    if val is None:
        return default
    return str(val)


def _source_for_filter(record: dict) -> str:
    """Normalized source value for sidebar options and filter (empty/missing → 'Unknown')."""
    return _safe_get(record, "source", "").strip() or "Unknown"


def _format_timestamp_display(iso_timestamp: str) -> str:
    """Format ISO timestamp for human-readable display (e.g. Feb 27, 2026 at 3:45 PM UTC)."""
    if not iso_timestamp or iso_timestamp == "—":
        return "—"
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y at %I:%M %p UTC").replace(" 0", " ")
    except (ValueError, TypeError):
        return iso_timestamp


st.set_page_config(page_title="Scraped job postings", layout="wide")
st.title("Scraped job postings")

postings = _load_postings()

if not postings:
    st.info("No data. Run the scraper first (Exercise 1.2) to generate raw_scrape_sample.json.")
    st.stop()

# Sidebar: filter by source (same normalization for options and filter so "Unknown" works)
# Include TEST_SOURCE_NO_DATA so you can select a source with no postings and verify the list depopulates
sources = sorted({_source_for_filter(p) for p in postings})
source_options = ["All"] + sources + [TEST_SOURCE_NO_DATA]
selected_source = st.sidebar.selectbox(
    "Filter by source",
    options=source_options,
    index=0,
)

# Filter postings by selected source; display updates when selection changes
if selected_source == "All":
    filtered = postings
else:
    filtered = [p for p in postings if _source_for_filter(p) == selected_source]

st.caption(f"Showing {len(filtered)} of {len(postings)} posting(s)")

if not filtered:
    st.warning("No postings for the selected source: **" + TEST_SOURCE_NO_DATA + "**. Try another source.")
else:
    for i, record in enumerate(filtered, start=1):
        source = _source_for_filter(record)
        url = _safe_get(record, "url", "—")
        timestamp_raw = _safe_get(record, "timestamp", "—")
        timestamp_display = _format_timestamp_display(timestamp_raw)
        raw_text = _safe_get(record, "raw_text", "")

        # Expandable card label: URL host or "Posting N"
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            label = parsed.netloc or (url[:50] + "…" if len(url) > 50 else url) if url else f"Posting {i}"
        except Exception:
            label = f"Posting {i}"

        with st.expander(f"{label} — {source}", expanded=False):
            st.markdown("**Source**  \n" + source)
            if url and url != "—":
                st.markdown("**URL**  \n" + f"[{url}]({url})")
            else:
                st.markdown("**URL**  \n—")
            st.markdown("**Scraped**  \n" + timestamp_display)
            st.markdown("---")
            st.markdown("**Content**")
            if raw_text:
                # Full content in a scrollable container; preserve line breaks
                st.text_area(
                    "Raw text",
                    value=raw_text,
                    height=min(400, max(120, 50 + raw_text.count("\n") * 18)),
                    key=f"raw_text_{i}",
                    disabled=True,
                    label_visibility="collapsed",
                )
            else:
                st.caption("(no text)")
