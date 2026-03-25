"""
End-to-end: ingest → normalize → skills extract → EnrichmentAgent (role/seniority + spam).

Same source contract as ``run_jsearch_enrichment_preview.py``. Read-only DB for reporting;
does not write to ``job_postings``. Spam scoring uses latest ``dbo.extracted_intelligence``
per ``normalized_job_id`` inside ``EnrichmentAgent``.

PowerShell (repo root)::

    python -m agents.scripts.run_jsearch_enrichment_preview_spam --limit 20 --html-out agents/data/rendered/enrichment_spam_preview.html

Classify an existing run only::

    python -m agents.scripts.run_jsearch_enrichment_preview_spam --skip-ingest --ingestion-run-id <uuid> --html-out agents/data/rendered/enrichment_spam_preview.html
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import structlog
from dotenv import load_dotenv
from sqlalchemy import text

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

load_dotenv(_REPO_ROOT / ".env")

from agents.common.data_store.database import session_scope  # noqa: E402
from agents.common.event_envelope import EventEnvelope  # noqa: E402
from agents.enrichment.agent import EnrichmentAgent  # noqa: E402
from agents.enrichment.enrichment_spam_preview_html import (  # noqa: E402
    render_enrichment_spam_preview_html,
)
from agents.ingestion.agent import IngestionAgent  # noqa: E402
from agents.normalization.agent import NormalizationAgent  # noqa: E402
from agents.scripts.jsearch_enrichment_preview_lib import SPAM_PREVIEW_SQL_BY_RUN  # noqa: E402
from agents.skills_extraction.agent import SkillsExtractionAgent  # noqa: E402

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger()


def _run_pipeline_chain(
    *,
    correlation_id: str,
    source: str,
    limit: int,
    query: str,
    location: str,
) -> str:
    """Return ingestion ``batch_id`` (same as ``ingestion_run_id`` on normalized rows)."""
    trigger = EventEnvelope(
        correlation_id=correlation_id,
        agent_id="run-jsearch-enrichment-preview-spam",
        payload={
            "source": source,
            "limit": limit,
            "query": query,
            "location": location,
        },
    )
    out_ingest = IngestionAgent().process(trigger)
    payload = out_ingest.payload
    if payload.get("event_type") == "SourceFailure":
        log.error("ingestion_failed", **{k: v for k, v in payload.items() if k != "error"})
        raise SystemExit(1)
    batch_id = str(payload.get("batch_id") or "")
    if not batch_id:
        log.error("ingestion_missing_batch_id")
        raise SystemExit(1)

    out_norm = NormalizationAgent().process(out_ingest)
    SkillsExtractionAgent().process(out_norm)

    log.info(
        "pipeline_chain_complete",
        batch_id=batch_id,
        staged_count=payload.get("staged_count"),
        normalized_count=out_norm.payload.get("normalized_count"),
    )
    return batch_id


def _fmt_bool_or_null(v: Any) -> str:
    if v is None:
        return "NULL"
    return "true" if v else "false"


def _extraction_note(row: dict[str, Any]) -> str:
    parts: list[str] = []
    if bool(row.get("extraction_failed")):
        parts.append("extraction_failed")
    s, t, ta, r, c = (
        row.get("skills") or [],
        row.get("tools") or [],
        row.get("tasks") or [],
        row.get("responsibilities") or [],
        row.get("context") or [],
    )
    if not (s or t or ta or r or c):
        parts.append("empty_extraction")
    return ",".join(parts) if parts else "—"


def _process_enrichment_spam_run(
    *,
    run_id: str,
    emit_jsonl: bool,
    html_out: Path | None,
    correlation_id: str,
    html_page_title: str,
) -> int:
    stmt = text(SPAM_PREVIEW_SQL_BY_RUN)
    params: dict[str, Any] = {"run_id": run_id}

    with session_scope() as session:
        rows = session.execute(stmt, params).mappings().all()

    agent = EnrichmentAgent()
    merged_for_html: list[dict[str, Any]] = []
    n = 0

    for row in rows:
        rdict = dict(row)
        nj = int(rdict["normalized_job_id"])
        jp = rdict.get("job_posting_id")
        posting_id: Any = jp if jp is not None else nj

        skills = rdict.get("skills")
        if skills is None:
            skills = []

        ev = EventEnvelope(
            correlation_id=correlation_id,
            agent_id="run-jsearch-enrichment-preview-spam",
            payload={
                "event_type": "SkillsExtracted",
                "batch_id": run_id,
                "normalized_job_id": nj,
                "posting_id": posting_id,
                "title": rdict.get("job_title") or "",
                "description": rdict.get("job_description"),
                "company": rdict.get("job_company"),
                "skills": skills,
            },
        )
        out = agent.process(ev)
        enr = dict(out.payload)

        note = _extraction_note(rdict)
        tier = enr.get("spam_tier", "—")
        ss = enr.get("spam_score")
        score_s = "NULL" if ss is None else f"{float(ss):.4f}"
        line = (
            f"normalized_job_id={nj}\tjob_posting_id={jp or ''}\t"
            f"source={rdict.get('source') or ''}\texternal_id={rdict.get('external_id') or ''}\t"
            f"role_classification={enr.get('role_classification')}\t"
            f"seniority={enr.get('seniority')}\t"
            f"spam_score={score_s}\tis_spam={_fmt_bool_or_null(enr.get('is_spam'))}\t"
            f"spam_tier={tier}\tnote={note}"
        )
        print(line)  # noqa: T201

        if emit_jsonl:
            rec = {"db": rdict, "enriched": enr}
            print(json.dumps(rec, default=str), flush=True)  # noqa: T201

        merged_for_html.append({"db": rdict, "enriched": enr})
        n += 1

    if html_out is not None:
        html_out.parent.mkdir(parents=True, exist_ok=True)
        sub = f"ingestion_run_id = {run_id}"
        doc = render_enrichment_spam_preview_html(
            merged_for_html,
            page_title=html_page_title,
            subtitle=sub,
        )
        html_out.write_text(doc, encoding="utf-8")
        log.info("enrichment_spam_html_written", path=str(html_out), row_count=len(merged_for_html))

    log.info("enrichment_spam_run_complete", row_count=n, jsonl=emit_jsonl, run_id=run_id)
    return n


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest → normalize → skills → enrichment (with spam from extracted_intelligence)."
    )
    parser.add_argument(
        "--source",
        choices=["jsearch", "crawl4ai", "all"],
        default="all",
        help="Ingestion source(s). Default: all.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max jobs per ingest when not using --skip-ingest.",
    )
    parser.add_argument("--query", default="software engineer", help="Keyword query (region config).")
    parser.add_argument("--location", default="Washington state", help="Location string (region config).")
    parser.add_argument(
        "--correlation-id",
        default="",
        help="Correlation id for enrichment events (default: random UUID).",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip ingest; query DB by --ingestion-run-id.",
    )
    parser.add_argument(
        "--ingestion-run-id",
        default="",
        help="With --skip-ingest: filter normalized_jobs by this run id.",
    )
    parser.add_argument(
        "--html-out",
        type=Path,
        default=None,
        help="Write HTML report to this path.",
    )
    parser.add_argument(
        "--no-jsonl",
        action="store_true",
        help="Do not print JSON lines to stdout.",
    )
    args = parser.parse_args()

    if not os.getenv("PYTHON_DATABASE_URL"):
        log.error("missing_python_database_url")
        raise SystemExit(1)

    cid = args.correlation_id.strip() or str(uuid.uuid4())

    if args.skip_ingest:
        run_id = args.ingestion_run_id.strip()
        if not run_id:
            log.error("ingestion_run_id_required_with_skip_ingest")
            raise SystemExit(1)
    else:
        if args.source in ("jsearch", "all") and not os.getenv("JSEARCH_API_KEY"):
            log.error("missing_jsearch_api_key")
            raise SystemExit(1)
        run_id = _run_pipeline_chain(
            correlation_id=cid,
            source=args.source,
            limit=args.limit,
            query=args.query,
            location=args.location,
        )

    emit_jsonl = not args.no_jsonl
    if not emit_jsonl and args.html_out is None:
        log.error("nothing_to_emit_use_jsonl_or_html_out")
        raise SystemExit(1)

    if args.skip_ingest:
        title = "Batch — enrichment + spam"
    else:
        title_map = {
            "all": "JSearch + Crawl4AI — enrichment + spam",
            "jsearch": "JSearch — enrichment + spam",
            "crawl4ai": "Crawl4AI — enrichment + spam",
        }
        title = title_map.get(args.source, title_map["all"])

    _process_enrichment_spam_run(
        run_id=run_id,
        emit_jsonl=emit_jsonl,
        html_out=args.html_out,
        correlation_id=cid,
        html_page_title=title,
    )


if __name__ == "__main__":
    main()
