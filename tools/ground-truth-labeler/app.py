"""Ground Truth Labeling Tool — Streamlit App.

Batch workflow: Search 10 jobs → label all sequentially → auto-append to
ground_truth_labeled.json after each record.

Layout: Left pane = forms + labeled items | Right pane = scrollable job text
JSearch results cached to jsearch_cache.json so you can reload without re-calling the API.

Usage:
    cd tools/ground-truth-labeler
    python -m streamlit run app.py
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

# Minimal toolbar avoids Streamlit share-modal.js (addEventListener on missing nodes in some setups).
st.set_option("client.toolbarMode", "minimal")
from jsearch_client import get_api_key, parse_job_sections, search_jobs
from schema import (
    GENAI_SKILLS,
    GroundTruthRecord,
    SkillRecord,
    SpanRecord,
    ToolRecord,
)
from text_selector import render_selectable_job_text, span_input_bridge

load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_FILE = Path(__file__).parent / "ground_truth_labeled.json"
CACHE_FILE = Path(__file__).parent / "jsearch_cache.json"


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------


def load_dataset() -> list[dict]:
    """Load existing dataset from disk, or return empty list."""
    if OUTPUT_FILE.exists():
        try:
            return json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def save_dataset(dataset: list[dict]) -> None:
    """Write the full dataset to disk."""
    OUTPUT_FILE.write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def next_gt_id(dataset: list[dict]) -> str:
    """Generate the next ground_truth_id based on existing records."""
    return f"gt-{len(dataset) + 1:03d}"


def load_cache() -> dict:
    """Load cached JSearch results from disk."""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def save_cache(query: str, jobs: list[dict], job_index: int = 0) -> None:
    """Save JSearch results and current position to disk cache."""
    CACHE_FILE.write_text(
        json.dumps({"query": query, "jobs": jobs, "job_index": job_index}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def clear_cache() -> None:
    """Delete the cache file."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()


# ---------------------------------------------------------------------------
# Job text rendering helper (used in right pane)
# ---------------------------------------------------------------------------

SECTION_COLORS = {
    "title": "rgba(33, 150, 243, 0.15)",
    "description": "rgba(156, 39, 176, 0.15)",
    "requirements": "rgba(76, 175, 80, 0.15)",
    "responsibilities": "rgba(255, 152, 0, 0.15)",
}


