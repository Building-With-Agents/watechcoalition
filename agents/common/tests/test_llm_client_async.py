"""Unit tests for async structured extraction calls in ``agents.common.llm_client``."""

from __future__ import annotations

import asyncio
import os
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import BaseModel

from agents.common.llm_client import (
    ainvoke_structured_extraction_llm,
    invoke_structured_extraction_llm,
)


class _ExampleSchema(BaseModel):
    """Minimal structured schema for testing."""

    items: list[str]


def _fake_langchain_module(azure_cls: MagicMock) -> ModuleType:
    module = ModuleType("langchain_openai")
    module.AzureChatOpenAI = azure_cls
    return module


def _deployment_env() -> dict[str, str]:
    return {
        "EXTRACTION_DEPLOYMENT_TASKS": "test-tasks-deployment",
    }


def test_ainvoke_structured_extraction_llm_matches_sync_success_metadata() -> None:
    """Async structured extraction should match the sync metadata contract on success."""
    prompt = "extract items"
    parsed = _ExampleSchema(items=["python"])
    raw_msg = SimpleNamespace(
        response_metadata={
            "model_name": "gpt-test",
            "usage": {"input_tokens": 12, "output_tokens": 4},
        }
    )
    chain = MagicMock()
    chain.invoke.return_value = {"parsed": parsed, "raw": raw_msg}
    chain.ainvoke = AsyncMock(return_value={"parsed": parsed, "raw": raw_msg})
    llm = MagicMock()
    llm.with_structured_output.return_value = chain
    azure_cls = MagicMock(return_value=llm)

    with (
        patch.dict(os.environ, _deployment_env(), clear=False),
        patch.dict(sys.modules, {"langchain_openai": _fake_langchain_module(azure_cls)}),
        patch("agents.common.llm_client.compute_extraction_cost", return_value=0.123),
        patch("agents.common.llm_client.log_extraction_event") as mock_log,
    ):
        parsed_async, async_meta = asyncio.run(
            ainvoke_structured_extraction_llm(
                prompt,
                _ExampleSchema,
                agent_name="async-agent",
                deployment_env_keys=("EXTRACTION_DEPLOYMENT_TASKS",),
                model_tier_for_cost="haiku",
            )
        )
        parsed_sync, sync_meta = invoke_structured_extraction_llm(
            prompt,
            _ExampleSchema,
            agent_name="sync-agent",
            deployment_env_keys=("EXTRACTION_DEPLOYMENT_TASKS",),
            model_tier_for_cost="haiku",
        )

    assert parsed_async == parsed_sync == parsed
    assert async_meta == sync_meta
    assert async_meta["tokens_used"] == 16
    assert async_meta["cost_usd"] == 0.123
    assert async_meta["model"] == "gpt-test (test-tasks-deployment)"
    chain.ainvoke.assert_awaited_once_with(prompt)
    chain.invoke.assert_called_once_with(prompt)
    assert mock_log.call_count == 2


def test_ainvoke_structured_extraction_llm_timeout_returns_failed_metadata() -> None:
    """Timeouts should be returned as failed metadata and not raised to callers."""
    chain = MagicMock()
    chain.ainvoke = AsyncMock(side_effect=TimeoutError("request timeout"))
    llm = MagicMock()
    llm.with_structured_output.return_value = chain
    azure_cls = MagicMock(return_value=llm)

    with (
        patch.dict(os.environ, _deployment_env(), clear=False),
        patch.dict(sys.modules, {"langchain_openai": _fake_langchain_module(azure_cls)}),
        patch("agents.common.llm_client.log_extraction_event"),
    ):
        parsed, meta = asyncio.run(
            ainvoke_structured_extraction_llm(
                "extract items",
                _ExampleSchema,
                agent_name="async-agent",
                deployment_env_keys=("EXTRACTION_DEPLOYMENT_TASKS",),
                model_tier_for_cost="haiku",
            )
        )

    assert parsed is None
    assert meta["success"] is False
    assert meta["extraction_failed"] is True
    assert meta["error_reason"] == "request timeout"
    assert meta["model"] == "test-tasks-deployment"
    assert "is_rate_limit" not in meta


