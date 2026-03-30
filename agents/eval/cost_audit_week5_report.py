"""Week 5 Phase 4 — reproducible cost audit metrics (Issue #90).

Queries ``dbo.extracted_intelligence`` and ``dbo.llm_audit_log``, resolves
model tiers for Azure deployment names, prints Markdown tables for pasting
into ``agents/eval/cost_audit_week5.md`` (§3b, §6) or for records.

Usage (repo root, venv, ``PYTHON_DATABASE_URL`` set):

    python -m agents.eval.cost_audit_week5_report
    python -m agents.eval.cost_audit_week5_report --since 2026-03-01

Optional comparison baseline (USD per successful EI row) for the >20% flag::

    python -m agents.eval.cost_audit_week5_report --baseline-per-record 0.0114
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "agents"))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

import structlog
from sqlalchemy import text

from agents.common.data_store.database import get_engine
from agents.eval.cost_tier import resolve_llm_audit_model_tier

log = structlog.get_logger()

_EI_AGG_SQL = """
SELECT
    COUNT(*) FILTER (WHERE NOT extraction_failed) AS success_count,
    COUNT(*) FILTER (WHERE extraction_failed) AS failed_count,
    COUNT(*) AS total_rows,
    COALESCE(SUM(extraction_tokens_used) FILTER (WHERE NOT extraction_failed), 0) AS success_tokens,
    COALESCE(SUM(extraction_cost_usd) FILTER (WHERE NOT extraction_failed), 0) AS success_cost_usd,
    COALESCE(SUM(extraction_tokens_used), 0) AS all_tokens,
    COALESCE(SUM(extraction_cost_usd), 0) AS all_cost_usd
FROM dbo.extracted_intelligence
"""

_EI_TIER_SQL = """
SELECT
    COALESCE(NULLIF(TRIM(extraction_metadata->>'model_tier'), ''), '(missing)') AS model_tier,
    COUNT(*) AS row_count,
    COALESCE(SUM(extraction_cost_usd), 0) AS total_cost_usd,
    COALESCE(SUM(extraction_tokens_used), 0) AS total_tokens
FROM dbo.extracted_intelligence
WHERE NOT extraction_failed
GROUP BY 1
ORDER BY total_cost_usd DESC
"""

_LLM_BY_MODEL_SQL_BASE = """
SELECT
    model,
    COUNT(*) AS call_count,
    COALESCE(SUM(cost_usd), 0) AS total_cost_usd,
    COALESCE(SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)), 0) AS total_tokens
FROM dbo.llm_audit_log
WHERE success = TRUE
"""

_LLM_TOTALS_SQL_BASE = """
SELECT
    COUNT(*) AS call_count,
    COALESCE(SUM(cost_usd), 0) AS total_cost_usd,
    COALESCE(SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)), 0) AS total_tokens
