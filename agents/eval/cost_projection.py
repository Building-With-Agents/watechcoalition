"""Cost Projection Script — Week 4.

Reads from dbo.llm_audit_log (populated by real LLM calls via llm_adapter.complete()
and by taxonomy Step 4 embedding calls via log_extraction_event in taxonomy._embed_texts_azure,
issue #108: agent_name=taxonomy-resolver, model=text-embedding-3-small),
separates Pass 1 (pattern matching, free) from Pass 2 (LLM inference + embeddings, paid),
groups costs by model tier (sonnet vs haiku vs other), projects at 1k / 10k / 100k
postings, and writes agents/eval/cost_model_week4.md.

Usage (from repo root, venv activated, .env loaded):
    python -m agents.eval.cost_projection [--output agents/eval/cost_model_week4.md]

Pass 1 vs Pass 2 distinction:
    Pass 1 — pattern matching / rule-based extraction. No LLM call, cost = $0.
             Tracked via ExtractionMetadata.pass1_tool_count.
    Pass 2 — LLM extraction of skill dimensions plus Step 4 embedding API calls. Cost tracked in llm_audit_log.
             Rows where success=TRUE and cost_usd > 0 are Pass 2 calls.

    Rows with cost_usd = 0 and success=TRUE are treated as Pass 1 (stub/pattern).

Embedding vs chat: see report section "Embedding vs chat"; embedding rows use tier **other**
in the model-tier table when the model is not haiku/sonnet.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "agents"))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

import structlog
from sqlalchemy import text

from agents.common.data_store.database import get_engine

log = structlog.get_logger()

_OUTPUT_PATH = Path(__file__).parent / "cost_model_week4.md"

_SCALE_POINTS = [1_000, 10_000, 100_000]

_QUERY = """
SELECT
    model,
    CASE
        WHEN model ILIKE '%haiku%' THEN 'haiku'
        WHEN model ILIKE '%sonnet%' THEN 'sonnet'
        ELSE 'other'
    END AS model_tier,
    COUNT(*) AS call_count,
    SUM(input_tokens)  AS total_input_tokens,
    SUM(output_tokens) AS total_output_tokens,
    SUM(token_count)   AS total_tokens,
    SUM(cost_usd)      AS total_cost_usd,
    AVG(cost_usd)      AS avg_cost_per_call,
    AVG(latency_ms)    AS avg_latency_ms
FROM dbo.llm_audit_log
WHERE success = TRUE
GROUP BY model, model_tier
ORDER BY total_cost_usd DESC;
"""

_DIMENSION_QUERY = """
SELECT
    agent_name,
    COUNT(*) AS call_count,
    SUM(cost_usd) AS total_cost_usd,
    AVG(cost_usd) AS avg_cost_per_call
FROM dbo.llm_audit_log
WHERE success = TRUE AND cost_usd > 0
GROUP BY agent_name
ORDER BY total_cost_usd DESC;
"""

# Issue #108: split taxonomy Step 4 embeddings from chat completions in totals.
_EMBED_VS_CHAT_QUERY = """
SELECT
    SUM(
        CASE WHEN agent_name = 'taxonomy-resolver' OR model ILIKE '%embedding%' THEN 1 ELSE 0 END
    ) AS embedding_calls,
    SUM(
        CASE WHEN agent_name = 'taxonomy-resolver' OR model ILIKE '%embedding%' THEN cost_usd ELSE 0 END
    ) AS embedding_cost_usd,
    SUM(
        CASE WHEN NOT (agent_name = 'taxonomy-resolver' OR model ILIKE '%embedding%') THEN 1 ELSE 0 END
    ) AS chat_calls,
    SUM(
        CASE WHEN NOT (agent_name = 'taxonomy-resolver' OR model ILIKE '%embedding%') THEN cost_usd ELSE 0 END
    ) AS chat_cost_usd
