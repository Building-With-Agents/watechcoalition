"""Read-only spam preview for Decision #8 (diagnostic). Does not write to ``job_postings``.

Loads ``normalized_jobs`` with latest ``extracted_intelligence``, scores via Azure LLM
(see :mod:`agents.enrichment.classifiers.spam_preview`). Writes optional HTML report.

For production wiring, an ``EnrichmentDegraded`` alert would be emitted by the Enrichment
Agent when classifiers fail batch-wide; this CLI only logs ``spam_preview_degraded_count``.

PowerShell (repo root)::

    python -m agents.scripts.run_spam_detection_preview --limit 20 --html-out agents/data/rendered/spam_preview.html
"""

from __future__ import annotations

import argparse
import os
import sys
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
from agents.enrichment.classifiers.spam_preview import (  # noqa: E402
    SpamPreviewResult,
    get_spam_thresholds,
    score_spam_preview,
)
from agents.enrichment.classifiers.spam_preview_html import render_spam_preview_html  # noqa: E402
from agents.scripts.jsearch_enrichment_preview_lib import (  # noqa: E402
    SPAM_PREVIEW_SQL_BY_RUN,
    SPAM_PREVIEW_SQL_RECENT,
    build_extraction_dict,
)

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


def _fmt_bool_or_null(v: bool | None) -> str:
    if v is None:
        return "NULL"
    return "true" if v else "false"


def main() -> None:
    parser = argparse.ArgumentParser(description="Spam tier preview (read-only DB, optional LLM).")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max rows when not using --ingestion-run-id (most recent by normalized_jobs.id DESC).",
    )
    parser.add_argument(
        "--ingestion-run-id",
        type=str,
        default=None,
        help="If set, only jobs from this normalization run (ordered by id ascending).",
    )
    parser.add_argument(
        "--html-out",
        type=Path,
        default=_REPO_ROOT / "agents" / "data" / "rendered" / "spam_preview.html",
        help="Output HTML path (single self-contained file).",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Skip writing HTML; stdout only.",
    )
    args = parser.parse_args()

    if not os.getenv("PYTHON_DATABASE_URL"):
        print("PYTHON_DATABASE_URL is required.", file=sys.stderr)  # noqa: T201
        raise SystemExit(1)

    rows_out: list[tuple[dict[str, Any], SpamPreviewResult]] = []
    degraded = 0

    with session_scope() as session:
        if args.ingestion_run_id:
            result = session.execute(
                text(SPAM_PREVIEW_SQL_BY_RUN),
                {"run_id": args.ingestion_run_id.strip()},
            )
        else:
            result = session.execute(
                text(SPAM_PREVIEW_SQL_RECENT),
                {"lim": args.limit},
            )
        db_rows = result.mappings().all()

    for row in db_rows:
        ext = build_extraction_dict(
            row.get("skills"),
            row.get("tools"),
            row.get("tasks"),
            row.get("responsibilities"),
            row.get("context"),
        )
        extraction_empty = ext is None
        extraction_failed = bool(row.get("extraction_failed"))
        preview = score_spam_preview(
            job_title=str(row.get("job_title") or ""),
            job_description=row.get("job_description"),
            extraction=ext or {},
            extraction_failed=extraction_failed,
            extraction_empty=extraction_empty,
        )
        if preview.degraded:
            degraded += 1

        nj = row.get("normalized_job_id")
        src = row.get("source") or ""
        eid = row.get("external_id") or ""
        score_s = "NULL" if preview.spam_score is None else f"{preview.spam_score:.4f}"
        note_parts = []
        if extraction_failed:
            note_parts.append("extraction_failed")
        if extraction_empty:
            note_parts.append("empty_extraction")
        note = ",".join(note_parts) if note_parts else "—"

        line = (
            f"normalized_job_id={nj}\tsource={src}\texternal_id={eid}\t"
            f"spam_score={score_s}\tis_spam={_fmt_bool_or_null(preview.is_spam)}\t"
            f"tier={preview.tier}\tnote={note}"
        )
        print(line)  # noqa: T201
        rows_out.append((dict(row), preview))

    log.info("spam_preview_degraded_count", count=degraded)
    print(  # noqa: T201
        f"summary\tdegraded_count={degraded}\trows={len(rows_out)}",
        file=sys.stdout,
    )

    if not args.no_html:
        flag_t, rej_t = get_spam_thresholds()
        html = render_spam_preview_html(rows_out, flag_threshold=flag_t, reject_threshold=rej_t)
        args.html_out.parent.mkdir(parents=True, exist_ok=True)
        args.html_out.write_text(html, encoding="utf-8")
        log.info("spam_preview_html_written", path=str(args.html_out))


if __name__ == "__main__":
    main()
