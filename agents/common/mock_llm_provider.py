"""Mock LLM provider for local development and trace generation.

Returns realistic extraction results from ground truth data
(agents/eval/extraction_ground_truth.json) without calling any real LLM.
Generates proper token counts, costs, and latency for Langfuse traces.

Usage: set LLM_PROVIDER=mock in .env
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

_GROUND_TRUTH: list[dict] | None = None
_GT_INDEX = 0

TSchema = TypeVar("TSchema", bound=BaseModel)

# ---------------------------------------------------------------------------
# Ground truth loading
# ---------------------------------------------------------------------------


def _load_ground_truth() -> list[dict]:
    """Load and cache ground truth records."""
    global _GROUND_TRUTH
    if _GROUND_TRUTH is None:
        gt_path = Path(__file__).parent.parent / "eval" / "extraction_ground_truth.json"
        with open(gt_path, encoding="utf-8") as f:
            _GROUND_TRUTH = json.load(f)
    return _GROUND_TRUTH


def _next_gt_record() -> dict:
    """Return next ground truth record (round-robin)."""
    global _GT_INDEX
    records = _load_ground_truth()
    record = records[_GT_INDEX % len(records)]
    _GT_INDEX += 1
    return record


# ---------------------------------------------------------------------------
# Schema mapping: ground truth → pipeline Pydantic models
# ---------------------------------------------------------------------------


def _map_skills_for_llm(gt: dict) -> list[dict]:
    """Map GT skill records to _LLMSkill format."""
    return [
        {
            "skill_name": s.get("skill_name", ""),
            "type": s.get("type", "Technical"),
            "confidence": s.get("confidence", 0.8),
            "required_flag": s.get("required_flag"),
            "source_span": s.get("source_span", {}),
        }
        for s in gt.get("skills", [])
    ]


def _map_tasks_for_llm(gt: dict) -> list[dict]:
    """Map GT task records to TaskRecord format (task_category, seniority_signal)."""
    return [
        {
            "task_description": t.get("task_description", ""),
            "task_category": t.get("category", "core"),
            "seniority_signal": "any",
            "confidence": t.get("confidence", 0.8),
            "source_span": t.get("source_span", {}),
        }
        for t in gt.get("tasks", [])
    ]


def _map_responsibilities_for_llm(gt: dict) -> list[dict]:
    """Map GT responsibility records to ResponsibilityRecord format."""
    return [
        {
            "responsibility_description": r.get("responsibility_description", ""),
            "scope": r.get("scope", "individual"),
            "requires_ai_competency": False,
            "confidence": r.get("confidence", 0.8),
            "source_span": r.get("source_span", {}),
        }
        for r in gt.get("labeled_responsibilities", [])
    ]


def _simulate_metrics(prompt: str, content: str) -> dict[str, Any]:
    """Simulate realistic token counts, cost, and latency."""
    input_tokens = max(1, len(prompt) // 4)
    output_tokens = max(1, len(content) // 4)
    cost_usd = (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000
    latency_ms = random.randint(200, 800)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tokens_used": input_tokens + output_tokens,
        "cost_usd": round(cost_usd, 6),
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# Mock entry points
# ---------------------------------------------------------------------------


def mock_complete(prompt: str, agent_name: str, **kwargs: Any) -> dict[str, Any]:
    """Mock replacement for llm_adapter.complete().

    Returns a JSON string as content, simulating what the real LLM returns.
    """
    gt = _next_gt_record()

    # Build response based on agent_name
    if "spam" in agent_name.lower():
        content = json.dumps({"is_spam": False, "confidence": 0.95, "reason": "Legitimate job posting"})
    else:
        content = json.dumps({"skills": _map_skills_for_llm(gt)})

    metrics = _simulate_metrics(prompt, content)
    time.sleep(metrics["latency_ms"] / 1000.0)

    return {
        "content": content,
        "input_tokens": metrics["input_tokens"],
        "output_tokens": metrics["output_tokens"],
        "cost_usd": metrics["cost_usd"],
        "model_tier": "sonnet",
        "success": True,
        "extraction_failed": False,
    }


def mock_invoke_skills_llm(
    prompt: str, *, agent_name: str | None = None
) -> tuple[str, dict[str, Any]]:
    """Mock replacement for llm_client.invoke_skills_llm().

    Handles skills extraction (default) and SOC classification
    (when called via enrichment-agent for SOC prompts).
    """
    gt = _next_gt_record()

    # SOC classification: enrichment-agent uses invoke_skills_llm for SOC
    if agent_name and "enrichment" in agent_name.lower() and "soc" in prompt.lower():
        content = "15-1252"  # Software Developers — realistic mock SOC code
    else:
        content = json.dumps({"skills": _map_skills_for_llm(gt)})

    metrics = _simulate_metrics(prompt, content)
    time.sleep(metrics["latency_ms"] / 1000.0)

    return content, {
        "tokens_used": metrics["tokens_used"],
        "cost_usd": metrics["cost_usd"],
        "latency_ms": metrics["latency_ms"],
        "success": True,
        "extraction_failed": False,
        "error_reason": None,
        "provider": "mock",
        "model": "mock-sonnet-v1",
    }


def mock_invoke_structured(
    prompt: str,
    output_schema: type[TSchema],
    *,
    agent_name: str,
    **kwargs: Any,
) -> tuple[TSchema | None, dict[str, Any]]:
    """Mock replacement for llm_client.invoke_structured_extraction_llm().

    Returns (parsed_model_instance, metadata).
    """
    gt = _next_gt_record()

    # Build structured response matching the Pydantic schema
    schema_name = output_schema.__name__.lower() if hasattr(output_schema, "__name__") else ""

    if "naics" in agent_name.lower() or "naics" in schema_name:
        raw_data = {"naics_code": "541511"}  # Custom Computer Programming Services
    elif "employer" in agent_name.lower() or "employer" in schema_name:
        raw_data = {
            "company_size": "mid_market",
            "ai_maturity_signal": "ai_adopting",
            "sector": "technology",
        }
    elif "tasks" in agent_name.lower():
        raw_data = {"tasks": _map_tasks_for_llm(gt)}
    elif "responsibilities" in agent_name.lower() or "resp" in agent_name.lower():
        raw_data = {"responsibilities": _map_responsibilities_for_llm(gt)}
    else:
        raw_data = {"skills": _map_skills_for_llm(gt)}

    content_str = json.dumps(raw_data)
    metrics = _simulate_metrics(prompt, content_str)
    time.sleep(metrics["latency_ms"] / 1000.0)

    try:
        parsed = output_schema.model_validate(raw_data)
    except Exception:
        parsed = None

    return parsed, {
        "tokens_used": metrics["tokens_used"],
        "cost_usd": metrics["cost_usd"],
        "latency_ms": metrics["latency_ms"],
        "success": parsed is not None,
        "extraction_failed": parsed is None,
        "error_reason": None if parsed is not None else "mock_schema_validation_failed",
        "provider": "mock",
        "model": "mock-sonnet-v1",
    }