FROM dbo.llm_audit_log
WHERE success = TRUE;
"""


def run(output_path: Path = _OUTPUT_PATH) -> None:
    engine = get_engine()

    with engine.connect() as conn:
        tier_rows = conn.execute(text(_QUERY)).fetchall()
        dimension_rows = conn.execute(text(_DIMENSION_QUERY)).fetchall()
        embed_chat_row = conn.execute(text(_EMBED_VS_CHAT_QUERY)).fetchone()

    if not tier_rows:
        log.warning("cost_projection_no_data", message="llm_audit_log is empty — run real extractions first.")
        _write_empty_report(output_path)
        return

    # Separate Pass 1 (free) from Pass 2 (paid)
    pass1_calls = sum(r.call_count for r in tier_rows if r.avg_cost_per_call == 0)
    pass2_rows = [r for r in tier_rows if r.avg_cost_per_call > 0]

    total_pass2_calls = sum(r.call_count for r in pass2_rows)
    total_pass2_cost = sum(r.total_cost_usd for r in pass2_rows)
    avg_cost_per_record = total_pass2_cost / total_pass2_calls if total_pass2_calls else 0.0

    lines: list[str] = []
    lines.append("# Cost Model — Week 4\n")
    lines.append(f"*Generated from `dbo.llm_audit_log` ({sum(r.call_count for r in tier_rows)} total calls)*\n")
    lines.append("")

    lines.append("## Pass 1 vs Pass 2 Cost Breakdown\n")
    lines.append("| Pass | Description | Call Count | Cost |")
    lines.append("|---|---|---|---|")
    lines.append(f"| Pass 1 | Pattern matching (free) | {pass1_calls} | $0.00 |")
    lines.append(f"| Pass 2 | LLM inference (paid) | {total_pass2_calls} | ${total_pass2_cost:.6f} |")
    lines.append("")

    lines.append("## Average Cost Per Record (by Model Tier)\n")
    lines.append("| Model | Tier | Calls | Avg Input Tokens | Avg Output Tokens | Avg Cost/Call | Avg Latency (ms) |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in pass2_rows:
        avg_in = (r.total_input_tokens or 0) / r.call_count
        avg_out = (r.total_output_tokens or 0) / r.call_count
        lines.append(
            f"| {r.model} | {r.model_tier} | {r.call_count} "
            f"| {avg_in:.0f} | {avg_out:.0f} "
            f"| ${r.avg_cost_per_call:.6f} | {r.avg_latency_ms:.0f} |"
        )
    lines.append("")

    lines.append("## Cost Projections at Scale\n")
    lines.append(f"*Avg Pass 2 cost per posting: ${avg_cost_per_record:.6f}*\n")
    lines.append("| Scale | Pass 1 Cost | Pass 2 Cost (all tiers) | Total |")
    lines.append("|---|---|---|---|")
    for scale in _SCALE_POINTS:
        pass2_total = avg_cost_per_record * scale
        lines.append(f"| {scale:,} postings | $0.00 | ${pass2_total:.2f} | ${pass2_total:.2f} |")
    lines.append("")

    # Per-tier projections
    if len(pass2_rows) > 1:
        lines.append("### Per-Tier Projections\n")
        lines.append("| Scale | " + " | ".join(r.model_tier for r in pass2_rows) + " |")
        lines.append("|---|" + "---|" * len(pass2_rows))
        for scale in _SCALE_POINTS:
            cols = [f"${r.avg_cost_per_call * scale:.2f}" for r in pass2_rows]
            lines.append(f"| {scale:,} | " + " | ".join(cols) + " |")
        lines.append("")

    if dimension_rows:
        lines.append("## Most Expensive Extraction Dimensions\n")
        lines.append("| Agent / Dimension | Calls | Total Cost | Avg Cost/Call |")
        lines.append("|---|---|---|---|")
        for r in dimension_rows:
            lines.append(f"| {r.agent_name} | {r.call_count} | ${r.total_cost_usd:.6f} | ${r.avg_cost_per_call:.6f} |")
        most_expensive = dimension_rows[0]
        lines.append(f"\n**Most expensive dimension:** `{most_expensive.agent_name}` "
                     f"at ${most_expensive.avg_cost_per_call:.6f}/call\n")

    if embed_chat_row is not None:
        ec = int(embed_chat_row.embedding_calls or 0)
        cc = int(embed_chat_row.chat_calls or 0)
        e_cost = float(embed_chat_row.embedding_cost_usd or 0)
        c_cost = float(embed_chat_row.chat_cost_usd or 0)
        lines.append("## Embedding vs chat (`llm_audit_log`)\n")
        lines.append(
            "Step 4 taxonomy embeddings are logged as `agent_name=taxonomy-resolver` and/or "
            "models matching `%embedding%` (issue #108). Chat completions are all other successful rows.\n"
        )
        lines.append("| Kind | Calls | Total cost (USD) |")
        lines.append("|---|---|---|")
        lines.append(f"| Step 4 embeddings | {ec} | ${e_cost:.6f} |")
        lines.append(f"| Chat completions | {cc} | ${c_cost:.6f} |")
        lines.append("")
        lines.append(
            "*Note:* The **Average Cost Per Record (by Model Tier)** table above includes embedding rows "
            "under tier **other** when the model name is not haiku/sonnet.\n"
        )
        lines.append("")

    lines.append("## Cost Optimization Opportunities\n")
    lines.append("- Route lower-complexity dimensions (tools verification, context) to Haiku instead of Sonnet.")
    lines.append("- Cache repeated skill patterns across similar job postings (Pass 1 expansion).")
    lines.append("- Batch multiple dimensions per LLM call to reduce per-call overhead.")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("cost_model_written", path=str(output_path))


def _write_empty_report(output_path: Path) -> None:
    """Write a placeholder report when no audit log data is available."""
    content = """# Cost Model — Week 4

*No data yet — llm_audit_log is empty.*

Run real LLM extractions (Week 4 full implementation) then re-run this script:

```bash
python -m agents.eval.cost_projection
```

## Expected Sections (once data is available)

- Pass 1 vs Pass 2 Cost Breakdown
- Average Cost Per Record (by Model Tier)
- Cost Projections at Scale (1k / 10k / 100k)
- Most Expensive Extraction Dimension
- Embedding vs chat (`llm_audit_log`, issue #108)
- Cost Optimization Opportunities
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    log.info("cost_model_empty_template_written", path=str(output_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Week 4 cost projection report.")
    parser.add_argument(
        "--output",
        type=Path,
        default=_OUTPUT_PATH,
        help="Path to write cost_model_week4.md (default: agents/eval/cost_model_week4.md)",
    )
    args = parser.parse_args()
    run(output_path=args.output)
