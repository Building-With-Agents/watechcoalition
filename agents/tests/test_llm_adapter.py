from __future__ import annotations

import pytest
from pydantic import BaseModel

from agents.common import llm_adapter
from agents.common.llm_adapter import LLMAdapterError, get_adapter


class _OutputSchema(BaseModel):
    summary: str


class _FakeModel:
    def __init__(self, fail_times: int = 0) -> None:
        self.calls = 0
        self.fail_times = fail_times

    def with_structured_output(self, schema: type[BaseModel] | dict[str, str]) -> _FakeModel:
        return self

    def invoke(self, prompt: str) -> dict[str, str]:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("temporary model failure")
        return {"summary": f"ok:{prompt}"}


def test_get_adapter_unsupported_provider_raises() -> None:
    with pytest.raises(LLMAdapterError):
        get_adapter("not-a-provider")


def test_complete_retries_and_returns_none_on_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_adapter, "_build_azure_openai_model", lambda: _FakeModel(fail_times=10))
    monkeypatch.setattr(llm_adapter.time, "sleep", lambda _: None)

    adapter = get_adapter("azure_openai")
    result = adapter.complete(prompt="hello", schema=_OutputSchema)

    assert result is None


def test_complete_retries_and_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    model = _FakeModel(fail_times=2)
    monkeypatch.setattr(llm_adapter, "_build_azure_openai_model", lambda: model)
    monkeypatch.setattr(llm_adapter.time, "sleep", lambda _: None)

    adapter = get_adapter("azure_openai")
    result = adapter.complete(prompt="world", schema=_OutputSchema)

    assert result == {"summary": "ok:world"}
    assert model.calls == 3
