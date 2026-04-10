"""Verify Bryan + Emilio (Pair C) -- Role and seniority classification.

Tests classify_job(), classify_role(), and classify_seniority() with
sample job data. No Azure LLM needed -- classification is deterministic
(token overlap + regex rules).

Usage (from repo root, venv active):
    python agents/scripts/verify_bryan_emilio_classification.py
"""

# ruff: noqa: T201
from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")

# ---------------------------------------------------------------------------
# Test cases: (title, description, expected_seniority_pattern)
# ---------------------------------------------------------------------------
TEST_CASES = [
    {
        "title": "Senior Machine Learning Engineer",
        "description": "Lead a team of ML engineers. 5+ years experience required. Design production pipelines.",
        "expected_seniority": "senior",
    },
    {
        "title": "Junior Data Analyst",
        "description": "Entry-level position. Assist with data cleaning and basic reporting.",
        "expected_seniority": "junior",
    },
    {
        "title": "Software Engineering Intern",
        "description": "Summer internship program. Learn web development fundamentals.",
        "expected_seniority": "intern",
        "is_internship": True,
    },
    {
        "title": "VP of Engineering",
        "description": "Oversee all engineering departments. Report to CTO. 15+ years experience.",
        "expected_seniority": "executive",
    },
    {
        "title": "Full Stack Developer",
        "description": "Build web applications using React and Node.js. 3 years experience preferred.",
        "expected_seniority": "mid",
    },
]


def main() -> int:
    passed = 0
    failed = 0

    # ------------------------------------------------------------------
    # 1. Import classification functions
    # ------------------------------------------------------------------
    print("\n=== 1. Import classification module ===")
    try:
        from agents.enrichment.classification import (
            classify_job,
            classify_role,
            classify_seniority,
        )

        print("  PASS: classification module imported")
        passed += 1
    except ImportError as e:
        print(f"  FAIL: cannot import classification -- {e}")
        print("  Make sure agents/enrichment/classification.py exists on your branch.")
        return 1

    # ------------------------------------------------------------------
    # 2. Test classify_seniority() with known inputs
    # ------------------------------------------------------------------
    print("\n=== 2. classify_seniority() ===")
    seniority_pass = 0
    seniority_fail = 0
    for tc in TEST_CASES:
        result = classify_seniority(
            tc["title"],
            tc["description"],
            None,  # no extraction data
            is_internship=tc.get("is_internship", False),
        )
        expected = tc["expected_seniority"]
        status = "PASS" if result == expected else "WARN"
        if result == expected:
            seniority_pass += 1
        else:
            seniority_fail += 1
        print(f'  {status}: "{tc["title"]}" -> {result} (expected: {expected})')

    if seniority_pass >= 3:
        print(f"  PASS: classify_seniority -- {seniority_pass}/{len(TEST_CASES)} correct")
        passed += 1
    else:
        print(f"  FAIL: classify_seniority -- only {seniority_pass}/{len(TEST_CASES)} correct")
        failed += 1

    # ------------------------------------------------------------------
    # 3. Test classify_role() with reference table data
    # ------------------------------------------------------------------
    print("\n=== 3. classify_role() -- with lookup tables ===")
    try:
        from sqlalchemy import text as sa_text

        from agents.common.data_store.database import session_scope

        with session_scope() as session:
            tech_rows = session.execute(sa_text("SELECT id, title FROM dbo.technology_areas ORDER BY title")).fetchall()
            sector_rows = session.execute(
                sa_text("SELECT industry_sector_id, sector_title FROM dbo.industry_sectors ORDER BY sector_title")
            ).fetchall()

        tech_areas = [(str(r[0]), r[1]) for r in tech_rows]
        sectors = [(str(r[0]), r[1]) for r in sector_rows]
        print(f"  Loaded {len(tech_areas)} technology areas, {len(sectors)} industry sectors")

        if len(tech_areas) == 0:
            print("  WARN: technology_areas table is empty -- classification will return 'unclassified'")

        for tc in TEST_CASES[:3]:
            corpus = f"{tc['title']} {tc['description']}"
            role = classify_role(tc["title"], corpus, tech_areas, sectors)
            print(f'  "{tc["title"]}" -> role: {role}')

        print("  PASS: classify_role runs without error")
        passed += 1

    except Exception as e:
        print(f"  FAIL: classify_role error -- {e}")
        print("  Check: is your local Postgres running? Is PYTHON_DATABASE_URL set?")
        failed += 1

    # ------------------------------------------------------------------
    # 4. Test classify_job() (combines role + seniority)
    # ------------------------------------------------------------------
    print("\n=== 4. classify_job() -- combined ===")
    try:
        for tc in TEST_CASES[:3]:
            role, seniority = classify_job(
                tc["title"],
                tc["description"],
                None,
                tech_areas if "tech_areas" in dir() else [],
                sectors if "sectors" in dir() else [],
                is_internship=tc.get("is_internship", False),
            )
            print(f'  "{tc["title"]}" -> role={role}, seniority={seniority}')

        print("  PASS: classify_job runs without error")
        passed += 1
    except Exception as e:
        print(f"  FAIL: classify_job error -- {e}")
        failed += 1

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 40}")
    print(f"Bryan + Emilio verification: {passed} passed, {failed} failed")
    print(f"{'=' * 40}\n")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