def render_job_text(job: dict) -> None:
    """Render color-coded job text sections in a scrollable container."""
    sections = [
        ("title", "Title", job.get("title", "")),
        ("description", "Description", job.get("description", "")),
        ("requirements", "Requirements", job.get("requirements", "")),
        ("responsibilities", "Responsibilities", job.get("responsibilities", "")),
    ]
    for field_source, label, text in sections:
        if text.strip():
            bg = SECTION_COLORS.get(field_source, "#f5f5f5")
            st.markdown(
                f'<div style="background:{bg}; padding:10px; border-radius:6px; '
                f'margin-bottom:6px;">'
                f"<strong>📌 {label}</strong> "
                f'<code style="font-size:0.75em;">field_source="{field_source}"</code>'
                f"<br/><pre style='white-space:pre-wrap; font-size:0.85em; "
                f"max-height:none; color:inherit;'>{text[:4000]}</pre>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

# --- Auto-load from cache BEFORE setting defaults ---
if "phase" not in st.session_state:
    # First run — initialize everything
    _cached = load_cache()
    _cached_jobs = _cached.get("jobs", [])
    _cached_index = _cached.get("job_index", 0)

    st.session_state.phase = "label" if _cached_jobs else "search"
    st.session_state.jobs = _cached_jobs
    st.session_state.job_index = _cached_index
    st.session_state.label_step = "review"
    st.session_state.skills = []
    st.session_state.tools = []
    st.session_state.labeler_notes = {}
elif not st.session_state.get("jobs"):
    # Session exists but jobs are empty — try cache reload
    _cached = load_cache()
    _cached_jobs = _cached.get("jobs", [])
    if _cached_jobs:
        st.session_state.jobs = _cached_jobs
        st.session_state.job_index = _cached.get("job_index", 0)
        st.session_state.phase = "label"
        st.session_state.label_step = "review"


def set_phase(phase: str) -> None:
    st.session_state.phase = phase


def set_label_step(step: str) -> None:
    st.session_state.label_step = step


def reset_labels() -> None:
    st.session_state.skills = []
    st.session_state.tools = []
    st.session_state.labeler_notes = {}
    st.session_state.pop("editing_skill_index", None)
    st.session_state.pop("editing_tool_index", None)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Ground Truth Labeler", page_icon="🏷️", layout="wide")

# CSS: independent scrolling for left (form) and right (job text) columns
st.markdown("""
<style>
/* The horizontal block containing the labeling columns:
   kill flex-grow so height constraint is respected */
[data-testid="stHorizontalBlock"]:has(.gt-section) {
    height: calc(100vh - 260px) !important;
    flex: 0 0 calc(100vh - 260px) !important;
    overflow: hidden !important;
    align-items: stretch !important;
    flex-wrap: nowrap !important;
}
/* Both columns: independent scroll */
[data-testid="stHorizontalBlock"]:has(.gt-section) > [data-testid="stColumn"] {
    overflow-y: auto !important;
    height: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# --- Sidebar: dataset status + labeled items for current job ---
dataset = load_dataset()
with st.sidebar:
    st.header("📊 Dataset")
    st.metric("Records saved", len(dataset))
    st.caption("Target: 20-30 records")
    st.caption(f"File: `{OUTPUT_FILE.name}`")

    # Show labeled skills/tools for current job
    if st.session_state.phase == "label" and st.session_state.label_step in ("skills", "tools", "save"):
        st.divider()
        st.subheader("Current Job Labels")
        if st.session_state.skills:
            st.markdown(f"**Skills ({len(st.session_state.skills)})**")
            for skill in st.session_state.skills:
                badge = " 🤖" if skill.is_genai_extension else ""
                st.markdown(f"- {skill.skill_name}{badge} *({skill.type})*")
        if st.session_state.tools:
            st.markdown(f"**Tools ({len(st.session_state.tools)})**")
            for tool in st.session_state.tools:
                badge = " 🤖" if tool.is_genai_tool else ""
                st.markdown(f"- {tool.tool_name}{badge} *({tool.category})*")

    # Saved records
    if dataset:
        st.divider()
        st.subheader("Saved Records")
        for rec in dataset:
            st.markdown(
                f"**{rec['ground_truth_id']}** — {rec['title'][:25]}  \n"
                f"{len(rec.get('skills', []))}S / {len(rec.get('tools', []))}T"
            )

    st.divider()
    cached = load_cache()
    if cached.get("query"):
        st.caption(f"Cached query: *{cached['query']}*")
    if st.button("🔄 New Search"):
        clear_cache()
        st.session_state.phase = "search"
        st.session_state.jobs = []
        st.session_state.job_index = 0
        reset_labels()
        st.rerun()


# =========================================================================
# PHASE: SEARCH — Load a batch of jobs
# =========================================================================

if st.session_state.phase == "search":
    st.title("🏷️ Ground Truth Labeling Tool")
    st.header("Step 1 — Search & Load Job Batch")

    tab_search, tab_manual = st.tabs(["🔍 JSearch API", "📝 Manual Entry"])

    with tab_search:
        api_key = get_api_key()
        if not api_key:
            st.warning(
                "No `JSEARCH_API_KEY` found in environment. "
                "Set it in your `.env` file or switch to Manual Entry."
            )
        else:
            st.success("JSearch API key detected.")

        query = st.text_input(
            "Search query",
            value="data engineer El Paso TX",
            help="Try: 'software engineer El Paso', 'AI engineer remote', etc.",
        )
        num_results = st.slider("Jobs to load", 1, 10, 10)

        if st.button("🔎 Search & Load All", disabled=not api_key):
            with st.spinner("Searching JSearch..."):
                results = search_jobs(query, num_results)
                if results and "error" not in results[0]:
                    parsed = [parse_job_sections(j) for j in results]
                    # Save to cache (flush old, write new)
                    save_cache(query, parsed)
                    st.session_state.jobs = parsed
                    st.session_state.job_index = 0
                    reset_labels()
                    set_phase("label")
                    set_label_step("review")
                    st.rerun()
                else:
                    st.error(f"Search failed: {results}")

    with tab_manual:
        st.markdown("Paste job posting details manually (no API key needed).")
        with st.form("manual_form"):
            m_title = st.text_input("Job Title")
            m_company = st.text_input("Company")
            col1, col2 = st.columns(2)
            with col1:
                m_city = st.text_input("City", value="El Paso")
            with col2:
                m_state = st.text_input("State", value="TX")
            m_description = st.text_area("Description", height=200)
            m_requirements = st.text_area("Requirements", height=150)
            m_responsibilities = st.text_area("Responsibilities", height=150)
            submitted = st.form_submit_button("Add to batch")
            if submitted and m_title:
                job = {
                    "external_id": f"manual-{uuid.uuid4().hex[:8]}",
                    "title": m_title,
                    "company": m_company,
                    "city": m_city,
                    "state": m_state,
                    "description": m_description,
                    "requirements": m_requirements,
                    "responsibilities": m_responsibilities,
                    "job_url": "",
                    "is_remote": False,
                    "employment_type": "",
                }
                st.session_state.jobs.append(job)
                st.success(f"Added. Batch now has {len(st.session_state.jobs)} job(s).")

        if st.session_state.jobs:
            st.divider()
            st.subheader(f"Batch ({len(st.session_state.jobs)} jobs)")
            for i, j in enumerate(st.session_state.jobs):
                st.markdown(f"{i+1}. **{j['title']}** — {j['company']}")
            if st.button("▶️ Start Labeling Batch"):
                save_cache("manual", st.session_state.jobs)
                st.session_state.job_index = 0
                reset_labels()
                set_phase("label")
                set_label_step("review")
                st.rerun()


# =========================================================================
# PHASE: LABEL — Cycle through each job in the batch
# =========================================================================

elif st.session_state.phase == "label":
    jobs = st.session_state.jobs
    idx = st.session_state.job_index

    if idx >= len(jobs):
        st.title("🏷️ Ground Truth Labeling Tool")
        st.success(f"✅ All {len(jobs)} jobs in this batch have been labeled!")
        st.info(f"Dataset now has **{len(load_dataset())}** total records in `{OUTPUT_FILE.name}`.")
        if st.button("🔍 Search for more jobs"):
            clear_cache()
            set_phase("search")
            st.session_state.jobs = []
            st.session_state.job_index = 0
            st.rerun()
    else:
        job = jobs[idx]

        # --- Progress bar ---
        st.title("🏷️ Ground Truth Labeling Tool")
        prog_col1, prog_col2 = st.columns([3, 1])
        with prog_col1:
            st.progress(idx / len(jobs), text=f"Job {idx + 1} of {len(jobs)}")
        with prog_col2:
            step_labels = {
                "review": "📖 Review",
                "skills": "🎯 Skills",
                "tools": "🔧 Tools",
                "save": "💾 Save",
            }
            st.markdown(f"**{step_labels.get(st.session_state.label_step, '')}**")

        st.markdown(f"### {job['title']} — {job['company']}")
        st.caption(f"{job.get('city', '')}, {job.get('state', '')} | ID: {job['external_id']}")
        st.divider()

        # =================================================================
        # LABEL STEP: Review (full width — read through before labeling)
        # =================================================================

        if st.session_state.label_step == "review":
            col1, col2, _ = st.columns([1, 1, 8])
            with col1:
                if st.button("⏭️ Skip this job"):
                    st.session_state.job_index += 1
                    cached = load_cache()
                    if cached.get("jobs"):
                        save_cache(cached.get("query", ""), cached["jobs"], st.session_state.job_index)
                    reset_labels()
                    set_label_step("review")
                    st.rerun()
            with col2:
                if st.button("Label Job Post →"):
                    reset_labels()
                    set_label_step("skills")
                    st.rerun()
            st.divider()
            render_job_text(job)

        # =================================================================
        # LABEL STEP: Skills — left pane form, right pane job text
        # =================================================================

        elif st.session_state.label_step == "skills":
            # Tab-like navigation
            nav1, nav2, nav3, nav4, _ = st.columns([1, 1, 1, 1, 6])
            with nav1:
                if st.button("← Review", key="nav_review_from_skills"):
                    set_label_step("review")
                    st.rerun()
            with nav2:
                st.button("🎯 Skills", key="nav_skills_active", disabled=True)
            with nav3:
                if st.button("🔧 Tools", key="nav_tools_from_skills"):
                    set_label_step("tools")
                    st.rerun()
            with nav4:
                if st.button("💾 Save →", key="nav_save_from_skills"):
                    set_label_step("save")
                    st.rerun()

            left, right = st.columns([1, 1])

            with right:
                st.markdown("#### 📄 Job Text")
                st.caption("💡 Highlight text to capture source_span automatically")
                render_selectable_job_text(job, bridge_key="skill_span_bridge")
                span_result = span_input_bridge(key="skill_span_bridge")
                if span_result:
                    st.session_state.span_selection = span_result
                with st.expander("ℹ️ GenAI Extension Skills (10-skill list)"):
                    for s in GENAI_SKILLS:
                        st.markdown(f"- {s}")

            with left:
                # --- Get span selection (if any) ---
                span_sel = st.session_state.get("span_selection")

                # --- Determine if editing ---
                editing_idx = st.session_state.get("editing_skill_index")
                editing_skill = st.session_state.skills[editing_idx] if editing_idx is not None else None

                if editing_skill:
                    st.markdown(f"#### ✏️ Edit Skill: {editing_skill.skill_name}")
                else:
                    st.markdown("#### 🎯 Add Skill")

                # --- Source Span section (from selection or editing) ---
                st.markdown("##### 📌 Source Span")
                if editing_skill:
                    sp = editing_skill.source_span
                    span_text = sp.text
                    span_field = sp.field_source
                    span_start = sp.start_char
                    span_end = sp.end_char
                    st.success(
                        f"**field_source:** `{span_field}` | "
                        f"**start_char:** {span_start} | **end_char:** {span_end}  \n"
                        f"**text:** *\"{span_text[:80]}{'...' if len(span_text) > 80 else ''}\"*"
                    )
                elif span_sel:
                    span_text = span_sel["text"]
                    span_field = span_sel["field_source"]
                    span_start = span_sel["start_char"]
                    span_end = span_sel["end_char"]
                    st.success(
                        f"**field_source:** `{span_field}` | "
                        f"**start_char:** {span_start} | **end_char:** {span_end}  \n"
                        f"**text:** *\"{span_text[:80]}{'...' if len(span_text) > 80 else ''}\"*"
                    )
                else:
                    span_text = None
                    span_field = None
                    span_start = None
                    span_end = None
                    st.warning("No span selected — drag text in the right pane to set source_span.")

                # Determine default skill_name from editing
                default_name = editing_skill.skill_name if editing_skill else ""

                with st.form("skill_form", clear_on_submit=True):
                    s_label = st.text_input(
                        "Skill name",
                        value=default_name,
                        help="e.g. Python, Prompt Engineering. The human-judged skill label.",
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        s_type = st.selectbox(
                            "Type",
                            ["Technical", "Domain", "Soft", "Certification", "Tool"],
                            index=["Technical", "Domain", "Soft", "Certification", "Tool"].index(editing_skill.type) if editing_skill else 0,
                        )
                        s_required = st.checkbox("Required?", value=editing_skill.required_flag if editing_skill and editing_skill.required_flag is not None else True)
                    with c2:
                        s_genai = st.checkbox("GenAI Extension skill?", value=editing_skill.is_genai_extension if editing_skill else False)
                    s_esco = st.text_input("ESCO URI (optional)", value=editing_skill.esco_uri or "" if editing_skill else "")
                    s_note = st.text_input(
                        "Labeler note (optional)",
                        value=st.session_state.labeler_notes.get(editing_skill.skill_name, "") if editing_skill else "",
                    )
                    s_confidence = st.slider("Confidence", 0.0, 1.0, editing_skill.confidence if editing_skill else 1.0, 0.05)

                    btn_label = "💾 Save Skill" if editing_skill else "➕ Add Skill"
                    submitted = st.form_submit_button(btn_label)
                    if submitted:
                        if not s_label.strip():
                            st.error("Skill name is required.")
                        elif span_field is None:
                            st.error("Source span is required — drag to select text in the right pane first.")
                        else:
                            skill_name = s_label.strip()
                            skill = SkillRecord(
                                skill_name=skill_name,
                                type=s_type,
                                confidence=s_confidence,
                                required_flag=s_required,
                                esco_uri=s_esco.strip() or None,
                                is_genai_extension=s_genai,
                                source_span=SpanRecord(
                                    text=span_text,
                                    field_source=span_field,
                                    start_char=span_start,
                                    end_char=span_end,
                                ),
                            )
                            if editing_idx is not None:
                                st.session_state.skills[editing_idx] = skill
                                st.session_state.pop("editing_skill_index", None)
                            else:
                                st.session_state.skills.append(skill)
                            if s_note.strip():
                                st.session_state.labeler_notes[skill_name] = s_note.strip()
                            # Clear span selection after use
                            st.session_state.pop("span_selection", None)
                            st.rerun()

                # Cancel edit button
                if editing_idx is not None:
                    if st.button("Cancel edit"):
                        st.session_state.pop("editing_skill_index", None)
                        st.rerun()

                # Show current skills
                if st.session_state.skills:
                    st.markdown(f"**Skills added ({len(st.session_state.skills)})**")
                    for i, skill in enumerate(st.session_state.skills):
                        sc1, sc2, sc3 = st.columns([4, 1, 1])
                        with sc1:
                            badge = " 🤖" if skill.is_genai_extension else ""
                            sp = skill.source_span
                            st.markdown(
                                f"- **{skill.skill_name}**{badge} — {skill.type} "
                                f"(`{sp.field_source}` [{sp.start_char}:{sp.end_char}])"
                            )
                        with sc2:
                            if st.button("✏️", key=f"es_{i}"):
                                st.session_state.editing_skill_index = i
                                st.rerun()
                        with sc3:
                            if st.button("🗑️", key=f"ds_{i}"):
                                st.session_state.skills.pop(i)
                                st.session_state.pop("editing_skill_index", None)
                                st.rerun()

        # =================================================================
        # LABEL STEP: Tools — left pane form, right pane job text
        # =================================================================

        elif st.session_state.label_step == "tools":
            # Tab-like navigation
            nav1, nav2, nav3, nav4, _ = st.columns([1, 1, 1, 1, 6])
            with nav1:
                if st.button("← Review", key="nav_review_from_tools"):
                    set_label_step("review")
                    st.rerun()
            with nav2:
                if st.button("🎯 Skills", key="nav_skills_from_tools"):
                    set_label_step("skills")
                    st.rerun()
            with nav3:
                st.button("🔧 Tools", key="nav_tools_active", disabled=True)
            with nav4:
                if st.button("💾 Save →", key="nav_save_from_tools"):
                    set_label_step("save")
                    st.rerun()

            left, right = st.columns([1, 1])

            with right:
                st.markdown("#### 📄 Job Text")
                st.caption("💡 Highlight text to capture source_span automatically")
                render_selectable_job_text(job, bridge_key="tool_span_bridge")
                span_result = span_input_bridge(key="tool_span_bridge")
                if span_result:
                    st.session_state.span_selection = span_result

            with left:
                # --- Get span selection (if any) ---
                span_sel = st.session_state.get("span_selection")

                # --- Determine if editing ---
                editing_tidx = st.session_state.get("editing_tool_index")
                editing_tool = st.session_state.tools[editing_tidx] if editing_tidx is not None else None
                cat_options = ["language", "framework", "platform", "database", "devops", "ai_tool", "other"]

                if editing_tool:
                    st.markdown(f"#### ✏️ Edit Tool: {editing_tool.tool_name}")
                else:
                    st.markdown("#### 🔧 Add Tool")

                # --- Source Span section (from selection or editing) ---
                st.markdown("##### 📌 Source Span")
                if editing_tool:
                    sp = editing_tool.source_span
                    span_text = sp.text
                    span_field = sp.field_source
                    span_start = sp.start_char
                    span_end = sp.end_char
                    st.success(
                        f"**field_source:** `{span_field}` | "
                        f"**start_char:** {span_start} | **end_char:** {span_end}  \n"
                        f"**text:** *\"{span_text[:80]}{'...' if len(span_text) > 80 else ''}\"*"
                    )
                elif span_sel:
                    span_text = span_sel["text"]
                    span_field = span_sel["field_source"]
                    span_start = span_sel["start_char"]
                    span_end = span_sel["end_char"]
                    st.success(
                        f"**field_source:** `{span_field}` | "
                        f"**start_char:** {span_start} | **end_char:** {span_end}  \n"
                        f"**text:** *\"{span_text[:80]}{'...' if len(span_text) > 80 else ''}\"*"
                    )
                else:
                    span_text = None
                    span_field = None
                    span_start = None
                    span_end = None
                    st.warning("No span selected — drag text in the right pane to set source_span.")

                # Determine default name from span selection or editing
                default_name = editing_tool.tool_name if editing_tool else ""

                with st.form("tool_form", clear_on_submit=True):
                    t_name = st.text_input(
                        "Tool name",
                        value=default_name,
                        help="e.g. Apache Spark, Docker, Pinecone. Drag text on the right to auto-fill.",
                    )
                    t_category = st.selectbox(
                        "Category",
                        cat_options,
                        index=cat_options.index(editing_tool.category) if editing_tool else None,
                        placeholder="Select category...",
                    )
                    t_genai = st.checkbox("GenAI tool?", value=editing_tool.is_genai_tool if editing_tool else False, help="Pinecone, LangChain, OpenAI API, etc.")
                    t_note = st.text_input(
                        "Labeler note (optional)",
                        value=st.session_state.labeler_notes.get(editing_tool.tool_name, "") if editing_tool else "",
                    )
                    t_confidence = st.slider("Confidence", 0.0, 1.0, editing_tool.confidence if editing_tool else 1.0, 0.05)

                    btn_label = "💾 Save Tool" if editing_tool else "➕ Add Tool"
                    submitted = st.form_submit_button(btn_label)
                    if submitted:
                        if not t_name.strip():
                            st.error("Tool name is required.")
                        elif span_field is None:
                            st.error("Source span is required — drag to select text in the right pane first.")
                        elif t_category is None:
                            st.error("Category is required.")
                        else:
                            name = t_name.strip()
                            tool = ToolRecord(
                                tool_name=name,
                                category=t_category,
                                confidence=t_confidence,
                                is_genai_tool=t_genai,
                                source_span=SpanRecord(
                                    text=span_text,
                                    field_source=span_field,
                                    start_char=span_start,
                                    end_char=span_end,
                                ),
                            )
                            if editing_tidx is not None:
                                st.session_state.tools[editing_tidx] = tool
                                st.session_state.pop("editing_tool_index", None)
                            else:
                                st.session_state.tools.append(tool)
                            if t_note.strip():
                                st.session_state.labeler_notes[name] = t_note.strip()
                            # Clear span selection after use
                            st.session_state.pop("span_selection", None)
                            st.rerun()

                # Cancel edit button
                if editing_tidx is not None:
                    if st.button("Cancel edit", key="cancel_tool_edit"):
                        st.session_state.pop("editing_tool_index", None)
                        st.rerun()

                # Show current tools
                if st.session_state.tools:
                    st.markdown(f"**Tools added ({len(st.session_state.tools)})**")
                    for i, tool in enumerate(st.session_state.tools):
                        tc1, tc2, tc3 = st.columns([4, 1, 1])
                        with tc1:
                            badge = " 🤖" if tool.is_genai_tool else ""
                            sp = tool.source_span
                            st.markdown(
                                f"- **{tool.tool_name}**{badge} — {tool.category} "
                                f"(`{sp.field_source}` [{sp.start_char}:{sp.end_char}])"
                            )
                        with tc2:
                            if st.button("✏️", key=f"et_{i}"):
                                st.session_state.editing_tool_index = i
                                st.rerun()
                        with tc3:
                            if st.button("🗑️", key=f"dt_{i}"):
                                st.session_state.tools.pop(i)
                                st.session_state.pop("editing_tool_index", None)
                                st.rerun()

        # =================================================================
        # LABEL STEP: Save
        # =================================================================

        elif st.session_state.label_step == "save":
            dataset = load_dataset()
            gt_id = next_gt_id(dataset)

            record = GroundTruthRecord(
                ground_truth_id=gt_id,
                external_id=job.get("external_id", ""),
                title=job["title"],
                company=job["company"],
                city=job.get("city"),
                state=job.get("state"),
                description=job.get("description", ""),
                requirements=job.get("requirements", ""),
                responsibilities=job.get("responsibilities", ""),
                skills=st.session_state.skills,
                tools=st.session_state.tools,
                labeler_notes=st.session_state.labeler_notes,
            )

            record_dict = record.model_dump()

            # Validation
            try:
                GroundTruthRecord.model_validate(record_dict)
                st.success("✅ Pydantic validation passed")
            except Exception as exc:
                st.error(f"❌ Validation failed: {exc}")

            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Skills", len(record.skills))
            with col2:
                st.metric("Tools", len(record.tools))
            with col3:
                st.metric("Dataset after save", len(dataset) + 1)

            # JSON preview
            with st.expander("JSON Preview", expanded=True):
                st.json(record_dict)

            st.divider()
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("← Back to Tools"):
                    set_label_step("tools")
                    st.rerun()

            with col2:
                if st.button("⏭️ Skip (don't save)"):
                    st.session_state.job_index += 1
                    reset_labels()
                    set_label_step("review")
                    st.rerun()

            with col3:
                if st.button("💾 Save & Next Job", type="primary"):
                    dataset.append(record_dict)
                    save_dataset(dataset)
                    st.session_state.job_index += 1
                    # Persist position to cache so refresh resumes here
                    cached = load_cache()
                    if cached.get("jobs"):
                        save_cache(cached.get("query", ""), cached["jobs"], st.session_state.job_index)
                    reset_labels()
                    set_label_step("review")
                    st.rerun()
