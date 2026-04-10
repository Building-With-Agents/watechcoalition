#!/usr/bin/env python3
# ruff: noqa: T201 -- manual integration script (not a pytest unit test)
"""End-to-end EmployerProfile classification smoke test against the dev database.

Steps:
1. Load ``PYTHON_DATABASE_URL`` from repo-root ``.env`` (python-dotenv).
2. Run idempotent migrations so ``dbo.normalized_jobs.employer_metadata`` exists.
3. Load one ``NormalizedJob`` row (``--job-id`` or first row with non-empty description).
4. Call :func:`build_employer_profile` (LLM + ``dbo.companies`` exact match for ``is_known_employer``).
5. Optionally ``UPDATE dbo.normalized_jobs.employer_metadata`` (skipped with ``--dry-run``).

Usage (repo root, agents venv active)::

    python agents/enrichment/tests/test_employer_integration.py
    python -m agents.enrichment.tests.test_employer_integration
    python agents/enrichment/tests/test_employer_integration.py --job-id 42
    python agents/enrichment/tests/test_employer_integration.py --dry-run

    # Real LLM, but replace description with strong signals (often non-unknown):
    python agents/enrichment/tests/test_employer_integration.py --job-id 11 --rich-demo

    # No LLM — use a JSON file (recommended on Windows / PowerShell):
    python agents/enrichment/tests/test_employer_integration.py --job-id 11 --inject-profile-file agents/enrichment/tests/fixtures/employer_inject.sample.json

    # PowerShell: avoid inline JSON (commas/quotes break parsing); use a variable:
    #   $j = '{"company_size":"enterprise","ai_maturity_signal":"ai_adopting","sector":"technology"}'
    #   python agents/enrichment/tests/test_employer_integration.py --job-id 11 --inject-profile $j

    # Real LLM on several rows (longest combined job text first):
    python agents/enrichment/tests/test_employer_integration.py --llm-scan --llm-scan-limit 10 --min-description-chars 400

    # If scan finds no rows, try 0 (all jobs) or lower threshold — text may live in requirements, not description.
    python agents/enrichment/tests/test_employer_integration.py --llm-scan --min-description-chars 0 --llm-scan-limit 20
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import func, select

# tests/ -> enrichment/ -> agents/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env", override=False)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.common.data_store.database import get_engine, session_scope  # noqa: E402
from agents.common.data_store.migrations import run_migrations  # noqa: E402
from agents.common.data_store.models import Company, NormalizedJob  # noqa: E402
from agents.common.types.job_profile import EmployerProfile  # noqa: E402
from agents.enrichment.classifiers.employer_classifier import (  # noqa: E402
    build_employer_profile,
    persist_employer_metadata,
    registry_has_exact_company_name,
)

# Canned text designed to surface company_size / sector / ai_maturity (real LLM runs).
_RICH_DEMO_DESCRIPTION = """
Global Enterprise Financial Corp is a Fortune 500 financial services firm with over 12,000
employees worldwide. We operate retail banking, commercial lending, and digital payments across
North America. This role is in our core technology organization building APIs and platforms
at scale.

