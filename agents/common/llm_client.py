"""Minimal LLM client for Pass 2 skills extraction. Uses Azure OpenAI via LangChain.

All calls go through agents.common.llm_adapter for cost and audit logging.
Retry and back-off are implemented by the caller (extract_skills), not here.
Loads .env from repo root so Azure env vars are available when this module is used.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    _repo_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_repo_root / ".env")
except ImportError:
    pass

from agents.common.llm_adapter import compute_extraction_cost, log_extraction_event

AGENT_NAME = "skills-extraction-agent"


def _get_llm() -> Any:
    """Build Azure OpenAI chat model for skills extraction."""
    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError as e:
        raise ImportError(
            "langchain-openai is required for Pass 2 skills extraction. "
            "Install with: pip install langchain-openai"
        ) from e

    deployment = (
        os.getenv("EXTRACTION_DEPLOYMENT_SKILLS")
        or os.getenv("EXTRACTION_MODEL_SKILLS")
        or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )
    if not deployment:
        raise ValueError(
            "One of EXTRACTION_DEPLOYMENT_SKILLS, EXTRACTION_MODEL_SKILLS, "
            "or AZURE_OPENAI_DEPLOYMENT_NAME must be set for skills extraction."
        )

    return AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        azure_deployment=deployment,
        temperature=0.1,
    )


def invoke_skills_llm(prompt: str) -> tuple[str, dict[str, Any]]:
    """Invoke the skills-extraction LLM once. No retry or back-off.

    Returns
    -------
    tuple[str, dict]
        (response_text, metadata). metadata includes: tokens_used, cost_usd,
        latency_ms, success, error_reason (optional), provider, model.
    """
    llm = _get_llm()
    model_name = (
        getattr(llm, "azure_deployment", None)
        or getattr(llm, "deployment_name", None)
        or getattr(llm, "model_name", None)
        or os.getenv("EXTRACTION_DEPLOYMENT_SKILLS")
        or os.getenv("EXTRACTION_MODEL_SKILLS")
        or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        or "azure-openai"
    )
    provider = "azure-openai"
    start = time.perf_counter()

    try:
        msg = llm.invoke(prompt)
        text = msg.content if hasattr(msg, "content") else str(msg)
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Approximate token count when usage not provided
        if hasattr(msg, "response_metadata") and isinstance(msg.response_metadata, dict):
            usage = msg.response_metadata.get("token_usage") or msg.response_metadata.get("usage")
            if isinstance(usage, dict):
                tokens_used = int(
                    usage.get("total_tokens")
                    or (usage.get("input_tokens", 0) + usage.get("output_tokens", 0))
                    or 0
                )
            else:
                tokens_used = (len(prompt) + len(text)) // 4
        else:
            tokens_used = (len(prompt) + len(text)) // 4

        # Split tokens: approximate input vs output when only total is available
        input_tokens_est = len(prompt) // 4
        output_tokens_est = max(0, tokens_used - input_tokens_est)
        cost_usd = compute_extraction_cost(input_tokens_est, output_tokens_est, "sonnet")
        log_extraction_event(
            agent_name=AGENT_NAME,
            prompt=prompt,
            model=model_name,
            provider=provider,
            latency_ms=latency_ms,
            input_tokens=input_tokens_est,
            output_tokens=output_tokens_est,
            cost_usd=cost_usd,
            success=True,
        )
        return text, {
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "success": True,
            "extraction_failed": False,
            "error_reason": None,
            "provider": provider,
            "model": model_name,
        }
    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        log_extraction_event(
            agent_name=AGENT_NAME,
            prompt=prompt,
            model=model_name,
            provider=provider,
            latency_ms=latency_ms,
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            success=False,
            error_reason=str(e),
        )
        return "", {
            "tokens_used": 0,
            "cost_usd": 0.0,
            "latency_ms": latency_ms,
            "success": False,
            "extraction_failed": True,
            "error_reason": str(e),
            "provider": provider,
            "model": model_name,
        }