def test_ainvoke_structured_extraction_llm_returns_rate_limit_metadata() -> None:
    """429 responses should expose the retry-after metadata used by async callers."""
    chain = MagicMock()
    chain.ainvoke = AsyncMock(side_effect=RuntimeError("Rate limit reached. Retry after 11 seconds."))
    llm = MagicMock()
    llm.with_structured_output.return_value = chain
    azure_cls = MagicMock(return_value=llm)

    with (
        patch.dict(os.environ, _deployment_env(), clear=False),
        patch.dict(sys.modules, {"langchain_openai": _fake_langchain_module(azure_cls)}),
        patch("agents.common.llm_client.log_extraction_event"),
    ):
        parsed, meta = asyncio.run(
            ainvoke_structured_extraction_llm(
                "extract items",
                _ExampleSchema,
                agent_name="async-agent",
                deployment_env_keys=("EXTRACTION_DEPLOYMENT_TASKS",),
                model_tier_for_cost="haiku",
            )
        )

    assert parsed is None
    assert meta["success"] is False
    assert meta["extraction_failed"] is True
    assert meta["is_rate_limit"] is True
    assert meta["retry_after_seconds"] == 11
    assert meta["error_reason"].startswith("429: ")


def test_ainvoke_structured_extraction_llm_empty_response_returns_failed_metadata() -> None:
    """Structured output with ``parsed=None`` should preserve token/cost metadata."""
    prompt = "extract items"
    raw_msg = SimpleNamespace(
        response_metadata={
            "model_name": "gpt-test",
            "usage": {"input_tokens": 10, "output_tokens": 6},
        }
    )
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value={"parsed": None, "raw": raw_msg})
    llm = MagicMock()
    llm.with_structured_output.return_value = chain
    azure_cls = MagicMock(return_value=llm)

    with (
        patch.dict(os.environ, _deployment_env(), clear=False),
        patch.dict(sys.modules, {"langchain_openai": _fake_langchain_module(azure_cls)}),
        patch("agents.common.llm_client.compute_extraction_cost", return_value=0.321),
        patch("agents.common.llm_client.log_extraction_event"),
    ):
        parsed, meta = asyncio.run(
            ainvoke_structured_extraction_llm(
                prompt,
                _ExampleSchema,
                agent_name="async-agent",
                deployment_env_keys=("EXTRACTION_DEPLOYMENT_TASKS",),
                model_tier_for_cost="haiku",
            )
        )

    assert parsed is None
    assert meta["success"] is False
    assert meta["extraction_failed"] is True
    assert meta["error_reason"] == "structured_output_empty"
    assert meta["tokens_used"] == 16
    assert meta["cost_usd"] == 0.321
    assert meta["model"] == "gpt-test (test-tasks-deployment)"


def test_ainvoke_structured_extraction_llm_handles_import_error() -> None:
    """Missing ``langchain_openai`` should return standard failure metadata."""
    with (
        patch.dict(os.environ, _deployment_env(), clear=False),
        patch.dict(sys.modules, {"langchain_openai": None}),
    ):
        parsed, meta = asyncio.run(
            ainvoke_structured_extraction_llm(
                "extract items",
                _ExampleSchema,
                agent_name="async-agent",
                deployment_env_keys=("EXTRACTION_DEPLOYMENT_TASKS",),
                model_tier_for_cost="haiku",
            )
        )

    assert parsed is None
    assert meta["success"] is False
    assert meta["extraction_failed"] is True
    assert "langchain-openai is required" in meta["error_reason"]
    assert meta["provider"] == "azure-openai"
    assert meta["model"] == ""