FROM dbo.llm_audit_log
WHERE success = TRUE
"""


def _fmt_money(x: float) -> str:
    return f"${x:.4f}"


def run_report(since: datetime | None, baseline_per_record: float | None) -> str:
    engine = get_engine()
    lines: list[str] = []

    llm_filter = " AND created_at >= :since " if since is not None else ""
    llm_by_model_sql = _LLM_BY_MODEL_SQL_BASE + llm_filter + " GROUP BY model ORDER BY total_cost_usd DESC"
    llm_totals_sql = _LLM_TOTALS_SQL_BASE + llm_filter

    params: dict = {}
    if since is not None:
        params["since"] = since

    with engine.connect() as conn:
        ei = conn.execute(text(_EI_AGG_SQL)).mappings().one()
        ei_tiers = conn.execute(text(_EI_TIER_SQL)).mappings().all()
        llm_models = conn.execute(text(llm_by_model_sql), params).mappings().all()
        llm_tot = conn.execute(text(llm_totals_sql), params).mappings().one()

    sc = int(ei["success_count"] or 0)
    success_cost = float(ei["success_cost_usd"] or 0)
    success_tokens = int(ei["success_tokens"] or 0)
    per_record = (success_cost / sc) if sc else 0.0
    per_record_tok = (success_tokens / sc) if sc else 0.0

    lines.append("### `extracted_intelligence` aggregates (reproducible)\n")
    lines.append("| Metric | Value |")
    lines.append("|--------|------:|")
    lines.append(f"| Success rows (`NOT extraction_failed`) | **{sc}** |")
    lines.append(f"| Failed rows | **{int(ei['failed_count'] or 0)}** |")
    lines.append(f"| Total rows | **{int(ei['total_rows'] or 0)}** |")
    lines.append(f"| Sum `extraction_tokens_used` (success only) | **{success_tokens:,}** |")
    lines.append(f"| Sum `extraction_cost_usd` (success only) | **{_fmt_money(success_cost)}** |")
    lines.append(f"| Avg cost / successful EI row | **{_fmt_money(per_record)}** |")
    lines.append(f"| Avg tokens / successful EI row | **{per_record_tok:,.1f}** |")
    lines.append(f"| Sum tokens (all rows, incl. failed) | **{int(ei['all_tokens'] or 0):,}** |")
    lines.append(f"| Sum cost USD (all rows) | **{_fmt_money(float(ei['all_cost_usd'] or 0))}** |")
    lines.append("")

    lines.append("**`extraction_metadata` → `model_tier` (success rows only):**\n")
    lines.append("| `model_tier` | Rows | Tokens | Cost USD |")
    lines.append("|--------------|-----:|-------:|---------:|")
    for r in ei_tiers:
        lines.append(
            f"| {r['model_tier']} | {int(r['row_count'])} | "
            f"{int(r['total_tokens']):,} | {_fmt_money(float(r['total_cost_usd'] or 0))} |"
        )
    if not ei_tiers:
        lines.append("| _none_ | 0 | 0 | $0.0000 |")
    lines.append("")

    total_llm_cost = float(llm_tot["total_cost_usd"] or 0)
    lines.append("### `llm_audit_log` vs EI (same DB, not 1:1 joinable)\n")
    lines.append("| Source | Calls / rows | Tokens | Cost USD |")
    lines.append("|--------|-------------:|-------:|---------:|")
    lines.append(
        f"| `llm_audit_log` (success) | **{int(llm_tot['call_count'])}** | "
        f"**{int(llm_tot['total_tokens']):,}** | **{_fmt_money(total_llm_cost)}** |"
    )
    lines.append(
        f"| `extracted_intelligence` (success rows) | **{sc}** | "
        f"**{success_tokens:,}** | **{_fmt_money(success_cost)}** |"
    )
    lines.append("")
    lines.append(
        "_EI totals attribute persisted Pass 2 skills cost per job row; audit log includes "
        "all LLM callers (tasks/responsibilities experiments, retries, etc.). Expect mismatch._\n"
    )

    # Resolved tiers
    tier_calls: dict[str, int] = defaultdict(int)
    tier_cost: dict[str, float] = defaultdict(float)
    tier_tokens: dict[str, int] = defaultdict(int)
    for r in llm_models:
        tier = resolve_llm_audit_model_tier(r["model"])
        tier_calls[tier] += int(r["call_count"])
        tier_cost[tier] += float(r["total_cost_usd"] or 0)
        tier_tokens[tier] += int(r["total_tokens"] or 0)

    lines.append("### `llm_audit_log` — resolved model tier (env-aware)\n")
    lines.append(
        "_Resolver: `agents.eval.cost_tier.resolve_llm_audit_model_tier` "
        "(substring haiku/sonnet → `MODEL_TIER_MAP` → deployment env match + "
        "`EXTRACTION_MODEL_TIER`)._\n"
    )
    lines.append("| Resolved tier | Calls | Tokens | Cost USD | Share of LLM cost |")
    lines.append("|---------------|------:|-------:|---------:|------------------:|")
    for tier in sorted(tier_cost.keys(), key=lambda t: -tier_cost[t]):
        share = (tier_cost[tier] / total_llm_cost * 100) if total_llm_cost > 0 else 0.0
        lines.append(
            f"| **{tier}** | {tier_calls[tier]} | {tier_tokens[tier]:,} | "
            f"{_fmt_money(tier_cost[tier])} | **{share:.2f}%** |"
        )
    lines.append("")
    lines.append("**Per deployment name (`model` column):**\n")
    lines.append("| `model` | Resolved tier | Calls | Tokens | Cost USD |")
    lines.append("|---------|---------------|------:|-------:|---------:|")
    for r in llm_models:
        tier = resolve_llm_audit_model_tier(r["model"])
        lines.append(
            f"| `{r['model']}` | {tier} | {int(r['call_count'])} | "
            f"{int(r['total_tokens']):,} | {_fmt_money(float(r['total_cost_usd'] or 0))} |"
        )
    lines.append("")

    if baseline_per_record is not None and baseline_per_record > 0 and sc > 0:
        delta = (per_record - baseline_per_record) / baseline_per_record * 100
        flag = "**ALERT (>20%)**" if abs(delta) > 20 else "within ±20%"
        lines.append("### Informal baseline check (Issue #90)\n")
        lines.append(f"- Baseline (input): **{_fmt_money(baseline_per_record)}** / successful EI row")
        lines.append(f"- Actual: **{_fmt_money(per_record)}** / successful EI row")
        lines.append(f"- Delta: **{delta:+.1f}%** — {flag}")
        lines.append(
            "_Baseline source should be documented (e.g. eval run from `prompt_iteration_log.md`)._\n"
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Print Week 5 cost audit Markdown metrics.")
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="ISO date/datetime; limit llm_audit_log rows to created_at >= this (EI is unfiltered).",
    )
    parser.add_argument(
        "--baseline-per-record",
        type=float,
        default=None,
        help="USD per successful EI row to compare for the >20%% variance flag.",
    )
    args = parser.parse_args()

    since_dt: datetime | None = None
    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since.replace("Z", "+00:00"))
        except ValueError:
            log.error("invalid_since", value=args.since)
            sys.exit(1)

    try:
        out = run_report(since_dt, args.baseline_per_record)
    except Exception as exc:
        log.error("cost_audit_report_failed", error=str(exc))
        raise
    sys.stdout.write(out)
    if not out.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
