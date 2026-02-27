# agents/common/llm_adapter.py
"""Provider-agnostic LLM adapter. Azure OpenAI default; switchable via LLM_PROVIDER."""

from __future__ import annotations

import os
from typing import Any

# Stub: implement get_adapter and complete() with 2 retries, llm_audit_log, extraction_status fallback.
# Use LangChain + Azure OpenAI per tech stack.


class _LLMAdapterStub:
    """Stub until Phase 1 implementation. complete() raises."""

    def complete(self, prompt: str, schema: type[Any] | None = None) -> Any:
        raise NotImplementedError("LLM adapter implementation — Phase 1")


def get_adapter(provider: str | None = None) -> _LLMAdapterStub:
    """Return adapter for provider (azure_openai | openai | anthropic). Default from env."""
    _ = provider or os.getenv("LLM_PROVIDER", "azure_openai")
    return _LLMAdapterStub()
