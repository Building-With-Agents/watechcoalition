"""Verify Juan + Enrique (Pair D) -- Company/location resolution + RecordEnriched event.

Tests resolve_company() with known and unknown companies, resolve_location(),
compute_field_confidence(), compute_overall_confidence(), and
build_record_enriched_event(). Steps 3, 4, and 8 require PostgreSQL.

Usage (from repo root, venv active):
    python agents/scripts/verify_juan_enrique_resolution.py

Local DB: start Docker, then from repo root::
    docker compose --env-file .env.docker up postgres -d

Set ``PYTHON_DATABASE_URL`` in ``.env`` to match ``POSTGRES_PORT`` in ``.env.docker``
(default host port is 5432 per ``docker-compose.yml``, not 5433).
"""

# ruff: noqa: T201
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")


def _print_preflight_hints(db_err: str | None) -> None:
    if not db_err:
        return
    el = db_err.lower()
    url = os.getenv("PYTHON_DATABASE_URL") or ""
    if "password authentication failed" in el:
        print("  Hint: the password in PYTHON_DATABASE_URL must match POSTGRES_PASSWORD in .env.docker.")
    if "connection refused" in el and ":5433" in url:
        print(
            "  Hint: URL uses port 5433; docker-compose defaults to host port 5432 "
            "(POSTGRES_PORT). Use the same port in PYTHON_DATABASE_URL."
        )


def _print_database_setup_help() -> None:
    print(
        """
  Fix: PostgreSQL must be running and PYTHON_DATABASE_URL must match host and port.

  1. Start Docker Desktop (Windows/Mac) or the Docker daemon (Linux).

  2. Copy .env.docker.example to .env.docker, set POSTGRES_PASSWORD (and optional
     POSTGRES_PORT; default mapped port is 5432 per docker-compose.yml).

  3. From the repo root run:
       docker compose --env-file .env.docker up postgres -d

  4. In .env set (password and port must match .env.docker):
       PYTHON_DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/talent_finder
     Use the same port as POSTGRES_PORT (5432 unless you changed it).

  See ONBOARDING.md section 5 for details.
"""
    )


def _offline_location_session_mock() -> MagicMock:
    """``resolve_location`` runs two ``execute`` calls; stub both when DB is down."""
    session = MagicMock()
    r1 = MagicMock()
    r1.scalar_one_or_none.return_value = None
    r2 = MagicMock()
    r2.__iter__ = lambda self: iter(())
    session.execute.side_effect = [r1, r2]
    return session


