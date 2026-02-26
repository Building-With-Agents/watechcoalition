"""
Streamlit dashboard to display job postings scraped by Crawl4AI.

Features:
- Loads JSON from the raw scrape sample
- Shows each posting in an expandable card with source, URL, timestamp, and raw text
- Sidebar filter allows filtering by source
"""

import json
from pathlib import Path

import streamlit as st

# ---- Config ----
repo_root = Path(__file__).resolve().parents[2]
json_path = repo_root / "agents" / "data" / "staging" / "raw_scrape_sample.json"
# ---- Load Data ----
if not json_path.exists():
    st.error(f"Scrape sample JSON not found at {json_path}")
    st.stop()

with open(json_path, "r", encoding="utf-8") as f:
    records = json.load(f)

# ---- Sidebar Filter ----
st.sidebar.title("Filters")
sources = sorted({r["source"] for r in records})
selected_source = st.sidebar.selectbox("Select source", ["All"] + sources)

if selected_source != "All":
    filtered_records = [r for r in records if r["source"] == selected_source]
else:
    filtered_records = records

# ---- Dashboard ----
st.title("Job Scrape Dashboard")
st.write(f"Showing {len(filtered_records)} posting(s) out of {len(records)} total")

for record in filtered_records:
    # Truncate raw_text for preview in expander title
    preview = record["raw_text"][:50].replace("\n", " ") + ("..." if len(record["raw_text"]) > 50 else "")
    with st.expander(f"{record['source']} — {preview}"):
        st.markdown(f"**URL:** {record['url']}")
        st.markdown(f"**Timestamp:** {record['timestamp']}")
        st.markdown("---")
        st.write(record["raw_text"])
