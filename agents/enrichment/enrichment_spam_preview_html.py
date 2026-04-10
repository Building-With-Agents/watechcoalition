"""Self-contained HTML for JSearch enrichment + spam preview (read-only diagnostic)."""

from __future__ import annotations

import html
import json
from typing import Any


def _esc(s: Any) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def _tier_class(tier: str | None) -> str:
    t = (tier or "").lower()
    if t == "clean":
        return "tier-clean"
    if t == "flagged":
        return "tier-flagged"
    if t == "rejected":
        return "tier-rejected"
    return "tier-unknown"


def render_enrichment_spam_preview_html(
    rows: list[dict[str, Any]],
    *,
    page_title: str = "Enrichment + spam preview",
    subtitle: str = "",
) -> str:
    """*rows*: each dict has ``db`` (SQL row mapping), ``enriched`` (RecordEnriched payload)."""
    sub = f'<p class="sub">{_esc(subtitle)}</p>' if subtitle else ""
    legend = (
        '<p class="legend"><strong>Spam tiers:</strong> clean → would write <code>is_spam=false</code>; '
        "flagged → <code>is_spam</code> NULL with <code>spam_score</code>; rejected → would not write to "
        "<code>job_postings</code>. uncertain = classifier degraded.</p>"
    )

    cards: list[str] = []
    for item in rows:
        db = item.get("db") or {}
        enr = item.get("enriched") or {}

        tier = enr.get("spam_tier") or "—"
        badge = _tier_class(str(tier) if tier != "—" else "")

        nj = db.get("normalized_job_id")
        jp = db.get("job_posting_id")
        src = db.get("source")
        eid = db.get("external_id")

        title = db.get("job_title") or enr.get("title")
        company = db.get("job_company") or enr.get("company")
        desc = db.get("job_description")

        ei_blob = {
            "skills": db.get("skills"),
            "tools": db.get("tools"),
            "tasks": db.get("tasks"),
            "responsibilities": db.get("responsibilities"),
            "context": db.get("context"),
            "extraction_failed": db.get("extraction_failed"),
            "ei_overall_confidence": db.get("ei_overall_confidence"),
        }
        ei_json = _esc(json.dumps(ei_blob, indent=2, ensure_ascii=False)[:80000])

        fc = enr.get("field_confidence") or {}
        fc_json = _esc(json.dumps(fc, indent=2, ensure_ascii=False))

        qscore = enr.get("quality_score")
        qscore_s = "—" if qscore is None else f"{float(qscore):.4f}"
        qcomp = enr.get("quality_components") or {}
        qcomp_json = _esc(json.dumps(qcomp, indent=2, ensure_ascii=False))

        is_spam = enr.get("is_spam")
        if enr.get("spam_degraded"):
            is_spam_s = "NULL (uncertain — classifier degraded)"
        elif is_spam is None and enr.get("spam_score") is not None:
            is_spam_s = "NULL (flagged for review — SQL NULL semantics)"
        elif is_spam is None:
            is_spam_s = "NULL"
        else:
            is_spam_s = "true" if is_spam else "false"

        ss = enr.get("spam_score")
        score_s = "NULL" if ss is None else f"{float(ss):.4f}"

        cards.append(
            f"""
<section class="card">
  <div class="head">
    <span class="badge {badge}">{_esc(tier)}</span>
    <span class="meta">normalized_job_id={_esc(nj)} job_posting_id={_esc(jp)} source={_esc(src)} external_id={_esc(eid)}</span>
  </div>
  <dl class="kv">
    <dt>role_classification</dt><dd>{_esc(enr.get("role_classification"))}</dd>
    <dt>seniority</dt><dd>{_esc(enr.get("seniority"))}</dd>
    <dt>quality_score</dt><dd>{_esc(qscore_s)}</dd>
    <dt>spam_score</dt><dd>{score_s}</dd>
    <dt>is_spam</dt><dd>{is_spam_s}</dd>
    <dt>overall_confidence</dt><dd>{_esc(enr.get("overall_confidence"))}</dd>
    <dt>spam_degraded</dt><dd>{_esc(enr.get("spam_degraded"))}</dd>
    <dt>spam_used_heuristic</dt><dd>{_esc(enr.get("spam_used_heuristic"))}</dd>
  </dl>
  <p class="rationale"><strong>Rationale:</strong> {_esc(enr.get("spam_rationale") or "—")}</p>
  <p class="note"><strong>Extraction note:</strong> {_esc(enr.get("spam_extraction_note") or "—")}</p>
  <h2 class="title">{_esc(title)}</h2>
  <p class="company">{_esc(company)}</p>
  <pre class="desc">{_esc(desc)}</pre>
  <details><summary>extracted_intelligence (JSON)</summary><pre class="json">{ei_json}</pre></details>
  <details><summary>quality_components</summary><pre class="json">{qcomp_json}</pre></details>
  <details><summary>field_confidence</summary><pre class="json">{fc_json}</pre></details>
</section>
"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{_esc(page_title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1rem 2rem; max-width: 1000px; }}
    .sub {{ color: #555; }}
    .legend {{ font-size: 0.95rem; }}
    .card {{ border: 1px solid #ccc; border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; }}
    .head {{ display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }}
    .meta {{ color: #555; font-size: 0.9rem; }}
    .badge {{ padding: 0.25rem 0.6rem; border-radius: 4px; font-weight: 600; }}
    .tier-clean {{ background: #d4edda; color: #155724; }}
    .tier-flagged {{ background: #fff3cd; color: #856404; }}
    .tier-rejected {{ background: #f8d7da; color: #721c24; }}
    .tier-unknown {{ background: #e2e3e5; color: #383d41; }}
    dl.kv {{ display: grid; grid-template-columns: 14rem 1fr; gap: 0.25rem 1rem; }}
    dt {{ font-weight: 600; }}
    .desc {{ white-space: pre-wrap; word-break: break-word; background: #f8f9fa; padding: 0.75rem; }}
    .json {{ font-size: 0.85rem; overflow: auto; max-height: 28rem; background: #f8f9fa; padding: 0.5rem; }}
    .title {{ margin: 0.5rem 0 0; font-size: 1.25rem; }}
    .company {{ color: #555; margin: 0 0 0.5rem; }}
  </style>
</head>
<body>
  <h1>{_esc(page_title)}</h1>
  {sub}
  {legend}
  {"".join(cards)}
</body>
</html>
"""
