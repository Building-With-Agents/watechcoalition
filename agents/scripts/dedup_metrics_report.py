"""Write a read-only HTML report of fuzzy dedup metrics from PostgreSQL.

Usage (repo root, with ``PYTHON_DATABASE_URL`` in ``.env``)::

    py -3.11 -m agents.scripts.dedup_metrics_report
    py -3.11 -m agents.scripts.dedup_metrics_report --output agents/data/reports/dedup_metrics.html --top-n 30 --open

Loads ``.env`` from repo root like ``db_check.py``. No long-running server;
open the generated HTML in a browser.
"""

from __future__ import annotations

import argparse
import html
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError

# Repo root on sys.path (parent of ``agents/``)
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from agents.common.env import load_repo_root_dotenv  # noqa: E402

load_repo_root_dotenv()


def _h(s: object) -> str:
    return html.escape(str(s), quote=True)


def _engine() -> Engine:
    import os

    url = os.getenv("PYTHON_DATABASE_URL")
    if not url or not str(url).strip():
        print("error: PYTHON_DATABASE_URL is not set", file=sys.stderr)
        sys.exit(1)
    return create_engine(url, future=True)


def _scalar(conn, sql: str, params: dict | None = None) -> object:
    row = conn.execute(text(sql), params or {}).first()
    return row[0] if row else None


def _rows(conn, sql: str, params: dict | None = None) -> list[dict]:
    return [dict(r) for r in conn.execute(text(sql), params or {}).mappings().all()]


def gather_metrics(engine: Engine, *, top_n: int) -> dict:
    out: dict = {}
    with engine.connect() as conn:
        out["with_embedding"] = int(
            _scalar(
                conn,
                """
                SELECT COUNT(*) FROM dbo.job_postings
                WHERE dedup_embedding IS NOT NULL
                """,
            )
            or 0
        )

        dup_rows = _rows(
            conn,
            """
            SELECT
                CASE
                    WHEN is_duplicate IS TRUE THEN 'true'
                    WHEN is_duplicate IS FALSE THEN 'false'
                    ELSE 'null'
                END AS bucket,
                COUNT(*) AS cnt
            FROM dbo.job_postings
            GROUP BY 1
            ORDER BY 1
            """,
        )
        out["is_duplicate_buckets"] = dup_rows

        out["distinct_clusters"] = int(
            _scalar(
                conn,
                """
                SELECT COUNT(DISTINCT duplicate_cluster_id)
                FROM dbo.job_postings
                WHERE duplicate_cluster_id IS NOT NULL
                """,
            )
            or 0
        )

        out["top_clusters"] = _rows(
            conn,
            """
            SELECT
                duplicate_cluster_id::text AS cluster_id,
                COUNT(*) AS member_count,
                MAX(SUBSTRING(job_title FROM 1 FOR 80)) AS sample_title
            FROM dbo.job_postings
            WHERE duplicate_cluster_id IS NOT NULL
            GROUP BY duplicate_cluster_id::text
            ORDER BY member_count DESC
            LIMIT :n
            """,
            {"n": top_n},
        )

        out["recent_postings"] = _rows(
            conn,
            """
            SELECT
                job_posting_id::text AS job_posting_id,
                CASE WHEN is_duplicate IS TRUE THEN 'true'
                     WHEN is_duplicate IS FALSE THEN 'false'
                     ELSE 'null' END AS is_duplicate,
                duplicate_cluster_id::text AS duplicate_cluster_id,
                SUBSTRING(dedup_text_hash FROM 1 FOR 12) AS dedup_hash_prefix
            FROM dbo.job_postings
            WHERE publish_date >= NOW() - INTERVAL '7 days'
            ORDER BY publish_date DESC NULLS LAST
            LIMIT 100
            """,
        )

        out["audit_enrichment_dedup"] = None
        try:
            cnt = _scalar(
                conn,
                """
                SELECT COUNT(*) FROM dbo.llm_audit_log
                WHERE agent_name = 'enrichment-dedup'
                """,
            )
            last_at = _scalar(
                conn,
                """
                SELECT MAX(created_at) FROM dbo.llm_audit_log
                WHERE agent_name = 'enrichment-dedup'
                """,
            )
            out["audit_enrichment_dedup"] = {"count": int(cnt or 0), "last_at": last_at}
        except Exception:
            out["audit_enrichment_dedup"] = {"count": None, "last_at": None, "error": "llm_audit_log query failed"}

    out["generated_at"] = datetime.now(timezone.utc).isoformat()
    return out


