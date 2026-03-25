"""Minimal LLM client for Pass 2 skills extraction. Uses Azure OpenAI via LangChain.

All calls go through agents.common.llm_adapter for cost and audit logging.
Retry and back-off are implemented by the caller (extract_skills), not here.
Loads .env from repo root so Azure env vars are available when this module is used.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    _repo_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_repo_root / ".env")
except ImportError:
    pass

from agents.common.llm_adapter import (
    MODEL_TIER_MAP,
    compute_extraction_cost,
    log_extraction_event,
)

AGENT_NAME = "skills-extraction-agent"


def _extract_retry_after(error_message: str) -> int | None:
    """Extract retry-after seconds from Azure OpenAI error message.

    Azure 429 responses often include "retry after N seconds" in the message.
    Same pattern used by the Next.js app in app/api/skills/parse-text/route.ts.
    """
    match = re.search(r"retry after (\d+)\s*seconds?", error_message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _model_tier_for_skills_extraction(model_name: str) -> str:
    """Map deployment/model name to pricing tier for :func:`compute_extraction_cost`.

    Uses the same ``MODEL_TIER_MAP`` as ``llm_adapter`` for Anthropic models.
    Azure OpenAI deployments are not in that map; use ``EXTRACTION_MODEL_TIER``
    (``sonnet`` | ``haiku``) or default ``sonnet`` for cost estimates.
    """
    explicit = os.getenv("EXTRACTION_MODEL_TIER", "").strip().lower()
    if explicit in ("sonnet", "haiku"):
        return explicit
    return MODEL_TIER_MAP.get(model_name, "sonnet")


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


def invoke_skills_llm(
    prompt: str,
    *,
    agent_name: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Invoke the skills-extraction LLM once. No retry or back-off.

    Parameters
    ----------
    prompt
        User prompt text.
    agent_name
        If set, used for ``llm_audit_log.agent_name`` instead of the default
        skills-extraction agent (e.g. spam preview diagnostics).

    Returns
    -------
    tuple[str, dict]
        (response_text, metadata). metadata includes: tokens_used, cost_usd,
        latency_ms, success, error_reason (optional), provider, model.
    """
    llm = _get_llm()
    audit_agent = agent_name or AGENT_NAME
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
                input_tokens = int(usage.get("input_tokens", 0))
                output_tokens = int(usage.get("output_tokens", 0))
                if tokens_used and (input_tokens or output_tokens) == 0:
                    input_tokens = len(prompt) // 4
                    output_tokens = max(0, tokens_used - input_tokens)
            else:
                tokens_used = (len(prompt) + len(text)) // 4
                input_tokens = len(prompt) // 4
                output_tokens = max(0, tokens_used - input_tokens)
        else:
            tokens_used = (len(prompt) + len(text)) // 4
            input_tokens = len(prompt) // 4
            output_tokens = max(0, tokens_used - input_tokens)

        model_tier = _model_tier_for_skills_extraction(str(model_name))
        cost_usd = compute_extraction_cost(input_tokens, output_tokens, model_tier)
        log_extraction_event(
            agent_name=audit_agent,
            prompt=prompt,
            model=model_name,
            provider=provider,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
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
        error_str = str(e)

        # Detect rate limiting: openai.RateLimitError or "429" in message
        is_rate_limit = False
        retry_after: int | None = None
        try:
            from openai import RateLimitError
            is_rate_limit = isinstance(e, RateLimitError)
        except ImportError:
            pass
        if not is_rate_limit:
            is_rate_limit = "429" in error_str or "rate limit" in error_str.lower()
        if is_rate_limit:
            retry_after = _extract_retry_after(error_str)
            error_str = f"429: {error_str}"

        log_extraction_event(
            agent_name=audit_agent,
            prompt=prompt,
            model=model_name,
            provider=provider,
            latency_ms=latency_ms,
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            success=False,
            error_reason=error_str,
        )
        return "", {
            "tokens_used": 0,
            "cost_usd": 0.0,
            "latency_ms": latency_ms,
            "success": False,
            "extraction_failed": True,
            "error_reason": error_str,
            "is_rate_limit": is_rate_limit,
            "retry_after_seconds": retry_after,
            "provider": provider,
            "model": model_name,
        }
