"""Minimal LLM client for Pass 2 skills extraction. Uses Azure OpenAI via LangChain.

All calls go through agents.common.llm_adapter for cost and audit logging.
Retry and back-off are implemented by the caller (extract_skills), not here.
Loads .env from repo root so Azure env vars are available when this module is used.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    _repo_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(_repo_root / ".env")
except ImportError:
    pass

import structlog

from agents.common.llm_adapter import compute_extraction_cost, log_extraction_event

AGENT_NAME = "skills-extraction-agent"
log = structlog.get_logger()

TSchema = TypeVar("TSchema", bound=BaseModel)


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


def _resolve_azure_deployment(*env_keys: str) -> str:
    """Return first non-empty deployment name from env keys (Haiku/Sonnet slots)."""
    for key in env_keys:
        val = os.getenv(key)
        if val and val.strip():
            return val.strip()
    raise ValueError(
        "Azure OpenAI deployment not configured. Set one of: " + ", ".join(env_keys)
    )


def invoke_structured_extraction_llm(
    prompt: str,
    output_schema: type[TSchema],
    *,
    agent_name: str,
    deployment_env_keys: tuple[str, ...],
    model_tier_for_cost: str,
) -> tuple[TSchema | None, dict[str, Any]]:
    """Invoke Azure OpenAI with LangChain ``with_structured_output`` once.

    Uses the same audit logging pattern as ``invoke_skills_llm``. On any
    exception, returns (None, metadata) with extraction_failed=True and
    does not raise — callers return empty lists and continue the batch.

    Parameters
    ----------
    prompt
        Full user prompt (no PII in downstream logs).
    output_schema
        Pydantic model class for the structured response root object.
    agent_name
        Name written to llm_audit_log.
    deployment_env_keys
        Ordered env var names for ``azure_deployment`` (first wins).
    model_tier_for_cost
        ``haiku`` or ``sonnet`` for ``compute_extraction_cost``.
    """
    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError as e:
        log.error("structured_llm_import_failed", error=str(e))
        return None, {
            "tokens_used": 0,
            "cost_usd": 0.0,
            "latency_ms": 0,
            "success": False,
            "extraction_failed": True,
            "error_reason": str(e),
            "provider": "azure-openai",
            "model": "",
        }

    try:
        deployment = _resolve_azure_deployment(*deployment_env_keys)
    except ValueError as e:
        log.warning("structured_llm_missing_deployment", error=str(e))
        return None, {
            "tokens_used": 0,
            "cost_usd": 0.0,
            "latency_ms": 0,
            "success": False,
            "extraction_failed": True,
            "error_reason": str(e),
            "provider": "azure-openai",
            "model": "",
        }

    model_name = deployment
    provider = "azure-openai"
    start = time.perf_counter()

    try:
        llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            azure_deployment=deployment,
            temperature=0.1,
        )
        try:
            chain = llm.with_structured_output(output_schema, include_raw=True)
            raw_out: Any = chain.invoke(prompt)
        except TypeError:
            chain = llm.with_structured_output(output_schema)
            raw_out = chain.invoke(prompt)

        latency_ms = int((time.perf_counter() - start) * 1000)

        parsed: TSchema | None
        msg_for_usage: Any = None
        if isinstance(raw_out, dict) and "parsed" in raw_out:
            parsed = raw_out.get("parsed")
            msg_for_usage = raw_out.get("raw")
        else:
            parsed = raw_out  # type: ignore[assignment]
            msg_for_usage = None

        tokens_used = 0
        if msg_for_usage is not None and hasattr(msg_for_usage, "response_metadata"):
            md = getattr(msg_for_usage, "response_metadata", None) or {}
            if isinstance(md, dict):
                usage = md.get("token_usage") or md.get("usage")
                if isinstance(usage, dict):
                    tokens_used = int(
                        usage.get("total_tokens")
                        or (usage.get("input_tokens", 0) + usage.get("output_tokens", 0))
                        or 0
                    )
        if tokens_used <= 0:
            out_preview = ""
            if parsed is not None:
                out_preview = str(parsed)[:2000]
            tokens_used = max(1, (len(prompt) + len(out_preview)) // 4)

        input_tokens_est = len(prompt) // 4
        output_tokens_est = max(0, tokens_used - input_tokens_est)
        cost_usd = compute_extraction_cost(
            input_tokens_est, output_tokens_est, model_tier_for_cost
        )

        log_extraction_event(
            agent_name=agent_name,
            prompt=prompt,
            model=model_name,
            provider=provider,
            latency_ms=latency_ms,
            input_tokens=input_tokens_est,
            output_tokens=output_tokens_est,
            cost_usd=cost_usd,
            success=parsed is not None,
            error_reason=None if parsed is not None else "structured_output_empty",
        )

        if parsed is None:
            return None, {
                "tokens_used": tokens_used,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                "success": False,
                "extraction_failed": True,
                "error_reason": "structured_output_empty",
                "provider": provider,
                "model": model_name,
            }

        return parsed, {
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
            agent_name=agent_name,
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
        return None, {
            "tokens_used": 0,
            "cost_usd": 0.0,
            "latency_ms": latency_ms,
            "success": False,
            "extraction_failed": True,
            "error_reason": str(e),
            "provider": provider,
            "model": model_name,
        }