def render_html(metrics: dict) -> str:
    buckets = metrics.get("is_duplicate_buckets") or []
    bucket_rows = "".join(f"<tr><td>{_h(r.get('bucket'))}</td><td>{int(r.get('cnt') or 0)}</td></tr>" for r in buckets)
    clusters = metrics.get("top_clusters") or []
    cluster_rows = "".join(
        f"<tr><td><code>{_h(c.get('cluster_id'))}</code></td>"
        f"<td>{int(c.get('member_count') or 0)}</td>"
        f"<td>{_h(c.get('sample_title') or '')}</td></tr>"
        for c in clusters
    )
    recent = metrics.get("recent_postings") or []
    recent_rows = "".join(
        f"<tr><td><code>{_h(p.get('job_posting_id'))}</code></td>"
        f"<td>{_h(p.get('is_duplicate'))}</td>"
        f"<td><code>{_h(p.get('duplicate_cluster_id') or '')}</code></td>"
        f"<td><code>{_h(p.get('dedup_hash_prefix') or '')}</code></td></tr>"
        for p in recent
    )
    audit = metrics.get("audit_enrichment_dedup") or {}
    audit_html = ""
    if audit.get("error"):
        audit_html = f"<p class='muted'>{_h(audit['error'])}</p>"
    elif audit.get("count") is not None:
        audit_html = (
            f"<p><strong>Rows</strong>: {int(audit['count'])} &nbsp; "
            f"<strong>Last created_at</strong>: {_h(audit.get('last_at') or '')}</p>"
        )
    else:
        audit_html = "<p class='muted'>No audit data</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Fuzzy dedup metrics</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1.5rem; background: #f6f7f9; color: #1a1a1a; }}
    h1 {{ font-size: 1.35rem; }}
    .cards {{ display: flex; flex-wrap: wrap; gap: 1rem; margin: 1rem 0; }}
    .card {{ background: #fff; border-radius: 8px; padding: 1rem 1.25rem; min-width: 160px;
            box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    .card .val {{ font-size: 1.6rem; font-weight: 600; }}
    .card .lbl {{ font-size: 0.85rem; color: #555; margin-top: 0.25rem; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 960px; background: #fff;
             border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
    th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #e8e8e8; }}
    th {{ background: #eef1f5; font-size: 0.85rem; }}
    .muted {{ color: #666; font-size: 0.9rem; }}
    section {{ margin-top: 2rem; }}
  </style>
</head>
<body>
  <h1>Fuzzy dedup metrics</h1>
  <p class="muted">Generated {_h(metrics.get("generated_at", ""))} (UTC)</p>
  <p class="muted">is_duplicate: NULL means unknown / not set; see CONTEXT.md.</p>

  <div class="cards">
    <div class="card"><div class="val">{int(metrics.get("with_embedding") or 0)}</div>
      <div class="lbl">Rows with dedup_embedding</div></div>
    <div class="card"><div class="val">{int(metrics.get("distinct_clusters") or 0)}</div>
      <div class="lbl">Distinct duplicate_cluster_id</div></div>
  </div>

  <section>
    <h2>is_duplicate buckets</h2>
    <table>
      <thead><tr><th>Bucket</th><th>Count</th></tr></thead>
      <tbody>{bucket_rows or "<tr><td colspan='2' class='muted'>No rows</td></tr>"}</tbody>
    </table>
  </section>

  <section>
    <h2>Top clusters by member count</h2>
    <table>
      <thead><tr><th>cluster_id</th><th>Members</th><th>Sample title (truncated)</th></tr></thead>
      <tbody>{cluster_rows or "<tr><td colspan='3' class='muted'>No clusters</td></tr>"}</tbody>
    </table>
  </section>

  <section>
    <h2>Recent postings (last 7 days, max 100)</h2>
    <table>
      <thead><tr><th>job_posting_id</th><th>is_duplicate</th><th>duplicate_cluster_id</th>
        <th>dedup_hash prefix</th></tr></thead>
      <tbody>{recent_rows or "<tr><td colspan='4' class='muted'>No rows</td></tr>"}</tbody>
    </table>
  </section>

  <section>
    <h2>llm_audit_log (enrichment-dedup)</h2>
    {audit_html}
  </section>
</body>
</html>
"""


def main() -> None:
    p = argparse.ArgumentParser(description="Generate fuzzy dedup metrics HTML report")
    p.add_argument(
        "--output",
        "-o",
        default=str(_REPO_ROOT / "agents" / "data" / "reports" / "dedup_metrics.html"),
        help="Output HTML path",
    )
    p.add_argument("--top-n", type=int, default=20, help="Max clusters to list")
    p.add_argument("--open", action="store_true", help="Open report in default browser")
    args = p.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        eng = _engine()
        metrics = gather_metrics(eng, top_n=max(1, min(args.top_n, 500)))
    except OperationalError as exc:
        print("error: could not connect to database (check PYTHON_DATABASE_URL)", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    html_out = render_html(metrics)
    out_path.write_text(html_out, encoding="utf-8")
    print(f"Wrote {out_path.resolve()}")
    if args.open:
        webbrowser.open(out_path.resolve().as_uri())


if __name__ == "__main__":
    main()
