"""Minimal LLM client for Pass 2 skills extraction. Uses Azure OpenAI via LangChain.

All calls go through agents.common.llm_adapter for cost and audit logging.
Retry and back-off are implemented by the caller (extract_skills), not here.
Loads .env from repo root so Azure env vars are available when this module is used.
"""

from __future__ import annotations

import contextlib
import json as _json
import os
import re
import time
import uuid
from contextlib import nullcontext
from typing import Any, TypeVar

import structlog
from pydantic import BaseModel

from agents.common.env import load_repo_root_dotenv
from agents.common.llm_adapter import (
    MODEL_TIER_MAP,
    compute_extraction_cost,
    get_tracer,
    log_extraction_event,
)

load_repo_root_dotenv()

AGENT_NAME = "skills-extraction-agent"


def _parse_output_for_trace(text: str, max_chars: int = 4000) -> str | dict | list:
    """Parse JSON output so Langfuse renders it as a collapsible tree.

    Returns a parsed dict/list if valid JSON, otherwise the raw string truncated.
    """
    truncated = text[:max_chars]
    try:
        return _json.loads(truncated)
    except (ValueError, TypeError):
        return truncated
log = structlog.get_logger()

# Maps audit-log agent_name values to clean Langfuse span names.
# Audit log names are kept as-is; span names are human-readable operation labels.
_SPAN_NAME_MAP = {
    "skills-extraction-agent": "skills-extraction",
    "skills-extraction-responsibilities": "responsibilities-extraction",
    "skills-extraction-tasks": "tasks-extraction",
}

