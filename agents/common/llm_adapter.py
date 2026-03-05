"""
Provider-agnostic LLM adapter for pipeline agents.

Contract:
    adapter = get_adapter(provider=os.getenv("LLM_PROVIDER", "azure_openai"))
    result = adapter.complete(prompt="...", schema=OutputSchema)

Behavior:
- Supports azure_openai, openai, anthropic.
- Retries up to 2 times on failure (3 total attempts).
- Logs failures with structured logging.
- Week 2 scope logs to structlog only (no DB writes to llm_audit_log).
- Returns None after retry exhaustion so callers can degrade gracefully.
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import structlog
from pydantic import BaseModel

log = structlog.get_logger()

DEFAULT_PROVIDER = "azure_openai"
MAX_RETRIES = 2
RETRY_BACKOFF_SECONDS = 0.25


class LLMAdapterError(RuntimeError):
    """Raised when adapter configuration is invalid or provider is unsupported."""


class BaseLLMAdapter(ABC):
    """Abstract LLM adapter contract used by all provider implementations."""

    provider: str

    @abstractmethod
    def complete(
        self,
        prompt: str,
        schema: type[BaseModel] | dict[str, Any] | None = None,
    ) -> Any | None:
        """
        Return provider output for the prompt.

        When retries are exhausted, implementations return None and log failure.
        """


class _LangChainAdapter(BaseLLMAdapter):
    """LangChain-backed adapter with retry and lazy provider client creation."""

    def __init__(
        self,
        provider: str,
        model_factory: Callable[[], Any],
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.provider = provider
        self._model_factory = model_factory
        self._max_retries = max_retries
        self._model: Any | None = None

    def _get_model(self) -> Any:
        if self._model is None:
            self._model = self._model_factory()
        return self._model

    def complete(
        self,
        prompt: str,
        schema: type[BaseModel] | dict[str, Any] | None = None,
    ) -> Any | None:
        if not prompt or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        for attempt in range(self._max_retries + 1):
            try:
                model = self._get_model()
                if schema is not None:
                    return model.with_structured_output(schema).invoke(prompt)
                response = model.invoke(prompt)
                return getattr(response, "content", response)
            except Exception as exc:  # pragma: no cover - network/provider failures are non-deterministic
                is_last_attempt = attempt >= self._max_retries
                log.warning(
                    "llm_complete_failed",
                    provider=self.provider,
                    attempt=attempt + 1,
                    max_attempts=self._max_retries + 1,
                    error_type=type(exc).__name__,
                    final_attempt=is_last_attempt,
                )
                if is_last_attempt:
                    return None
                time.sleep(RETRY_BACKOFF_SECONDS * (2**attempt))
        return None


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    raise LLMAdapterError(f"Missing required environment variable: {name}")


def _build_azure_openai_model() -> Any:
    from langchain_openai import AzureChatOpenAI

    return AzureChatOpenAI(
        azure_endpoint=_require_env("AZURE_OPENAI_ENDPOINT"),
        api_key=_require_env("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        deployment_name=_require_env("AZURE_OPENAI_DEPLOYMENT_NAME"),
        temperature=0,
    )


def _build_openai_model() -> Any:
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        api_key=_require_env("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0,
    )


def _build_anthropic_model() -> Any:
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise LLMAdapterError(
            "Anthropic provider requires `langchain-anthropic` in requirements."
        ) from exc

    return ChatAnthropic(
        api_key=_require_env("ANTHROPIC_API_KEY"),
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
        temperature=0,
    )


def get_adapter(provider: str | None = None) -> BaseLLMAdapter:
    """
    Return provider-specific LLM adapter.

    Supported providers:
    - azure_openai (default)
    - openai
    - anthropic
    """
    selected = (provider or os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER)).strip().lower()
    factories: dict[str, Callable[[], Any]] = {
        "azure_openai": _build_azure_openai_model,
        "openai": _build_openai_model,
        "anthropic": _build_anthropic_model,
    }

    if selected not in factories:
        supported = ", ".join(sorted(factories))
        raise LLMAdapterError(f"Unsupported LLM provider '{selected}'. Supported providers: {supported}")

    return _LangChainAdapter(provider=selected, model_factory=factories[selected])


__all__ = [
    "BaseLLMAdapter",
    "DEFAULT_PROVIDER",
    "LLMAdapterError",
    "MAX_RETRIES",
    "get_adapter",
]
