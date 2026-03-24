"""
End-to-end: JSearch ingest → normalize → skills extract → deterministic enrichment JSONL.

Chains existing agents (no ``job_postings`` promotion). Prints one JSON object per line
(stdout) with ``normalized_job_id``, optional ``job_posting_id``, ``source``,
``external_id``, ``seniority``, ``role_classification``.

Use ``--html-out path`` to write a side-by-side HTML comparison (posting vs enrichment).
Add ``--no-jsonl`` to suppress stdout JSONL when you only want the HTML file.

Prerequisites (repo-root ``.env`` or environment):
  - ``PYTHON_DATABASE_URL`` — SQLAlchemy PostgreSQL URL
  - ``JSEARCH_API_KEY`` — when not using ``--skip-ingest``
  - Optional: ``SKILLS_EXTRACTION_MAX_JOBS`` — default ``10`` caps how many normalized
    rows get Pass 2 extraction in one run; set to ``0`` to process **all** rows
    (see ``SkillsExtractionAgent.process``).

PowerShell::

    cd C:\\path\\to\\watechcoalition
    py agents/scripts/run_jsearch_enrichment_preview.py --limit 20

Classify an existing run only (normalization + skills must have already run)::

    py agents/scripts/run_jsearch_enrichment_preview.py --skip-ingest --ingestion-run-id <uuid>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

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
from agents.enrichment.comparison_report_html import (  # noqa: E402
    render_enrichment_comparison_html,
)
from agents.ingestion.agent import IngestionAgent  # noqa: E402
from agents.normalization.agent import NormalizationAgent  # noqa: E402
from agents.scripts.jsearch_enrichment_preview_lib import (  # noqa: E402
    NORMALIZED_RUN_SQL,
    build_enrichment_output_record,
)
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
    limit: int,
    query: str,
    location: str,
) -> str:
    """Return ingestion ``batch_id`` (same as ``ingestion_run_id`` on normalized rows)."""
    trigger = EventEnvelope(
        correlation_id=correlation_id,
        agent_id="run-jsearch-enrichment-preview",
        payload={
            "source": "jsearch",
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
    out_skills = SkillsExtractionAgent().process(out_norm)

    log.info(
        "pipeline_chain_complete",
        batch_id=batch_id,
        staged_count=payload.get("staged_count"),
        normalized_count=out_norm.payload.get("normalized_count"),
        skills_count=out_skills.payload.get("skills_count"),
        tools_count=out_skills.payload.get("tools_count"),
    )
    return batch_id


def _process_enrichment_run(
    run_id: str,
    *,
    emit_jsonl: bool,
    html_out: Path | None,
) -> int:
    stmt = text(NORMALIZED_RUN_SQL)
    with session_scope() as session:
        technology_areas, industry_sectors = EnrichmentAgent._load_reference_labels(session)
        rows = session.execute(stmt, {"run_id": run_id}).mappings().all()

    merged_for_html: list[dict] = []
    n = 0
    for row in rows:
        rec = build_enrichment_output_record(
            normalized_job_id=int(row["normalized_job_id"]),
            source=str(row.get("source") or ""),
            external_id=str(row.get("external_id") or ""),
            job_title=str(row.get("job_title") or ""),
            job_description=row.get("job_description"),
            skills=row.get("skills"),
            tools=row.get("tools"),
            tasks=row.get("tasks"),
            responsibilities=row.get("responsibilities"),
            context=row.get("context"),
            technology_areas=technology_areas,
            industry_sectors=industry_sectors,
            job_posting_id=row.get("job_posting_id"),
            is_internship=bool(row.get("is_internship")),
        )
        if emit_jsonl:
            print(json.dumps(rec, default=str), flush=True)  # noqa: T201 — JSONL stdout contract
        if html_out is not None:
            merged = {
                **rec,
                "job_title": row.get("job_title"),
                "job_company": row.get("job_company"),
                "job_description": row.get("job_description"),
                "job_city": row.get("job_city"),
                "job_state": row.get("job_state"),
                "job_url": row.get("job_url"),
            }
            merged_for_html.append(merged)
        n += 1

    if html_out is not None:
        html_out.parent.mkdir(parents=True, exist_ok=True)
        doc = render_enrichment_comparison_html(
            merged_for_html,
            page_title="JSearch batch — posting vs enrichment",
            subtitle=f"ingestion_run_id = {run_id}",
        )
        html_out.write_text(doc, encoding="utf-8")
        log.info("enrichment_html_written", path=str(html_out), row_count=len(merged_for_html))

    log.info("enrichment_run_complete", run_id=run_id, row_count=n, jsonl=emit_jsonl)
    return n


def main() -> None:
    parser = argparse.ArgumentParser(
        description="JSearch → normalize → skills → print deterministic enrichment (JSONL)."
    )
    parser.add_argument("--limit", type=int, default=50, help="JSearch fetch cap (ingest only).")
    parser.add_argument("--query", default="software engineer", help="Keyword query for JSearch.")
    parser.add_argument("--location", default="Washington state", help="Location string for JSearch.")
    parser.add_argument(
        "--correlation-id",
        default="",
        help="Correlation id for the event chain (default: random UUID).",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip API + agents; only query DB for this ingestion_run_id.",
    )
    parser.add_argument(
        "--ingestion-run-id",
        default="",
        help="Required with --skip-ingest; same as batch_id from a prior ingest.",
    )
    parser.add_argument(
        "--html-out",
        type=Path,
        default=None,
        help="Write side-by-side HTML report (job posting vs enrichment) to this path.",
    )
    parser.add_argument(
        "--no-jsonl",
        action="store_true",
        help="Do not print JSON lines to stdout (use with --html-out for HTML-only).",
    )
    args = parser.parse_args()

    if not os.getenv("PYTHON_DATABASE_URL"):
        log.error("missing_python_database_url")
        raise SystemExit(1)

    if args.skip_ingest:
        run_id = args.ingestion_run_id.strip()
        if not run_id:
            log.error("ingestion_run_id_required_with_skip_ingest")
            raise SystemExit(1)
    else:
        if not os.getenv("JSEARCH_API_KEY"):
            log.error("missing_jsearch_api_key")
            raise SystemExit(1)
        cid = args.correlation_id.strip() or str(uuid.uuid4())
        run_id = _run_pipeline_chain(
            correlation_id=cid,
            limit=args.limit,
            query=args.query,
            location=args.location,
        )

    emit_jsonl = not args.no_jsonl
    if not emit_jsonl and args.html_out is None:
        log.error("nothing_to_emit_use_jsonl_or_html_out")
        raise SystemExit(1)

    _process_enrichment_run(run_id, emit_jsonl=emit_jsonl, html_out=args.html_out)


if __name__ == "__main__":
    main()
