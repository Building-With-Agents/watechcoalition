"""
Run a single job through the Skills Extraction Agent and generate an HTML timeline.

Usage:
  python -m agents.scripts.run_skills_extraction_timeline
  python -m agents.scripts.run_skills_extraction_timeline --mock

--mock: Use mocked extract_skills (no Azure LLM). Produces example metrics in the HTML.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import time
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

# Repo root on sys.path for agents
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.common.event_envelope import EventEnvelope
from agents.skills_extraction.agent import (
    ExtractionResult,
    ExtractionStore,
    SkillsExtractionAgent,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _payload_summary(payload: dict, max_skills: int = 5, max_tools: int = 5) -> dict:
    """Compact summary safe for HTML display (no secrets)."""
    out = {
        "event_type": payload.get("event_type"),
        "batch_id": payload.get("batch_id"),
        "job_ids": payload.get("job_ids"),
        "title": payload.get("title"),
        "company": payload.get("company"),
        "skills_count": payload.get("skills_count"),
        "tools_count": payload.get("tools_count"),
        "taxonomy_coverage": payload.get("taxonomy_coverage"),
        "extraction_cost_usd": payload.get("extraction_cost_usd"),
        "failed_count": payload.get("failed_count"),
        "llm_provider": payload.get("llm_provider"),
        "llm_model": payload.get("llm_model"),
        "llm_call_logged": payload.get("llm_call_logged"),
        "skills_extraction_alert": payload.get("skills_extraction_alert"),
    }
    skills = payload.get("skills") or []
    if skills:
        out["skills_preview"] = [s.get("label") or s.get("name") for s in skills[:max_skills]]
        if len(skills) > max_skills:
            out["skills_preview"].append(f"+ {len(skills) - max_skills} more")
    tools = payload.get("tools") or []
    if tools:
        out["tools_preview"] = [t.get("tool_name") or t.get("label") for t in tools[:max_tools]]
        if len(tools) > max_tools:
            out["tools_preview"].append(f"+ {len(tools) - max_tools} more")
    return out


ALL_METRIC_KEYS = (
    "tokens_used",
    "latency_ms",
    "extraction_cost_usd",
    "taxonomy_coverage",
    "skills_count",
    "tools_count",
    "failed_count",
    "record_count",
    "llm_provider",
    "llm_model",
    "llm_call_logged",
    "skills_extraction_alert",
)


def _normalize_metrics(metrics: dict, fill_none: bool = True) -> dict:
    """Ensure all standard metric keys are present; use None for missing when fill_none."""
    out = dict(metrics)
    if fill_none:
        for k in ALL_METRIC_KEYS:
            if k not in out:
                out[k] = None
    return out


def _metrics_from_results(results: Sequence[ExtractionResult]) -> dict:
    """Aggregate metrics from ExtractionResult list."""
    total_tokens = sum(getattr(r, "extraction_tokens_used", 0) or 0 for r in results)
    total_cost = sum(getattr(r, "extraction_cost_usd", 0.0) or 0.0 for r in results)
    total_skills = sum(len(r.skills) for r in results)
    total_tools = sum(len(r.tools) for r in results)
    failed = sum(1 for r in results if r.extraction_status != "success")
    any_alert = any(getattr(r, "alert_skills_extraction", False) for r in results)
    any_llm_called = any((getattr(r, "extraction_tokens_used", 0) or 0) > 0 for r in results)
    skills_with_taxonomy = sum(
        1
        for r in results
        for s in r.skills
        if isinstance(s, dict) and (s.get("esco_uri") or s.get("is_genai_extension"))
    )
    taxonomy_coverage = (skills_with_taxonomy / total_skills) if total_skills else 0.0
    return _normalize_metrics({
        "tokens_used": total_tokens,
        "extraction_cost_usd": round(total_cost, 6),
        "skills_count": total_skills,
        "tools_count": total_tools,
        "failed_count": failed,
        "skills_extraction_alert": any_alert,
        "record_count": len(results),
        "taxonomy_coverage": round(taxonomy_coverage, 4),
        "llm_provider": "azure-openai" if any_llm_called else "stub",
        "llm_model": "sonnet" if any_llm_called else "stub",
        "llm_call_logged": any_llm_called,
    }, fill_none=True)


def _source_span_cell(span: dict | None) -> str:
    """Format source_span for a table cell: text; field; start–end."""
    if not span or not isinstance(span, dict):
        return "—"
    text = span.get("text", "")
    field = span.get("field_source", "")
    start = span.get("start_char", "")
    end = span.get("end_char", "")
    return f"{html.escape(str(text))}; field: {html.escape(str(field))}; chars {start}–{end}"


def _render_tools_table(tools_full: list[dict]) -> str:
    """Render full tools list with source_span as HTML table."""
    if not tools_full:
        return "<p class=\"desc\">No tools extracted.</p>"
    parts = [
        '<h3 class="subsection">Pass 1: Tools extracted</h3>',
        '<table class="data-table"><thead><tr><th>Tool</th><th>Category</th><th>Confidence</th><th>Source span</th></tr></thead><tbody>',
    ]
    for t in tools_full:
        span = t.get("source_span") if isinstance(t.get("source_span"), dict) else {}
        parts.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td class=\"span-cell\">{}</td></tr>".format(
                html.escape(str(t.get("tool_name") or t.get("label") or "")),
                html.escape(str(t.get("category", ""))),
                t.get("confidence", ""),
                _source_span_cell(span),
            )
        )
    parts.append("</tbody></table>")
    return "\n    ".join(parts)


def _source_span_cell_with_debug(span: dict | None, span_auto_corrected: bool = False, original_end_char: int | None = None) -> str:
    """Format source_span for a table cell; append debug note when span was auto-corrected."""
    cell = _source_span_cell(span)
    if span_auto_corrected and original_end_char is not None and span and isinstance(span, dict):
        corrected_end = span.get("end_char", "")
        cell += ' <span class="debug-note" title="LLM returned invalid end_char; corrected to match text length">[span corrected: end_char {} → {}]</span>'.format(
            original_end_char, corrected_end
        )
    return cell


def _render_skills_table(skills_full: list[dict]) -> str:
    """Render full skills list with source_span as HTML table."""
    if not skills_full:
        return "<p class=\"desc\">No skills extracted.</p>"
    parts = [
        '<h3 class="subsection">Pass 2: Skills extracted</h3>',
        '<table class="data-table"><thead><tr><th>Label</th><th>Type</th><th>Confidence</th><th>Required</th><th>ESCO / GenAI</th><th>Source span</th></tr></thead><tbody>',
    ]
    for s in skills_full:
        if not isinstance(s, dict):
            continue
        span = s.get("source_span") if isinstance(s.get("source_span"), dict) else {}
        esco = s.get("esco_uri") or ""
        genai = "Yes" if s.get("is_genai_extension") else ""
        if esco or genai:
            tax = f"{html.escape(str(esco))}" + (" (GenAI)" if genai else "")
        else:
            tax = "—"
        span_cell = _source_span_cell_with_debug(
            span,
            span_auto_corrected=s.get("span_auto_corrected", False),
            original_end_char=s.get("original_end_char"),
        )
        parts.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td class=\"span-cell\">{}</td></tr>".format(
                html.escape(str(s.get("label") or s.get("name") or "")),
                html.escape(str(s.get("type", ""))),
                s.get("confidence", ""),
                "Yes" if s.get("required_flag") else ("No" if s.get("required_flag") is False else "—"),
                tax,
                span_cell,
            )
        )
    parts.append("</tbody></table>")
    return "\n    ".join(parts)


def build_timeline_html(steps: list[dict], output_path: Path, run_context: dict | None = None) -> None:
    """Write a self-contained HTML file with chronological timeline and metrics."""
    run_context = run_context or {}
    posting = run_context.get("posting") or {}
    tools_full = run_context.get("tools_full") or []
    skills_full = run_context.get("skills_full") or []

    html_parts = [
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Skills Extraction Agent — Run Timeline</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 960px; margin: 0 auto; padding: 1.5rem; background: #0f172a; color: #e2e8f0; }
    h1 { color: #38bdf8; margin-bottom: 0.5rem; }
    .subtitle { color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem; }
    .posting { margin: 1.25rem 0; padding: 1rem; background: #1e293b; border-radius: 8px; border-left: 4px solid #64748b; }
    .posting h2 { font-size: 1rem; color: #94a3b8; margin: 0 0 0.75rem 0; }
    .posting .field { margin-bottom: 0.75rem; }
    .posting .field-label { font-weight: 600; color: #38bdf8; font-size: 0.85rem; }
    .posting .field-body { color: #cbd5e1; font-size: 0.9rem; white-space: pre-wrap; }
    .step { margin: 1.25rem 0; padding: 1rem; background: #1e293b; border-radius: 8px; border-left: 4px solid #38bdf8; }
    .step h2 { font-size: 1rem; color: #38bdf8; margin: 0 0 0.25rem 0; }
    .step .desc { color: #94a3b8; font-size: 0.85rem; margin-bottom: 0.75rem; }
    .step h3.subsection { font-size: 0.9rem; color: #94a3b8; margin: 1rem 0 0.5rem 0; }
    .metrics { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 0.5rem; margin: 0.5rem 0; }
    .metric { background: #334155; padding: 0.4rem 0.6rem; border-radius: 4px; font-size: 0.8rem; }
    .metric .key { color: #94a3b8; }
    .metric .val { color: #f1f5f9; font-weight: 600; }
    pre { background: #0f172a; padding: 0.75rem; border-radius: 6px; overflow: auto; font-size: 0.8rem; color: #cbd5e1; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin: 0.5rem 0; }
    .data-table th, .data-table td { padding: 0.4rem 0.5rem; text-align: left; border-bottom: 1px solid #334155; }
    .data-table th { color: #94a3b8; }
    .data-table .span-cell { max-width: 280px; word-break: break-word; }
    .debug-note { font-size: 0.75rem; color: #94a3b8; margin-left: 0.25rem; }
  </style>
</head>
<body>
  <h1>Skills Extraction Agent — Run Timeline</h1>
  <p class="subtitle">Chronological steps and metrics. Generated at """
        + _utc_now()
        + """</p>
"""
    ]

    # Job posting section
    if posting and any(posting.get(k) for k in ("title", "company", "description", "requirements", "responsibilities")):
        html_parts.append('  <section class="posting">\n')
        html_parts.append('    <h2>Job posting (input)</h2>\n')
        for field_label, key in (
            ("Title", "title"),
            ("Company", "company"),
            ("Description", "description"),
            ("Requirements", "requirements"),
            ("Responsibilities", "responsibilities"),
        ):
            val = posting.get(key) or ""
            html_parts.append(f'    <div class="field"><span class="field-label">{field_label}</span><div class="field-body">{html.escape(str(val))}</div></div>\n')
        html_parts.append("  </section>\n")

    for i, step in enumerate(steps, 1):
        label = step.get("label", f"Step {i}")
        desc = step.get("description", "")
        payload_summary = step.get("payload_summary")
        metrics = step.get("metrics") or {}
        ts = step.get("timestamp", "")

        html_parts.append('  <section class="step">\n')
        html_parts.append(f'    <h2>{i}. {html.escape(label)}</h2>\n')
        if ts:
            html_parts.append(f'    <p class="desc">At {ts}</p>\n')
        if desc:
            html_parts.append(f'    <p class="desc">{html.escape(desc)}</p>\n')

        if metrics:
            html_parts.append('    <div class="metrics">\n')
            for k, v in metrics.items():
                if v is None:
                    v = "N/A"
                elif isinstance(v, bool):
                    v = "Yes" if v else "No"
                html_parts.append(f'      <div class="metric"><span class="key">{html.escape(str(k))}</span>: <span class="val">{html.escape(str(v))}</span></div>\n')
            html_parts.append("    </div>\n")

        if payload_summary:
            html_parts.append("    <pre>" + html.escape(json.dumps(payload_summary, indent=2, default=str)) + "</pre>\n")

        # Full tools and skills tables on "Extraction completed & store saved" step
        if label == "Extraction completed & store saved" and (tools_full or skills_full):
            html_parts.append("    " + _render_tools_table(tools_full) + "\n")
            html_parts.append("    " + _render_skills_table(skills_full) + "\n")

        html_parts.append("  </section>\n")

    html_parts.append("</body>\n</html>\n")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(html_parts), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run skills extraction and generate HTML timeline")
    parser.add_argument("--mock", action="store_true", help="Mock extract_skills (no LLM call)")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "eval" / "skills_extraction_run.html",
        help="Output HTML path",
    )
    args = parser.parse_args()

    steps: list[dict] = []

    # Synthetic NormalizationComplete-style event
    input_payload = {
        "event_type": "NormalizationComplete",
        "batch_id": "timeline-run-1",
        "title": "Senior Platform Engineer",
        "company": "Acme Corp",
        "description": "Build and maintain backend services in Python and Go. Use Docker and Kubernetes. Lead cross-functional initiatives.",
        "requirements": "5+ years Python, SQL, REST APIs. Experience with AWS or GCP.",
        "responsibilities": "Own services end-to-end. Collaborate with product and data teams.",
        "source": "timeline-script",
        "external_id": "job-timeline-1",
    }

    input_envelope = EventEnvelope(
        correlation_id="timeline-correlation-1",
        agent_id="normalization-agent",
        payload=input_payload,
    )

    # Step 1: Input event received
    step1_metrics = {k: None for k in ALL_METRIC_KEYS}
    step1_metrics["batch_id"] = input_payload.get("batch_id")
    step1_metrics["job"] = input_payload.get("title")
    steps.append({
        "timestamp": _utc_now(),
        "label": "Input event received",
        "description": "NormalizationComplete event passed to Skills Extraction Agent.",
        "payload_summary": _payload_summary(input_payload),
        "metrics": step1_metrics,
    })

    # Custom store to capture results and record "Extraction completed & store saved"
    saved_results: list = []
    extraction_start: float | None = None

    class TimelineExtractionStore(ExtractionStore):
        def save(self, results: Sequence[ExtractionResult]) -> None:
            saved_results.extend(results)
            # Handoff step: Pass 1 (tools) complete → input to Pass 2 (skills)
            pass1_tool_names = []
            if results:
                pass1_tool_names = [t.tool_name for t in results[0].tools]
            handoff_metrics = {k: None for k in ALL_METRIC_KEYS}
            handoff_metrics["tools_count"] = len(pass1_tool_names)
            steps.append({
                "timestamp": _utc_now(),
                "label": "Pass 1 (tools) complete → input to Pass 2 (skills)",
                "description": "Tool names produced by Pass 1 and passed as pass1_tools into the skills extractor.",
                "payload_summary": {
                    "pass1_tool_names": pass1_tool_names,
                    "pass1_tool_count": len(pass1_tool_names),
                },
                "metrics": handoff_metrics,
            })
            # Extraction completed & store saved
            metrics = _metrics_from_results(results)
            if extraction_start is not None:
                metrics["latency_ms"] = round((time.perf_counter() - extraction_start) * 1000, 2)
            payload_preview = {}
            if results:
                r = results[0]
                payload_preview = {
                    "job_id": r.work_item.job_id,
                    "title": r.work_item.title,
                    "company": r.work_item.company,
                    "skills_count": len(r.skills),
                    "tools_count": len(r.tools),
                    "extraction_status": r.extraction_status,
                }
            steps.append({
                "timestamp": _utc_now(),
                "label": "Extraction completed & store saved",
                "description": "Pass 1 (tools) and Pass 2 (skills) ran. Results persisted.",
                "payload_summary": payload_preview,
                "metrics": metrics,
            })

    store = TimelineExtractionStore()
    agent = SkillsExtractionAgent(extraction_store=store)

    extraction_start = time.perf_counter()
    if args.mock:
        from unittest.mock import patch

        from agents.common.types import SkillRecord, SpanRecord

        mock_skill = SkillRecord(
            label="Python",
            type="Technical",
            confidence=0.92,
            esco_uri="http://data.europa.eu/esco/skill/example",
            source_span=SpanRecord(
                text="Python", field_source="requirements", start_char=0, end_char=6
            ),
        )
        mock_meta = {
            "extraction_failed": False,
            "tokens_used": 150,
            "cost_usd": 0.003,
            "latency_ms": 1200,
            "success": True,
            "provider": "azure-openai",
            "model": "sonnet",
        }
        with patch("agents.skills_extraction.agent.extract_skills") as mock_extract:
            mock_extract.return_value = ([mock_skill], mock_meta)
            out_envelope = agent.process(input_envelope)
    else:
        out_envelope = agent.process(input_envelope)

    # Step 4: SkillsExtracted event emitted (use saved_results for tokens/cost when available)
    out_payload = out_envelope.payload
    total_run_ms = (time.perf_counter() - extraction_start) * 1000
    step3_metrics = _normalize_metrics({
        "latency_ms": round(total_run_ms, 2),
        "extraction_cost_usd": out_payload.get("extraction_cost_usd"),
        "taxonomy_coverage": out_payload.get("taxonomy_coverage"),
        "skills_count": out_payload.get("skills_count"),
        "tools_count": out_payload.get("tools_count"),
        "failed_count": out_payload.get("failed_count"),
        "llm_provider": out_payload.get("llm_provider"),
        "llm_model": out_payload.get("llm_model"),
        "llm_call_logged": out_payload.get("llm_call_logged"),
        "skills_extraction_alert": out_payload.get("skills_extraction_alert"),
        "record_count": len(saved_results) if saved_results else None,
    }, fill_none=True)
    if saved_results:
        agg = _metrics_from_results(saved_results)
        step3_metrics["tokens_used"] = agg.get("tokens_used")
        step3_metrics["extraction_cost_usd"] = agg.get("extraction_cost_usd")
    steps.append({
        "timestamp": _utc_now(),
        "label": "SkillsExtracted event emitted",
        "description": "Agent returned the final event with payload and metrics.",
        "payload_summary": _payload_summary(out_payload),
        "metrics": step3_metrics,
    })

    # Run context for HTML: posting, full tools, full skills
    posting = {
        "title": input_payload.get("title"),
        "company": input_payload.get("company"),
        "description": input_payload.get("description"),
        "requirements": input_payload.get("requirements"),
        "responsibilities": input_payload.get("responsibilities"),
    }
    tools_full = []
    skills_full = []
    if saved_results:
        r = saved_results[0]
        tools_full = [t.model_dump() for t in r.tools]
        skills_full = list(r.skills)  # already list of dicts

    run_context = {
        "posting": posting,
        "tools_full": tools_full,
        "skills_full": skills_full,
    }
    build_timeline_html(steps, args.out, run_context=run_context)
    print(f"Timeline written to {args.out}")
    print(f"Open in browser: file://{args.out.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
