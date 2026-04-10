"""Side-by-side HTML report: job posting text vs deterministic enrichment labels.

Suitable for local review; escape all dynamic text for XSS safety.

This module does **not** call ``load_dotenv`` or read process environment variables;
it only formats the *rows* dicts passed in. Callers (e.g. CLI scripts) should load
repo-root ``.env`` before opening DB connections or building those rows.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from typing import Any


def _esc(s: Any) -> str:
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def render_enrichment_comparison_html(
    rows: list[dict[str, Any]],
    *,
    page_title: str = "Enrichment comparison",
    subtitle: str | None = None,
) -> str:
    """
    Build a full HTML document. Each *rows* item should include posting fields
    (e.g. ``job_title``, ``company``, ``job_description``, ``source``,
    ``external_id``) and enrichment fields (``seniority``, ``role_classification``,
    ``normalized_job_id``, optional ``job_posting_id``).
    """
    subtitle_html = f'<p class="sub">{_esc(subtitle)}</p>' if subtitle else ""
    cards: list[str] = []
    for i, row in enumerate(rows, start=1):
        cards.append(_render_card(row, index=i))

    body = "\n".join(cards)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>{_esc(page_title)}</title>
  <style>
    :root {{
      --border: #c5cbd3;
      --bg: #f6f8fa;
      --panel: #fff;
      --accent: #0969da;
      --muted: #57606a;
    }}
    body {{
      font-family: system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 1.5rem;
      background: var(--bg);
      color: #1f2328;
      line-height: 1.5;
    }}
    h1 {{ font-size: 1.35rem; margin: 0 0 0.25rem 0; }}
    .sub {{ color: var(--muted); margin: 0 0 1.25rem 0; font-size: 0.9rem; }}
    .job-card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      margin-bottom: 1.25rem;
      overflow: hidden;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}
    .job-card h2 {{
      margin: 0;
      padding: 0.65rem 1rem;
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--muted);
      background: #eaeef2;
      border-bottom: 1px solid var(--border);
    }}
    .cols {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0;
      min-height: 8rem;
    }}
    @media (max-width: 900px) {{
      .cols {{ grid-template-columns: 1fr; }}
    }}
    .col {{
      padding: 1rem 1.1rem;
      vertical-align: top;
    }}
    .col-posting {{ border-right: 1px solid var(--border); }}
    @media (max-width: 900px) {{
      .col-posting {{ border-right: none; border-bottom: 1px solid var(--border); }}
    }}
    .col h3 {{
      margin: 0 0 0.5rem 0;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--muted);
    }}
    .title-line {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 0.35rem; }}
    .company {{ color: var(--muted); margin-bottom: 0.75rem; }}
    .meta {{ font-size: 0.8rem; color: var(--muted); margin-bottom: 0.75rem; }}
    .meta code {{ background: #eef1f4; padding: 0.1rem 0.35rem; border-radius: 4px; }}
    .body-text {{
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 0.88rem;
      max-height: 28rem;
      overflow-y: auto;
      border: 1px solid #e8eaed;
      border-radius: 6px;
      padding: 0.65rem 0.75rem;
      background: #fafbfc;
    }}
    .enrich-dl {{
      margin: 0;
      display: grid;
      gap: 0.65rem;
    }}
    .enrich-dl dt {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--muted);
      margin: 0;
    }}
    .enrich-dl dd {{
      margin: 0.15rem 0 0 0;
      font-size: 1.05rem;
      font-weight: 600;
    }}
    .enrich-role {{ color: var(--accent); }}
    .qc-pre {{
      font-size: 0.72rem;
      margin: 0.5rem 0 0 0;
      padding: 0.5rem;
      background: #f6f8fa;
      border-radius: 6px;
      overflow-x: auto;
      max-height: 10rem;
    }}
    footer {{
      margin-top: 2rem;
      font-size: 0.8rem;
      color: var(--muted);
    }}
  </style>
</head>
<body>
  <h1>{_esc(page_title)}</h1>
  {subtitle_html}
  {body}
  <footer>Generated {_esc(now)} · {len(rows)} job(s)</footer>
</body>
</html>
"""


def _render_card(row: dict[str, Any], *, index: int) -> str:
    title = _esc(row.get("job_title") or row.get("title") or "(no title)")
    company = _esc(row.get("job_company") or row.get("company") or "")
    desc = row.get("job_description") or row.get("description") or ""
    desc_html = _esc(desc) if desc else '<em class="muted">(no description)</em>'

    src = _esc(row.get("source") or "")
    eid = _esc(row.get("external_id") or "")
    nj = row.get("normalized_job_id")
    jp = row.get("job_posting_id")
    loc_parts = [
        row.get("job_city") or row.get("city"),
        row.get("job_state") or row.get("state_province"),
    ]
    loc = ", ".join(str(p) for p in loc_parts if p)
    url = row.get("job_url") or ""
    url_html = f'<div class="meta"><a href="{_esc(url)}" rel="noopener">Job URL</a></div>' if url else ""

    seniority = _esc(row.get("seniority") or "")
    role = _esc(row.get("role_classification") or "")
    qs = row.get("quality_score")
    qc = row.get("quality_components")
    qs_html = f"{float(qs):.4f}" if isinstance(qs, int | float) else _esc(qs)
    qc_html = (
        f'<pre class="qc-pre">{_esc(json.dumps(qc, indent=2, sort_keys=True))}</pre>' if isinstance(qc, dict) else ""
    )

    return f"""
  <section class="job-card" id="job-{index}">
    <h2>Job #{index}</h2>
    <div class="cols">
      <div class="col col-posting">
        <h3>Job posting (normalized)</h3>
        <div class="title-line">{title}</div>
        {f'<div class="company">{company}</div>' if company else ""}
        <div class="meta">
          <div><strong>source</strong> <code>{src}</code> · <strong>external_id</strong> <code>{eid}</code></div>
          <div><strong>normalized_job_id</strong> <code>{_esc(nj)}</code>
          {f" · <strong>job_posting_id</strong> <code>{_esc(jp)}</code>" if jp else ""}</div>
          {f"<div><strong>location</strong> {_esc(loc)}</div>" if loc else ""}
        </div>
        {url_html}
        <div class="body-text">{desc_html}</div>
      </div>
      <div class="col col-enrichment">
        <h3>Enrichment output</h3>
        <dl class="enrich-dl">
          <dt>Seniority</dt>
          <dd>{seniority or "<em>—</em>"}</dd>
          <dt>Role classification</dt>
          <dd class="enrich-role">{role or "<em>—</em>"}</dd>
          <dt>Quality score</dt>
          <dd>{qs_html if qs is not None else "<em>—</em>"}</dd>
        </dl>
        {qc_html}
      </div>
    </div>
  </section>
"""


def snippet_json_preview(obj: Any, max_len: int = 2000) -> str:
    """Optional compact JSON for debugging (escaped)."""
    try:
        s = json.dumps(obj, indent=2, default=str)
    except TypeError:
        s = str(obj)
    if len(s) > max_len:
        s = s[: max_len - 3] + "..."
    return _esc(s)
