"""HTML report for spam preview (single self-contained file)."""

from __future__ import annotations

import html
import json
from typing import Any

from agents.enrichment.classifiers.spam_preview import SpamPreviewResult


def render_spam_preview_html(
    rows: list[tuple[dict[str, Any], SpamPreviewResult]],
    *,
    flag_threshold: float,
    reject_threshold: float,
) -> str:
    """Build one HTML document. *rows* is (db_row, preview_result) per job."""
    legend = (
        f"<p><strong>Thresholds (env):</strong> SPAM_FLAG_THRESHOLD={flag_threshold:g}, "
        f"SPAM_REJECT_THRESHOLD={reject_threshold:g}. "
        "Tier semantics: <em>clean</em> → would write <code>is_spam=false</code>; "
        "<em>flagged</em> → would write <code>is_spam</code> NULL with <code>spam_score</code> set "
        "(SQL NULL = unknown — query with <code>is_spam IS NULL AND spam_score IS NOT NULL</code>); "
        "<em>rejected</em> → would <strong>not</strong> write to "
        "<code>job_postings</code> (this report still shows text for review). "
        "<em>uncertain</em> = classifier degraded — not verified clean.</p>"
    )

    cards: list[str] = []
    for row, preview in rows:
        tier = preview.tier
        badge_class = "tier-unknown"
        if tier == "clean":
            badge_class = "tier-clean"
        elif tier == "flagged":
            badge_class = "tier-flagged"
        elif tier == "rejected":
            badge_class = "tier-rejected"

        if preview.degraded:
            is_spam_s = "NULL (uncertain — classifier degraded)"
        elif preview.is_spam is None:
            is_spam_s = "NULL (flagged for review — SQL NULL semantics)"
        else:
            is_spam_s = "true" if preview.is_spam is True else "false"

        score_s = "NULL" if preview.spam_score is None else f"{preview.spam_score:.4f}"
        oc_s = "NULL" if preview.overall_confidence is None else f"{preview.overall_confidence:.4f}"
        fc_json = json.dumps(preview.field_confidence, indent=2, ensure_ascii=False) if preview.field_confidence else "{}"

        title = html.escape(str(row.get("job_title") or ""))
        company = html.escape(str(row.get("job_company") or ""))
        desc = html.escape(str(row.get("job_description") or ""))
        nj_id = row.get("normalized_job_id")
        src = html.escape(str(row.get("source") or ""))
        eid = html.escape(str(row.get("external_id") or ""))

        ex_blob = {
            "skills": row.get("skills"),
            "tools": row.get("tools"),
            "tasks": row.get("tasks"),
            "responsibilities": row.get("responsibilities"),
            "context": row.get("context"),
        }
        ex_json = html.escape(json.dumps(ex_blob, indent=2, ensure_ascii=False)[:50000])

        rat = html.escape(str(preview.rationale or ""))
        enote = html.escape(str(preview.extraction_note or ""))
        heur = "yes" if preview.used_heuristic else "no"

        cards.append(
            f"""
<section class="card">
  <div class="card-head">
    <span class="badge {badge_class}">{html.escape(tier)}</span>
    <span class="meta">normalized_job_id={html.escape(str(nj_id))} source={src} external_id={eid}</span>
  </div>
  <dl class="kv">
    <dt>spam_score</dt><dd>{score_s}</dd>
    <dt>is_spam</dt><dd>{is_spam_s}</dd>
    <dt>overall_confidence</dt><dd>{oc_s}</dd>
    <dt>heuristic_used</dt><dd>{heur}</dd>
    <dt>extraction_note</dt><dd>{enote or "—"}</dd>
  </dl>
  <p class="rationale"><strong>Rationale:</strong> {rat or "—"}</p>
  <h3 class="jobtitle">{title}</h3>
  <p class="company">{company}</p>
  <pre class="desc">{desc}</pre>
  <details>
    <summary>extracted_intelligence (JSON)</summary>
    <pre class="json">{ex_json}</pre>
  </details>
  <details>
    <summary>field_confidence</summary>
    <pre class="json">{html.escape(fc_json)}</pre>
  </details>
</section>
"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Spam preview — Decision #8</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1rem 2rem; max-width: 960px; }}
    .card {{ border: 1px solid #ccc; border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; }}
    .card-head {{ display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem; flex-wrap: wrap; }}
    .meta {{ color: #555; font-size: 0.9rem; }}
    .badge {{ padding: 0.25rem 0.6rem; border-radius: 4px; font-weight: 600; }}
    .tier-clean {{ background: #d4edda; color: #155724; }}
    .tier-flagged {{ background: #fff3cd; color: #856404; }}
    .tier-rejected {{ background: #f8d7da; color: #721c24; }}
    .tier-unknown {{ background: #e2e3e5; color: #383d41; }}
    dl.kv {{ display: grid; grid-template-columns: 12rem 1fr; gap: 0.25rem 1rem; }}
    dt {{ font-weight: 600; }}
    .desc {{ white-space: pre-wrap; word-break: break-word; background: #f8f9fa; padding: 0.75rem; }}
    .json {{ font-size: 0.85rem; overflow: auto; max-height: 24rem; background: #f8f9fa; padding: 0.5rem; }}
    .jobtitle {{ margin: 0.5rem 0 0; }}
    .company {{ color: #555; margin: 0 0 0.5rem; }}
    .rationale {{ font-size: 0.95rem; }}
  </style>
</head>
<body>
  <h1>Spam detection preview</h1>
  {legend}
  {"".join(cards)}
</body>
</html>
"""
