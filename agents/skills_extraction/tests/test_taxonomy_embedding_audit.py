"""Issue #108: Step 4 embedding calls write to llm_audit_log via log_extraction_event."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

# Import after env may be patched
from agents.skills_extraction.extractors.taxonomy import _embed_texts_azure


@pytest.fixture
def embedding_env() -> dict[str, str]:
    return {
        "AZURE_OPENAI_EMBEDDING_ENDPOINT": "https://test.openai.azure.com",
        "AZURE_OPENAI_EMBEDDING_API_KEY": "test-key",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME": "embedding-deployment",
    }


@patch("agents.common.llm_adapter.log_extraction_event")
def test_embed_texts_azure_logs_audit_on_success(
    mock_log: MagicMock,
    embedding_env: dict[str, str],
) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "data": [{"embedding": [0.0, 1.0, 0.5]}],
        "usage": {"prompt_tokens": 42},
    }

    mock_client_instance = MagicMock()
    mock_client_instance.post.return_value = mock_resp

    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_client_instance
    mock_cm.__exit__.return_value = None

    with (
        patch.dict(os.environ, embedding_env, clear=False),
        patch(
            "agents.skills_extraction.extractors.taxonomy.httpx.Client",
            return_value=mock_cm,
        ),
    ):
        out = _embed_texts_azure(["hello"])

    assert out == [[0.0, 1.0, 0.5]]
    mock_log.assert_called_once()
    kwargs = mock_log.call_args.kwargs
    assert kwargs["agent_name"] == "taxonomy-resolver"
    assert kwargs["model"] == "text-embedding-3-small"
    assert kwargs["provider"] == "azure-openai"
    assert kwargs["input_tokens"] == 42
    assert kwargs["output_tokens"] == 0
    assert kwargs["success"] is True
    assert kwargs["error_reason"] is None
    assert kwargs["prompt"] == "hello"
    assert kwargs["latency_ms"] >= 0


@patch("agents.common.llm_adapter.log_extraction_event")
def test_embed_texts_azure_audit_uses_total_tokens_when_no_prompt_tokens(
    mock_log: MagicMock,
    embedding_env: dict[str, str],
) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "data": [{"embedding": [1.0]}],
        "usage": {"total_tokens": 99},
    }

    mock_client_instance = MagicMock()
    mock_client_instance.post.return_value = mock_resp
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_client_instance
    mock_cm.__exit__.return_value = None

    with (
        patch.dict(os.environ, embedding_env, clear=False),
        patch(
            "agents.skills_extraction.extractors.taxonomy.httpx.Client",
            return_value=mock_cm,
        ),
    ):
        _embed_texts_azure(["a", "b"])

    kwargs = mock_log.call_args.kwargs
    assert kwargs["input_tokens"] == 99
    assert kwargs["prompt"] == "a\nb"