We are actively deploying machine learning and generative AI in production (fraud detection,
customer chat, document understanding) and partner closely with our MLOps and data science
teams. You will work on systems that serve millions of customers daily.
""".strip()

_RICH_DEMO_COMPANY = "Global Enterprise Financial Corp"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="EmployerProfile integration (normalized_jobs.employer_metadata).")
    p.add_argument(
        "--job-id",
        type=int,
        default=None,
        help="Use this normalized_jobs.id (otherwise pick first row with a non-empty description).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Classify only; do not UPDATE normalized_jobs.",
    )
    p.add_argument(
        "--rich-demo",
        action="store_true",
        help=(
            "For classification only: use a canned company name + description with explicit "
            "Fortune 500 / headcount / finance / GenAI signals (real LLM; usually non-unknown)."
        ),
    )
    p.add_argument(
        "--inject-profile",
        type=str,
        default=None,
        metavar="JSON",
        help=("Skip the LLM. Inline JSON (fragile in PowerShell). Prefer --inject-profile-file."),
    )
    p.add_argument(
        "--inject-profile-file",
        type=Path,
        default=None,
        metavar="PATH",
        help="Skip the LLM. Read UTF-8 JSON object from this file (reliable on Windows).",
    )
    p.add_argument(
        "--llm-scan",
        action="store_true",
        help=(
            "Run build_employer_profile (real LLM) on multiple normalized_jobs rows. "
            "Does not combine with --job-id, --rich-demo, or inject options."
        ),
    )
    p.add_argument(
        "--llm-scan-limit",
        type=int,
        default=8,
        metavar="N",
        help="With --llm-scan: max rows to classify (default 8).",
    )
    p.add_argument(
        "--min-description-chars",
        type=int,
        default=200,
        metavar="N",
        help=(
            "With --llm-scan: minimum character count for title + description + requirements + "
            "responsibilities combined (default 200). Use 0 to include all rows."
        ),
    )
    p.add_argument(
        "--llm-scan-order",
        choices=("length_desc", "id_desc", "id_asc"),
        default="length_desc",
        help="With --llm-scan: row order (default length_desc = longest text first).",
    )
    p.add_argument(
        "--persist-scan",
        action="store_true",
        help="With --llm-scan: write employer_metadata for each scanned row (omit for read-only).",
    )
    return p.parse_args()


def _parse_inject_json(raw: str) -> dict:
    s = raw.strip().lstrip("\ufeff")
    try:
        injected = json.loads(s)
    except json.JSONDecodeError as exc:
        preview = repr(s[:160])
        print(f"ERROR: Invalid JSON: {exc}", file=sys.stderr)
        print(f"  Received (first 160 chars, repr): {preview}", file=sys.stderr)
        print(
            "  Hint: On PowerShell, inline JSON often breaks. Use either:\n"
            "    --inject-profile-file profile.json\n"
            '  or: $j = \'{"company_size":"enterprise","ai_maturity_signal":"ai_adopting","sector":"technology"}\'\n'
            "       python ... --inject-profile $j",
            file=sys.stderr,
        )
        raise SystemExit(3) from exc
    if not isinstance(injected, dict):
        print("ERROR: Injected JSON must be a JSON object {...}.", file=sys.stderr)
        raise SystemExit(3)
    return injected


def _pick_job(session, job_id: int | None) -> NormalizedJob | None:
    if job_id is not None:
        return session.get(NormalizedJob, job_id)

    stmt = (
        select(NormalizedJob)
        .where(NormalizedJob.description.isnot(None))
        .where(NormalizedJob.description != "")
        .order_by(NormalizedJob.id.asc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def _companies_count(session) -> int:
    n = session.scalar(select(func.count()).select_from(Company))
    return int(n or 0)


def _employer_scan_text_score_expr():
    """Chars available for employer LLM: title + description + requirements + responsibilities."""
    body = (
        func.coalesce(func.length(NormalizedJob.description), 0)
        + func.coalesce(func.length(NormalizedJob.requirements), 0)
        + func.coalesce(func.length(NormalizedJob.responsibilities), 0)
    )
    return body + func.length(NormalizedJob.title)


def _employer_context_for_llm(job: NormalizedJob) -> str:
    """Same text shape the scan filters on, passed as the first arg to build_employer_profile."""
    title = (job.title or "").strip()
    chunks: list[str] = []
    if title:
        chunks.append(f"Job title: {title}")
    for block in (job.description, job.requirements, job.responsibilities):
        if isinstance(block, str) and block.strip():
            chunks.append(block.strip())
    return "\n\n".join(chunks)


def _print_llm_scan_diagnostics(session, min_chars: int) -> None:
    score = _employer_scan_text_score_expr()
    total = int(session.scalar(select(func.count()).select_from(NormalizedJob)) or 0)
    max_score = session.scalar(select(func.max(score)).select_from(NormalizedJob))
    max_desc = session.scalar(
        select(func.max(func.coalesce(func.length(NormalizedJob.description), 0))).select_from(NormalizedJob)
    )
    meeting = int(session.scalar(select(func.count()).select_from(NormalizedJob).where(score >= min_chars)) or 0)
    print("\n=== Diagnostics (why no rows?) ===", file=sys.stderr)
    print(f"  normalized_jobs total rows:     {total}", file=sys.stderr)
    print(f"  rows with score >= {min_chars}:        {meeting}", file=sys.stderr)
    print(
        "  max combined text score:        "
        f"{max_score if max_score is not None else 0}  (title+description+requirements+responsibilities)",
        file=sys.stderr,
    )
    print(
        f"  max description length only:    {max_desc if max_desc is not None else 0}",
        file=sys.stderr,
    )
    print(
        "  Tip: Text may be in requirements/responsibilities. Try --min-description-chars 0 or a lower number.",
        file=sys.stderr,
    )


def _fetch_jobs_for_llm_scan(
    session,
    *,
    limit: int,
    min_description_chars: int,
    order: str,
) -> list[NormalizedJob]:
    score = _employer_scan_text_score_expr()
    stmt = select(NormalizedJob).where(score >= min_description_chars)
    if order == "length_desc":
        stmt = stmt.order_by(score.desc(), NormalizedJob.id.desc())
    elif order == "id_desc":
        stmt = stmt.order_by(NormalizedJob.id.desc())
    else:
        stmt = stmt.order_by(NormalizedJob.id.asc())
    stmt = stmt.limit(limit)
    return list(session.execute(stmt).scalars().all())


def _has_non_unknown_llm_fields(profile: EmployerProfile) -> bool:
    return profile.company_size != "unknown" or profile.ai_maturity_signal != "unknown" or profile.sector != "unknown"


def _run_llm_scan(args: argparse.Namespace) -> None:
    print("=== LLM scan (real Azure call per row) ===")
    print(
        f"  limit={args.llm_scan_limit}  min_combined_text_chars={args.min_description_chars}  "
        f"order={args.llm_scan_order}"
    )
    persist = args.persist_scan and not args.dry_run
    if args.persist_scan and args.dry_run:
        print("  WARN: --persist-scan skipped because --dry-run is set.", file=sys.stderr)
    if not persist:
        print("  (read-only: not writing employer_metadata; add --persist-scan to save)")

    with session_scope() as session:
        jobs = _fetch_jobs_for_llm_scan(
            session,
            limit=args.llm_scan_limit,
            min_description_chars=args.min_description_chars,
            order=args.llm_scan_order,
        )
        if not jobs:
            print("\nNo rows matched your threshold.", file=sys.stderr)
            _print_llm_scan_diagnostics(session, args.min_description_chars)
            return

        rich_count = 0
        for job in jobs:
            corpus = _employer_context_for_llm(job)
            profile = build_employer_profile(corpus, job.company or "", session)
            if _has_non_unknown_llm_fields(profile):
                rich_count += 1

            print("\n---")
            print(f"id={job.id}  corpus_chars={len(corpus)}  title={job.title!r}  company={job.company!r}")
            print(json.dumps(profile.model_dump(mode="json"), indent=2))

            if persist:
                persist_employer_metadata(session, profile, normalized_job_id=job.id)
                session.flush()

        print("\n=== Scan summary ===")
        print(
            f"  Classified {len(jobs)} job(s); {rich_count} had at least one non-unknown "
            f"among company_size / ai_maturity_signal / sector."
        )
        print("  (is_known_employer is from dbo.companies exact match, not the LLM.)")
    print("Done.")


def main() -> None:
    args = _parse_args()
    if args.inject_profile is not None and args.inject_profile_file is not None:
        print("ERROR: Use only one of --inject-profile and --inject-profile-file.", file=sys.stderr)
        sys.exit(2)
    injecting = args.inject_profile is not None or args.inject_profile_file is not None
    if args.llm_scan:
        if args.job_id is not None:
            print("ERROR: Do not use --job-id with --llm-scan.", file=sys.stderr)
            sys.exit(2)
        if injecting:
            print("ERROR: Do not use inject options with --llm-scan.", file=sys.stderr)
            sys.exit(2)
        if args.rich_demo:
            print("ERROR: Do not use --rich-demo with --llm-scan.", file=sys.stderr)
            sys.exit(2)
        if args.llm_scan_limit < 1:
            print("ERROR: --llm-scan-limit must be >= 1.", file=sys.stderr)
            sys.exit(2)
        if args.min_description_chars < 0:
            print("ERROR: --min-description-chars must be >= 0.", file=sys.stderr)
            sys.exit(2)
    if not os.getenv("PYTHON_DATABASE_URL"):
        print("ERROR: PYTHON_DATABASE_URL is not set (check .env).", file=sys.stderr)
        sys.exit(1)

    engine = get_engine()
    run_migrations(engine)

    if args.llm_scan:
        _run_llm_scan(args)
        return

    with session_scope() as session:
        job = _pick_job(session, args.job_id)
        if job is None:
            print(
                "ERROR: No matching normalized_jobs row (try --job-id or seed data).",
                file=sys.stderr,
            )
            sys.exit(2)

        desc = job.description if isinstance(job.description, str) else None
        company_for_profile = job.company or ""

        if injecting and args.rich_demo:
            print("WARN: --rich-demo ignored when inject profile options are set.", file=sys.stderr)

        if args.rich_demo and not injecting:
            desc = _RICH_DEMO_DESCRIPTION
            company_for_profile = _RICH_DEMO_COMPANY

        print("=== Job under test ===")
        print(f"  normalized_job_id: {job.id}")
        print(f"  title:             {job.title}")
        print(f"  company (row):     {job.company}")
        if args.rich_demo and not injecting:
            print("  company (classify):  [rich-demo] " + company_for_profile)
        print(
            f"  employer_metadata (before): {json.dumps(job.employer_metadata, indent=2) if job.employer_metadata else repr(job.employer_metadata)}"
        )

        co_count = _companies_count(session)
        print("\n=== dbo.companies ===")
        print(f"  Row count: {co_count}  (is_known_employer uses exact normalized name match)")

        if injecting:
            print("\n=== Injected profile (no LLM) ===")
            if args.inject_profile_file is not None:
                path = args.inject_profile_file
                if not path.is_file():
                    print(f"ERROR: File not found: {path}", file=sys.stderr)
                    sys.exit(3)
                injected = _parse_inject_json(path.read_text(encoding="utf-8"))
            else:
                assert args.inject_profile is not None
                injected = _parse_inject_json(args.inject_profile)
            is_known = registry_has_exact_company_name(session, job.company or "")
            merged = {**EmployerProfile().model_dump(mode="json"), **injected, "is_known_employer": is_known}
            profile = EmployerProfile.model_validate(merged)
        else:
            label = "LLM classification (build_employer_profile)"
            if args.rich_demo:
                label += " [rich-demo text]"
            print(f"\n=== {label} ===")
            profile = build_employer_profile(desc, company_for_profile, session)
        payload = profile.model_dump(mode="json")
        print(json.dumps(payload, indent=2))

        if args.dry_run:
            print("\n--dry-run: skipping UPDATE on dbo.normalized_jobs.")
            return

        persist_employer_metadata(session, profile, normalized_job_id=job.id)
        session.flush()
        session.refresh(job)

        print("\n=== After persist ===")
        print(
            f"  employer_metadata (after): {json.dumps(job.employer_metadata, indent=2) if job.employer_metadata else repr(job.employer_metadata)}"
        )
        print("Done.")


if __name__ == "__main__":
    main()
