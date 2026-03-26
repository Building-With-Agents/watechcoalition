"""Verify Juan + Enrique (Pair D) -- Company/location resolution + RecordEnriched event.

Tests resolve_company() with known and unknown companies, resolve_location(),
compute_field_confidence(), compute_overall_confidence(), and
build_record_enriched_event(). Requires local Postgres running.

Usage (from repo root, venv active):
    python agents/scripts/verify_juan_enrique_resolution.py
"""
# ruff: noqa: T201
from __future__ import annotations

import sys
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")


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
        print(f"  {status}: \"{raw}\" -> \"{result}\"")

    if norm_pass >= 3:
        print(f"  PASS: normalization working ({norm_pass}/{len(test_names)})")
        passed += 1
    else:
        print(f"  FAIL: normalization issues ({norm_pass}/{len(test_names)})")
        failed += 1

    # ------------------------------------------------------------------
    # 3. resolve_company() with DB -- known company
    # ------------------------------------------------------------------
    print("\n=== 3. resolve_company() -- database lookup ===")
    try:
        from agents.common.data_store.database import session_scope
        from sqlalchemy import text as sa_text

        with session_scope() as session:
            # Find any existing company to test exact match
            row = session.execute(
                sa_text("SELECT company_name FROM dbo.companies LIMIT 1")
            ).fetchone()

            if row:
                known_name = row[0]
                company_id, confidence = resolve_company(known_name, session)
                print(f"  Known company \"{known_name}\" -> id={company_id}, confidence={confidence:.2f}")
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
    try:
        from agents.common.data_store.database import session_scope
        from sqlalchemy import text as sa_text

        fake_name = f"VerifyTest_{uuid.uuid4().hex[:8]} Corp"
        with session_scope() as session:
            company_id, confidence = resolve_company(fake_name, session)
            print(f"  Unknown company \"{fake_name}\" -> id={company_id}, confidence={confidence:.2f}")

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
                    print(f"  Placeholder row: name=\"{check[0]}\"")
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
        from agents.common.data_store.database import session_scope

        with session_scope() as session:
            loc_id, confidence, raw_text, borderplex = resolve_location("El Paso, TX", session)
            print(f"  \"El Paso, TX\" -> loc_id={loc_id}, confidence={confidence:.2f}, borderplex={borderplex}")
            print(f"  PASS: resolve_location runs without error")
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
        )
        print(f"  agent_id: {event.agent_id}")
        print(f"  payload keys: {list(event.payload.keys())}")
        print(f"  payload event_type: {event.payload.get('event_type', 'N/A')}")
        print(f"  PASS: RecordEnriched event built")
        passed += 1
    except Exception as e:
        print(f"  FAIL: build_record_enriched_event error -- {e}")
        failed += 1

    # ------------------------------------------------------------------
    # 8. Non-negotiable: no null company_id in job_postings
    # ------------------------------------------------------------------
    print("\n=== 8. Non-negotiable: no null company_id ===")
    try:
        from agents.common.data_store.database import session_scope
        from sqlalchemy import text as sa_text

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
    print(f"\n{'='*40}")
    print(f"Juan + Enrique verification: {passed} passed, {failed} failed")
    print(f"{'='*40}\n")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
