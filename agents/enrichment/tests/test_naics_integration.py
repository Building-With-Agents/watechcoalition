#!/usr/bin/env python3
# ruff: noqa: T201 -- manual integration script (not a pytest unit test)
"""End-to-end NAICS classification smoke test against the local dev database.

Steps:
1. Load ``PYTHON_DATABASE_URL`` from repo-root ``.env`` (python-dotenv).
2. Run idempotent migrations so ``dbo.normalized_jobs.naics_code`` exists.
3. Load one ``NormalizedJob`` row (engineering / software / developer title, non-empty description).
4. Show ``dbo.naics`` taxonomy stats via the ``NAICS`` SQLAlchemy model.
5. Call :func:`classify_naics` (uses ``NAICS`` for candidate retrieval internally).
6. Optionally ``UPDATE dbo.normalized_jobs`` with the classified code (skipped with ``--dry-run``).

Usage (repo root, agents venv active)::

    python agents/enrichment/tests/test_naics_integration.py
    python -m agents.enrichment.tests.test_naics_integration
    python agents/enrichment/tests/test_naics_integration.py --job-id 42
    python agents/enrichment/tests/test_naics_integration.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import func, or_, select, update

# tests/ -> enrichment/ -> agents/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env", override=False)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.common.data_store.database import get_engine, session_scope  # noqa: E402
from agents.common.data_store.migrations import run_migrations  # noqa: E402
from agents.common.data_store.models import NAICS, NormalizedJob  # noqa: E402
from agents.enrichment.classifiers.naics_classifier import classify_naics  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="NAICS integration test (normalized_jobs write-back).")
    p.add_argument(
        "--job-id",
        type=int,
        default=None,
        help="Use this normalized_jobs.id (otherwise pick first engineering/software match).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Classify only; do not UPDATE normalized_jobs.",
    )
    return p.parse_args()


def _pick_job(session, job_id: int | None) -> NormalizedJob | None:
    if job_id is not None:
        return session.get(NormalizedJob, job_id)

    title_match = or_(
        func.lower(NormalizedJob.title).contains("engineer"),
        func.lower(NormalizedJob.title).contains("software"),
        func.lower(NormalizedJob.title).contains("developer"),
    )
    stmt = (
        select(NormalizedJob)
        .where(title_match)
        .where(NormalizedJob.description.isnot(None))
        .where(NormalizedJob.description != "")
        .order_by(NormalizedJob.id.asc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def _taxonomy_summary(session) -> tuple[int, list[tuple[str, str]]]:
    total = session.scalar(select(func.count()).select_from(NAICS))
    if total is None:
        total = 0
    rows = session.execute(
        select(NAICS.naics_code, NAICS.title)
        .where(func.length(NAICS.naics_code) == 6)
        .order_by(NAICS.naics_code)
        .limit(8)
    ).all()
    samples = [(str(r[0]), str(r[1])) for r in rows]
    return int(total), samples


def _naics_title(session, code: str) -> str | None:
    row = session.execute(select(NAICS.title).where(NAICS.naics_code == code)).first()
    return str(row[0]) if row else None


def main() -> None:
    args = _parse_args()
    if not os.getenv("PYTHON_DATABASE_URL"):
        print("ERROR: PYTHON_DATABASE_URL is not set (check .env).", file=sys.stderr)
        sys.exit(1)

    engine = get_engine()
    run_migrations(engine)

    with session_scope() as session:
        job = _pick_job(session, args.job_id)
        if job is None:
            print(
                "ERROR: No matching normalized_jobs row (try --job-id or seed data).",
                file=sys.stderr,
            )
            sys.exit(2)

        print("=== Job under test ===")
        print(f"  normalized_job_id: {job.id}")
        print(f"  Job title:         {job.title}")
        print(f"  Company:           {job.company}")
        before = job.naics_code
        print(f"  naics_code (before): {before!r}")

        tax_total, tax_samples = _taxonomy_summary(session)
        print("\n=== dbo.naics (SQLAlchemy NAICS model) ===")
        print(f"  Total NAICS rows: {tax_total}")
        print("  Sample 6-digit codes + industry titles (context the classifier draws from):")
        for code, title in tax_samples:
            print(f"    {code}  {title}")

        print("\n=== LLM classification (classify_naics) ===")
        raw = classify_naics(job.title, job.description, session)
        print(f"  Raw result: {raw!r}")

        if raw == "unknown":
            stored = "unknown"
            sector_label = "unknown"
        else:
            stored = raw.strip() or "unknown"
            sector_label = _naics_title(session, stored) if stored != "unknown" else "unknown"

        print(f"  Stored code:      {stored!r}")
        print(f"  NAICS title:      {sector_label!r}")

        if args.dry_run:
            print("\n--dry-run: skipping UPDATE on dbo.normalized_jobs.")
            return

        session.execute(
            update(NormalizedJob)
            .where(NormalizedJob.id == job.id)
            .values(naics_code=stored)
            .execution_options(synchronize_session=False),
        )
        session.flush()
        session.refresh(job)

        print("\n=== After persist ===")
        print(f"  naics_code (after): {job.naics_code!r}")
        print("Done.")


if __name__ == "__main__":
    main()
