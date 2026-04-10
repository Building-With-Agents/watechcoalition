"""Verify Angel + Fabian (Pair A) -- Eval harness + cost audit queries.

Runs the extraction eval in stub mode (no Azure needed) and checks
that the ground truth file loads, the harness produces metrics, and
the llm_audit_log table is queryable for cost audit.

Usage (from repo root, venv active):
    python agents/scripts/verify_angel_fabian_eval.py
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


def main() -> int:
    passed = 0
    failed = 0

    # ------------------------------------------------------------------
    # 1. Ground truth file exists and loads
    # ------------------------------------------------------------------
    print("\n=== 1. Ground truth file ===")
    gt_path = _REPO_ROOT / "agents" / "eval" / "extraction_ground_truth.json"
    if gt_path.exists():
        from agents.eval.extraction_eval_core import load_ground_truth

        data = load_ground_truth(gt_path)
        print(f"  PASS: ground truth loaded -- {len(data)} records")
        passed += 1
    else:
        print(f"  FAIL: ground truth file not found at {gt_path}")
        failed += 1

    # ------------------------------------------------------------------
    # 2. Eval harness runs in stub mode (no Azure needed)
    # ------------------------------------------------------------------
    print("\n=== 2. Eval harness (stub mode) ===")
    try:
        from agents.eval.extraction_eval_core import print_console, run_eval_dataset

        result = run_eval_dataset(
            data[:5],  # limit to 5 for speed
            mode="stub",
            limit=5,
            write_artifacts=False,
        )
        print_console(result.console_lines)
        print(f"  PASS: eval harness ran -- {len(result.console_lines)} output lines")
        passed += 1
    except Exception as e:
        print(f"  FAIL: eval harness error -- {e}")
        failed += 1

    # ------------------------------------------------------------------
    # 3. Cost audit query (llm_audit_log table)
    # ------------------------------------------------------------------
    print("\n=== 3. Cost audit -- llm_audit_log table ===")
    try:
        from sqlalchemy import text as sa_text

        from agents.common.data_store.database import session_scope

        with session_scope() as session:
            row = session.execute(sa_text("SELECT COUNT(*) AS cnt FROM dbo.llm_audit_log")).fetchone()
            count = row[0] if row else 0
            print(f"  llm_audit_log rows: {count}")
            if count > 0:
                rows = session.execute(
                    sa_text(
                        "SELECT agent_name, model, COUNT(*) AS calls, "
                        "SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)) AS tokens, "
                        "SUM(COALESCE(cost_usd, 0)) AS cost "
                        "FROM dbo.llm_audit_log "
                        "GROUP BY agent_name, model ORDER BY cost DESC"
                    )
                ).fetchall()
                for r in rows:
                    print(f"    {r[0]} ({r[1]}): {r[2]} calls, {r[3]} tokens, ${r[4]:.4f}")
            print(f"  PASS: llm_audit_log queryable ({count} rows)")
            passed += 1
    except Exception as e:
        print(f"  FAIL: cost audit query error -- {e}")
        failed += 1

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'=' * 40}")
    print(f"Angel + Fabian verification: {passed} passed, {failed} failed")
    print(f"{'=' * 40}\n")
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
