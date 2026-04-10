# ruff: noqa: T201
"""Summarize LLM spend from dbo.llm_audit_log and project cost for N jobs.

Usage (repo root, venv activated):

    python agents/scripts/llm_audit_cost_report.py
    python agents/scripts/llm_audit_cost_report.py --project-jobs 1000

Reads PYTHON_DATABASE_URL from .env.

Notes:
- ``extracted_intelligence.extraction_cost_usd`` is the per-job rollup from Skills Extraction
  (tasks + responsibilities + skills + pass-1 metadata). Use AVG for projection.
- ``llm_audit_log`` rows include taxonomy batch calls and enrichment (dedup embeddings, spam
  preview) which are not strictly one row per job; enrichment projection uses total
  enrichment-related cost divided by current ``job_postings`` count as a rough per-job add-on.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text  # noqa: E402

from agents.common.data_store.database import get_engine  # noqa: E402
from agents.common.env import load_repo_root_dotenv  # noqa: E402

load_repo_root_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM audit cost summary and projection")
    parser.add_argument(
        "--project-jobs",
        type=int,
        default=1000,
        help="Raw normalized job count to project (default: 1000)",
    )
    args = parser.parse_args()

    engine = get_engine()
    with engine.connect() as conn:
        print("=== dbo.llm_audit_log — by agent_name ===\n")
        rows = conn.execute(
            text(
                """
                SELECT agent_name,
                       COUNT(*) AS calls,
                       COALESCE(SUM(cost_usd), 0) AS sum_cost_usd,
                       COALESCE(SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)), 0) AS sum_tokens
                FROM dbo.llm_audit_log
                GROUP BY agent_name
                ORDER BY sum_cost_usd DESC NULLS LAST, calls DESC
                """
            )
        ).fetchall()
        if not rows:
            print("(no rows in llm_audit_log)")
        else:
            print(f"{'agent_name':<40} {'calls':>8} {'sum_cost_usd':>14} {'sum_tokens':>12}")
            print("-" * 78)
            total_calls = 0
            total_cost = 0.0
            total_tok = 0
            for r in rows:
                print(f"{r[0]:<40} {r[1]:>8} {float(r[2]):>14.6f} {r[3]:>12}")
                total_calls += r[1]
                total_cost += float(r[2] or 0)
                total_tok += r[3] or 0
            print("-" * 78)
            print(f"{'TOTAL':<40} {total_calls:>8} {total_cost:>14.6f} {total_tok:>12}")

        print("\n=== dbo.extracted_intelligence — extraction_cost_usd ===\n")
        row = conn.execute(
            text(
                """
                SELECT COUNT(*) AS n,
                       COALESCE(SUM(extraction_cost_usd), 0) AS sum_cost,
                       COALESCE(AVG(NULLIF(extraction_cost_usd, 0)), 0) AS avg_cost_nonzero
                FROM dbo.extracted_intelligence
                """
            )
        ).one()
        n_ext, sum_ext, avg_nz = int(row[0]), float(row[1]), float(row[2])
        print(f"Rows: {n_ext}")
        print(f"Sum extraction_cost_usd: {sum_ext:.6f}")
        print(f"Avg extraction_cost_usd (excluding zeros): {avg_nz:.6f}")

        print("\n=== Normalized jobs — description fill rate (for projection) ===\n")
        row2 = conn.execute(
            text(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN description IS NULL OR TRIM(description) = '' THEN 1 ELSE 0 END) AS empty_desc
                FROM dbo.normalized_jobs
                """
            )
        ).one()
        total_nj, empty_nj = int(row2[0]), int(row2[1] or 0)
        if total_nj == 0:
            fill_rate = 0.54
            print("No normalized_jobs rows; using default 54% with-description rate for projection.")
        else:
            fill_rate = (total_nj - empty_nj) / total_nj
            print(f"normalized_jobs: {total_nj} total, {empty_nj} empty description")
            print(f"Fraction with description (eligible for Pass-2 LLM): {fill_rate:.1%}")

        print("\n=== Enrichment LLM (audit) vs job_postings ===\n")
        row3 = conn.execute(
            text(
                """
                SELECT COALESCE(SUM(l.cost_usd), 0)
                FROM dbo.llm_audit_log l
                WHERE l.agent_name LIKE 'enrichment%'
                """
            )
        ).scalar()
        enrich_cost = float(row3 or 0)
        jp = conn.execute(text("SELECT COUNT(*) FROM dbo.job_postings")).scalar()
        jp_n = int(jp or 0)
        enrich_per_job = enrich_cost / jp_n if jp_n else 0.0
        print(f"Sum cost_usd (agent_name LIKE 'enrichment%%'): {enrich_cost:.6f}")
        print(f"job_postings count: {jp_n}")
        print(f"Implied enrichment LLM cost per posting (rough): {enrich_per_job:.6f}")

        row_audit_skills = conn.execute(
            text(
                """
                SELECT COALESCE(SUM(cost_usd), 0)
                FROM dbo.llm_audit_log
                WHERE agent_name IN (
                    'skills-extraction-tasks',
                    'skills-extraction-responsibilities',
                    'skills-extraction-agent',
                    'taxonomy-resolver'
                )
                """
            )
        ).scalar()
        audit_skills_total = float(row_audit_skills or 0)

        print(f"\n=== Projection — {args.project_jobs} raw jobs through normalize → extract → enrich ===\n")
        jobs_with_text = int(round(args.project_jobs * fill_rate))
        avg_ex = avg_nz if avg_nz > 0 else (sum_ext / n_ext if n_ext else 0.0)
        proj_extract = jobs_with_text * avg_ex
        proj_enrich = args.project_jobs * enrich_per_job if enrich_per_job > 0 else 0.0
        if jp_n == 0:
            proj_enrich = 0.0
            print("(job_postings is empty — enrichment per-job estimate skipped.)")
        print(f"Assumed jobs needing Pass-2 extraction: ~{jobs_with_text} ({fill_rate:.0%} of {args.project_jobs})")
        print(f"Avg extraction_cost_usd per extracted row (DB column): {avg_ex:.6f}")
        print(f"Projected skills extraction (from extraction_cost_usd only): ~${proj_extract:.2f}")

        proj_audit = 0.0
        if n_ext > 0 and audit_skills_total > 0:
            audit_per_extracted = audit_skills_total / n_ext
            proj_audit = jobs_with_text * audit_per_extracted
            print(
                f"Historical audit cost (tasks+resp+skills+taxonomy) / extracted rows: "
                f"${audit_skills_total:.4f} / {n_ext} = ${audit_per_extracted:.4f} per row"
            )
            print(
                f"Projected skills path (audit-based, same mix): ~${proj_audit:.2f} "
                f"(often closer to actual LLM spend than extraction_cost_usd alone)"
            )

        print(f"Projected enrichment LLM (linear on job count): ~${proj_enrich:.2f}")
        print(f"Projected subtotal (extraction_cost_usd method + enrichment): ~${proj_extract + proj_enrich:.2f}")
        if proj_audit > 0:
            print(f"Projected subtotal (audit-based skills + enrichment): ~${proj_audit + proj_enrich:.2f}")
        print(
            "\nNote: extraction_cost_usd may not include every billed token path; "
            "prefer the audit-based line when it differs materially."
        )


if __name__ == "__main__":
    main()