TSchema = TypeVar("TSchema", bound=BaseModel)


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
            "langchain-openai is required for Pass 2 skills extraction. Install with: pip install langchain-openai"
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
    # Mock provider: return ground truth data, no API calls
    if os.getenv("LLM_PROVIDER", "").strip().lower() == "mock":
        from agents.common.mock_llm_provider import mock_invoke_skills_llm

        audit_agent = agent_name or AGENT_NAME
        tracer = get_tracer()
        span_ctx = (
            tracer.start_span(
                _SPAN_NAME_MAP.get(audit_agent, audit_agent),
                correlation_id=str(uuid.uuid4()),
                input=prompt,
                metadata={"agent_name": audit_agent, "model": "mock-sonnet-v1"},
            )
            if tracer
            else nullcontext()
        )
        with span_ctx:
            text, meta = mock_invoke_skills_llm(prompt, agent_name=audit_agent)
            log_extraction_event(
                agent_name=audit_agent, prompt=prompt, model="mock-sonnet-v1",
                provider="mock", latency_ms=meta["latency_ms"],
                input_tokens=meta.get("tokens_used", 0) // 2,
                output_tokens=meta.get("tokens_used", 0) // 2,
                cost_usd=meta["cost_usd"], success=True,
            )
            if tracer:
                with contextlib.suppress(Exception):
                    tracer.log_event("llm_success", {
                        "input_tokens": meta.get("tokens_used", 0) // 2,
                        "output_tokens": meta.get("tokens_used", 0) // 2,
                        "cost_usd": meta["cost_usd"],
                        "output": _parse_output_for_trace(text),
                    })
            return text, meta

    llm = _get_llm()
    audit_agent = agent_name or AGENT_NAME
    deployment_name = (
        getattr(llm, "azure_deployment", None)
        or getattr(llm, "deployment_name", None)
        or getattr(llm, "model_name", None)
        or os.getenv("EXTRACTION_DEPLOYMENT_SKILLS")
        or os.getenv("EXTRACTION_MODEL_SKILLS")
        or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        or "azure-openai"
    )
    model_name = deployment_name  # overwritten below if response has actual model
    provider = "azure-openai"

    tracer = get_tracer()
    span_ctx = (
        tracer.start_span(
            _SPAN_NAME_MAP.get(audit_agent, audit_agent),
            correlation_id=str(uuid.uuid4()),
            input=prompt,
            metadata={"agent_name": audit_agent, "model": model_name},
        )
        if tracer
        else nullcontext()
    )
    start = time.perf_counter()

    with span_ctx:
        try:
            msg = llm.invoke(prompt)
            text = msg.content if hasattr(msg, "content") else str(msg)
            latency_ms = int((time.perf_counter() - start) * 1000)

            # Extract actual model name from response metadata (not just deployment name)
            if hasattr(msg, "response_metadata") and isinstance(msg.response_metadata, dict):
                actual_model = msg.response_metadata.get("model_name") or msg.response_metadata.get("model")
                if actual_model:
                    model_name = f"{actual_model} ({deployment_name})"

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
            if tracer:
                try:
                    tracer.record_latency("llm_call", seconds=latency_ms / 1000.0)
                    tracer.log_event(
                        "llm_success",
                        {
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "cost_usd": round(cost_usd, 6),
                            "output": _parse_output_for_trace(text),
                        },
                    )
                except Exception:
                    pass
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
            if tracer:
                with contextlib.suppress(Exception):
                    tracer.record_error(e, context={"agent_name": audit_agent, "model": model_name})
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
    # Mock provider: return ground truth data, no API calls
    if os.getenv("LLM_PROVIDER", "").strip().lower() == "mock":
        from agents.common.mock_llm_provider import mock_invoke_structured

        tracer = get_tracer()
        span_ctx = (
            tracer.start_span(
                _SPAN_NAME_MAP.get(agent_name, agent_name),
                correlation_id=str(uuid.uuid4()),
                input=prompt,
                metadata={"agent_name": agent_name, "model": "mock-sonnet-v1"},
            )
            if tracer
            else nullcontext()
        )
        with span_ctx:
            parsed, meta = mock_invoke_structured(prompt, output_schema, agent_name=agent_name)
            log_extraction_event(
                agent_name=agent_name, prompt=prompt, model="mock-sonnet-v1",
                provider="mock", latency_ms=meta["latency_ms"],
                input_tokens=meta.get("tokens_used", 0) // 2,
                output_tokens=meta.get("tokens_used", 0) // 2,
                cost_usd=meta["cost_usd"],
                success=meta["success"],
                error_reason=meta.get("error_reason"),
            )
            if tracer:
                with contextlib.suppress(Exception):
                    tracer.log_event("llm_success", {
                        "input_tokens": meta.get("tokens_used", 0) // 2,
                        "output_tokens": meta.get("tokens_used", 0) // 2,
                        "cost_usd": meta["cost_usd"],
                        "output": parsed.model_dump(mode="json") if hasattr(parsed, "model_dump") else _parse_output_for_trace(str(parsed)) if parsed else "mock_parse_failed",
                    })
            return parsed, meta

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

    deployment_name = deployment
    model_name = deployment_name  # overwritten below if response has actual model
    provider = "azure-openai"

    tracer = get_tracer()
    span_ctx = (
        tracer.start_span(
            _SPAN_NAME_MAP.get(agent_name, agent_name),
            correlation_id=str(uuid.uuid4()),
            input=prompt,
            metadata={"agent_name": agent_name, "model": model_name},
        )
        if tracer
        else nullcontext()
    )
    start = time.perf_counter()

    with span_ctx:
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

            # Extract actual model name from response metadata
            tokens_used = 0
            if msg_for_usage is not None and hasattr(msg_for_usage, "response_metadata"):
                md = getattr(msg_for_usage, "response_metadata", None) or {}
                if isinstance(md, dict):
                    actual_model = md.get("model_name") or md.get("model")
                    if actual_model:
                        model_name = f"{actual_model} ({deployment_name})"
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

            if tracer:
                try:
                    tracer.record_latency("llm_call", seconds=latency_ms / 1000.0)
                    tracer.log_event("llm_success", {
                        "input_tokens": input_tokens_est,
                        "output_tokens": output_tokens_est,
                        "cost_usd": round(cost_usd, 6),
                        "output": parsed.model_dump(mode="json") if hasattr(parsed, "model_dump") else _parse_output_for_trace(str(parsed)) if parsed is not None else "structured_output_empty",
                    })
                except Exception:
                    pass

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
            if tracer:
                with contextlib.suppress(Exception):
                    tracer.record_error(e, context={"agent_name": agent_name, "model": model_name})
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