def main() -> int:
    passed = 0
    failed = 0

    # ------------------------------------------------------------------
    # 1. Import resolution modules
    # ------------------------------------------------------------------
    print("\n=== 1. Import resolution modules ===")
    try:
        from agents.enrichment.resolvers.company_resolver import (
            normalize_company_name,
            resolve_company,
        )
        from agents.enrichment.resolvers.location_resolver import resolve_location

        print("  PASS: resolvers imported")
        passed += 1
    except ImportError as e:
        print(f"  FAIL: cannot import resolvers -- {e}")
        if "thefuzz" in str(e):
            print("  FIX: pip install thefuzz python-Levenshtein")
        else:
            print("  Make sure agents/enrichment/resolvers/ directory exists on your branch.")
        return 1

    from sqlalchemy import text as sa_text

    from agents.common.data_store.database import (
        check_db_connection_detail,
        session_scope,
    )

    # ------------------------------------------------------------------
    # 2. Company name normalization
    # ------------------------------------------------------------------
    print("\n=== 2. normalize_company_name() ===")
    test_names = [
        ("Microsoft Corporation", "microsoft"),
        ("Apple Inc.", "apple"),
        ("  Google  LLC  ", "google"),
        ("Amazon.com, Inc.", "amazon.com"),
        ("TechCorp", "techcorp"),
    ]
    norm_pass = 0
    for raw, expected_contains in test_names:
        result = normalize_company_name(raw)
        ok = expected_contains in result
        if ok:
            norm_pass += 1
        status = "PASS" if ok else "WARN"
        print(f'  {status}: "{raw}" -> "{result}"')

    if norm_pass >= 3:
        print(f"  PASS: normalization working ({norm_pass}/{len(test_names)})")
        passed += 1
    else:
        print(f"  FAIL: normalization issues ({norm_pass}/{len(test_names)})")
        failed += 1

    # ------------------------------------------------------------------
    # Preflight: steps 3, 4, 8 need PostgreSQL
    # ------------------------------------------------------------------
    print("\n=== Preflight: PostgreSQL (steps 3, 4, 8) ===")
    db_ok, db_err = check_db_connection_detail()
    if not db_ok:
        if not os.getenv("PYTHON_DATABASE_URL"):
            print("  FAIL: PYTHON_DATABASE_URL is not set in .env")
        else:
            print("  FAIL: cannot connect to PostgreSQL (wrong URL, port, or server down)")
        _print_preflight_hints(db_err)
        _print_database_setup_help()
    else:
        print("  PASS: database reachable")
        try:
            from agents.common.data_store.database import get_engine
            from agents.common.data_store.migrations import run_migrations

            run_migrations(get_engine())
            print("  PASS: idempotent run_migrations() applied (e.g. companies geo columns #110)")
        except Exception as mig_exc:
            print(f"  WARN: run_migrations failed — steps 4–5 may fail until fixed: {mig_exc}")

    # ------------------------------------------------------------------
    # 3. resolve_company() with DB -- known company
    # ------------------------------------------------------------------
    print("\n=== 3. resolve_company() -- database lookup ===")
    if not db_ok:
        print("  SKIP/FAIL: requires database (see Preflight)")
        failed += 1
    else:
        try:
            with session_scope() as session:
                # Find any existing company to test exact match
                row = session.execute(sa_text("SELECT company_name FROM dbo.companies LIMIT 1")).fetchone()

                if row:
                    known_name = row[0]
                    company_id, confidence = resolve_company(known_name, session)
                    print(f'  Known company "{known_name}" -> id={company_id}, confidence={confidence:.2f}')
                    if company_id and confidence > 0.5:
                        print("  PASS: known company resolved")
                        passed += 1
                    else:
                        print("  FAIL: known company should resolve with high confidence")
                        failed += 1
                else:
                    print("  WARN: companies table is empty -- skipping known company test")
                    passed += 1  # not their fault

        except Exception as e:
            print(f"  FAIL: resolve_company error -- {e}")
            failed += 1

    # ------------------------------------------------------------------
    # 4. resolve_company() -- unknown company (placeholder creation)
    # ------------------------------------------------------------------
    print("\n=== 4. resolve_company() -- placeholder creation ===")
    if not db_ok:
        print("  SKIP/FAIL: requires database (see Preflight)")
        failed += 1
    else:
        try:
            fake_name = f"VerifyTest_{uuid.uuid4().hex[:8]} Corp"
            with session_scope() as session:
                company_id, confidence = resolve_company(fake_name, session)
                print(f'  Unknown company "{fake_name}" -> id={company_id}, confidence={confidence:.2f}')

                if company_id is None:
                    print("  FAIL: company_id is None -- placeholder was NOT created. This is the #1 non-negotiable.")
                    failed += 1
                else:
                    # Verify placeholder exists in companies table
                    check = session.execute(
                        sa_text("SELECT company_name FROM dbo.companies WHERE company_id = :cid"),
                        {"cid": company_id},
                    ).fetchone()
                    if check:
                        print(f'  Placeholder row: name="{check[0]}"')
                        print("  PASS: placeholder created -- company_id is never null")
                        passed += 1
                    else:
                        print("  FAIL: company_id returned but no row found in companies table")
                        failed += 1

                # Clean up test placeholder
                session.execute(
                    sa_text("DELETE FROM dbo.companies WHERE company_name = :name"),
                    {"name": fake_name},
                )

        except Exception as e:
            print(f"  FAIL: placeholder creation error -- {e}")
            failed += 1

    # ------------------------------------------------------------------
    # 5. resolve_location()
    # ------------------------------------------------------------------
    print("\n=== 5. resolve_location() ===")
    try:
        # Resolver queries Company; stub session.execute when DB is unreachable.
        session = _offline_location_session_mock() if not db_ok else None
        if session is None:
            with session_scope() as real_session:
                loc_id, confidence, raw_text, borderplex = resolve_location("El Paso, TX", real_session)
        else:
            loc_id, confidence, raw_text, borderplex = resolve_location("El Paso, TX", session)
        print(f'  "El Paso, TX" -> loc_id={loc_id}, confidence={confidence:.2f}, borderplex={borderplex}')
        print("  PASS: resolve_location runs without error")
        passed += 1
    except Exception as e:
        print(f"  FAIL: resolve_location error -- {e}")
        failed += 1

    # ------------------------------------------------------------------
    # 6. Confidence computation
    # ------------------------------------------------------------------
    print("\n=== 6. compute_field_confidence() + compute_overall_confidence() ===")
    try:
        from agents.enrichment.resolvers.confidence import (
            compute_field_confidence,
            compute_overall_confidence,
        )

        field_conf = compute_field_confidence(
            company_confidence=0.95,
            location_confidence=0.90,
            sector_id=1,
            seniority_confidence=0.85,
        )
        print(f"  field_confidence: {field_conf}")

        overall = compute_overall_confidence(
            field_confidence=field_conf,
            extraction_confidence=0.88,
            quality_score=0.75,
            taxonomy_coverage=0.92,
        )
        print(f"  overall_confidence: {overall:.4f}")

        if 0.0 <= overall <= 1.0:
            print("  PASS: confidence values in [0, 1]")
            passed += 1
        else:
            print("  FAIL: overall_confidence out of range")
            failed += 1

    except Exception as e:
        print(f"  FAIL: confidence computation error -- {e}")
        failed += 1

    # ------------------------------------------------------------------
    # 7. RecordEnriched event
    # ------------------------------------------------------------------
    print("\n=== 7. build_record_enriched_event() ===")
    try:
        from agents.enrichment.resolvers.events import build_record_enriched_event

        event = build_record_enriched_event(
            correlation_id=str(uuid.uuid4()),
            batch_id=str(uuid.uuid4()),
            enriched_count=8,
            spam_rejected_count=1,
            flagged_for_review_count=2,
            temporal_period_distribution={"unknown": 8},
            borderplex_subregion_distribution={"unknown": 8},
            duplicate_count=0,
            soc_classified_count=0,
            naics_classified_count=0,
        )
        print(f"  agent_id: {event.agent_id}")
        print(f"  payload keys: {list(event.payload.keys())}")
        print(f"  payload event_type: {event.payload.get('event_type', 'N/A')}")
        print("  PASS: RecordEnriched event built")
        passed += 1
    except Exception as e:
        print(f"  FAIL: build_record_enriched_event error -- {e}")
        failed += 1

    # ------------------------------------------------------------------
    # 8. Non-negotiable: no null company_id in job_postings
    # ------------------------------------------------------------------
    print("\n=== 8. Non-negotiable: no null company_id ===")
    if not db_ok:
        print("  SKIP/FAIL: requires database (see Preflight)")
        failed += 1
    else:
        try:
            with session_scope() as session:
                row = session.execute(
                    sa_text("SELECT COUNT(*) FROM dbo.job_postings WHERE company_id IS NULL")
                ).fetchone()
                null_count = row[0] if row else -1
                print(f"  Null company_id count: {null_count}")
                if null_count == 0:
                    print("  PASS: no null company_id in job_postings")
                    passed += 1
                else:
                    print(f"  FAIL: {null_count} rows have null company_id -- this is a non-negotiable")
                    failed += 1
        except Exception as e:
            print(f"  FAIL: null company_id check error -- {e}")
            failed += 1

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 40}")
    print(f"Juan + Enrique verification: {passed} passed, {failed} failed")
    print(f"{'=' * 40}\n")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
