"""Unit tests for ``agents.eval.cost_tier``."""

from __future__ import annotations

import pytest

from agents.eval.cost_tier import resolve_llm_audit_model_tier


@pytest.fixture
def clear_deployment_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "EXTRACTION_DEPLOYMENT_SKILLS",
        "EXTRACTION_MODEL_SKILLS",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "EXTRACTION_MODEL_TIER",
    ):
        monkeypatch.delenv(key, raising=False)


def test_substring_haiku_sonnet(clear_deployment_env: None) -> None:
    assert resolve_llm_audit_model_tier("claude-haiku-4-5") == "haiku"
    assert resolve_llm_audit_model_tier("claude-sonnet-4-5") == "sonnet"


def test_azure_deployment_uses_extraction_model_tier(
    monkeypatch: pytest.MonkeyPatch,
    clear_deployment_env: None,
) -> None:
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-skills")
    monkeypatch.setenv("EXTRACTION_MODEL_TIER", "haiku")
    assert resolve_llm_audit_model_tier("gpt-4o-skills") == "haiku"


def test_azure_deployment_defaults_sonnet(
    monkeypatch: pytest.MonkeyPatch,
    clear_deployment_env: None,
) -> None:
    monkeypatch.setenv("EXTRACTION_DEPLOYMENT_SKILLS", "my-deploy")
    monkeypatch.delenv("EXTRACTION_MODEL_TIER", raising=False)
    assert resolve_llm_audit_model_tier("my-deploy") == "sonnet"


def test_unknown_model_is_other(clear_deployment_env: None) -> None:
    assert resolve_llm_audit_model_tier("unknown-deployment-xyz") == "other"


def test_empty_model_other(clear_deployment_env: None) -> None:
    assert resolve_llm_audit_model_tier("") == "other"
    assert resolve_llm_audit_model_tier(None) == "other"
