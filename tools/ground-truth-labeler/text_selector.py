"""Text selection component for ground truth labeling.

Uses a hidden Streamlit text_input as the JS→Python bridge.
On mouseup, JS writes selection JSON to the hidden input and triggers
its change event → Streamlit reruns → Python reads the value.

This is the proven pattern for Streamlit JS↔Python communication.
"""

from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

SECTION_COLORS = {
    "title": "rgba(33, 150, 243, 0.15)",
    "description": "rgba(156, 39, 176, 0.15)",
    "requirements": "rgba(76, 175, 80, 0.15)",
    "responsibilities": "rgba(255, 152, 0, 0.15)",
}

SECTION_BORDER_COLORS = {
    "title": "rgba(33, 150, 243, 0.5)",
    "description": "rgba(156, 39, 176, 0.5)",
    "requirements": "rgba(76, 175, 80, 0.5)",
    "responsibilities": "rgba(255, 152, 0, 0.5)",
}


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def span_input_bridge(key: str = "span_bridge") -> dict | None:
    """Hidden text_input that receives span data from JS.

    Renders a text_input hidden via CSS. The mouseup JS listener writes
    to this input and triggers a change event → Streamlit rerun.

    Returns span dict or None.
    """
    # Hidden text input — the JS bridge target
    raw = st.text_input(
        "span_data",
        value="",
        key=key,
        label_visibility="collapsed",
    )

    # Hide it with CSS
    st.markdown(
        """<style>
        div[data-testid="stTextInput"]:has(input[aria-label="span_data"]) {
            position: absolute;
            top: -9999px;
            opacity: 0;
            height: 0;
            overflow: hidden;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    if raw and raw.strip():
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "field_source" in data:
                return data
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def render_selectable_job_text(job: dict, bridge_key: str = "span_bridge") -> None:
    """Render color-coded job text with mouseup → hidden input bridge."""
    sections = [
        ("title", "Title", job.get("title", "")),
        ("description", "Description", job.get("description", "")),
        ("requirements", "Requirements", job.get("requirements", "")),
        ("responsibilities", "Responsibilities", job.get("responsibilities", "")),
    ]

    all_html = ""
    for field_source, label, text in sections:
        if not text.strip():
            continue
        bg = SECTION_COLORS.get(field_source, "rgba(128,128,128,0.1)")
        border = SECTION_BORDER_COLORS.get(field_source, "rgba(128,128,128,0.3)")
        escaped = _escape_html(text[:4000])
        all_html += (
            f'<div class="gt-section" data-field="{field_source}" '
            f'style="background:{bg}; border-left:3px solid {border}; '
            f'padding:10px; border-radius:6px; margin-bottom:8px;">'
            f'<div style="margin-bottom:4px;">'
            f'<strong>&#x1F4CC; {label}</strong> '
            f'<code style="font-size:0.7em; opacity:0.7;">{field_source}</code>'
            f'</div>'
            f'<div class="gt-section-text" data-field="{field_source}" '
            f'style="white-space:pre-wrap; font-size:0.85em; line-height:1.5; '
            f'cursor:text; user-select:text;">'
            f'{escaped}</div></div>'
        )

    st.markdown(all_html, unsafe_allow_html=True)

    # Inject mouseup listener that writes to the hidden Streamlit text_input
    components.html("""
    <script>
    (function() {
        var parentDoc = window.parent.document;

        // Remove previous listener if any, then install fresh
        if (parentDoc._gtSelHandler) {
            parentDoc.removeEventListener("mouseup", parentDoc._gtSelHandler);
        }

        parentDoc._gtSelHandler = function() {
            var sel = parentDoc.getSelection();
            if (!sel || sel.isCollapsed || !sel.toString().trim()) return;

            var selectedText = sel.toString().trim();

            var node = sel.anchorNode;
            var sectionEl = null;
            while (node && node !== parentDoc.body) {
                if (node.nodeType === 1 && node.classList &&
                    node.classList.contains("gt-section-text")) {
                    sectionEl = node;
                    break;
                }
                node = node.parentNode;
            }
            if (!sectionEl) return;

            var fieldSource = sectionEl.getAttribute("data-field");
            var range = sel.getRangeAt(0);
            var preRange = parentDoc.createRange();
            preRange.setStart(sectionEl, 0);
            preRange.setEnd(range.startContainer, range.startOffset);
            var startChar = preRange.toString().length;
            var endChar = startChar + selectedText.length;

            var data = JSON.stringify({
                text: selectedText,
                field_source: fieldSource,
                start_char: startChar,
                end_char: endChar
            });

            // Save scroll positions of both columns before triggering rerun
            var hBlock = sectionEl.closest('[data-testid="stHorizontalBlock"]');
            if (hBlock) {
                var cols = hBlock.querySelectorAll(':scope > [data-testid="stColumn"]');
                cols.forEach(function(col, i) {
                    sessionStorage.setItem('gt_col_scroll_' + i, col.scrollTop);
                });
            }

            // Find the hidden Streamlit text_input, set value, press Enter to trigger rerun
            function setSpanInput(data, retries) {
                var input = parentDoc.querySelector('input[aria-label="span_data"]');
                if (input) {
                    input.focus();
                    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.parent.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeInputValueSetter.call(input, data);
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                    input.dispatchEvent(new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                } else if (retries > 0) {
                    setTimeout(function() { setSpanInput(data, retries - 1); }, 200);
                }
            }
            setSpanInput(data, 5);
        };
        parentDoc.addEventListener("mouseup", parentDoc._gtSelHandler);

        // Persistent scroll restorer: watches for .gt-section to appear after rerun
        if (!parentDoc._gtScrollObserver) {
            parentDoc._gtScrollObserver = new MutationObserver(function() {
                var s0 = sessionStorage.getItem('gt_col_scroll_0');
                var s1 = sessionStorage.getItem('gt_col_scroll_1');
                if (!s0 && !s1) return;

                var section = parentDoc.querySelector('.gt-section');
                if (!section) return;

                var hBlock = section.closest('[data-testid="stHorizontalBlock"]');
                if (!hBlock) return;

                var cols = hBlock.querySelectorAll(':scope > [data-testid="stColumn"]');
                if (cols.length < 2) return;

                // Wait a tick for layout to settle
                setTimeout(function() {
                    if (s0) cols[0].scrollTop = parseInt(s0, 10);
                    if (s1) cols[1].scrollTop = parseInt(s1, 10);
                    sessionStorage.removeItem('gt_col_scroll_0');
                    sessionStorage.removeItem('gt_col_scroll_1');
                }, 100);
            });
            parentDoc._gtScrollObserver.observe(parentDoc.body, { childList: true, subtree: true });
        }
    })();
    </script>
    """, height=0, width=0)
