"""
test_llm_adapter.py — unit tests for llm_adapter.log_extraction_event.

Run with:
    cd agents
    pytest common/tests/test_llm_adapter.py -v
"""

from __future__ import annotations

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from agents.common.llm_adapter import log_extraction_event


def _session_scope_mock(session: MagicMock) -> MagicMock:
    """Build a MagicMock that works as a context manager yielding ``session``."""
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = None
    scope = MagicMock(return_value=cm)
    return scope


def test_log_extraction_event_success() -> None:
    """Success path: LLMAuditLog gets exact kwargs; session.add called once."""
    prompt = "ping"
    expected_prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    session = MagicMock()

    with (
        patch("agents.common.llm_adapter.session_scope", _session_scope_mock(session)),
        patch("agents.common.llm_adapter.LLMAuditLog") as MockLLMAuditLog,
    ):
        log_extraction_event(
            agent_name="test_agent",
            prompt=prompt,
            model="gpt-4o-mini",
            provider="azure_openai",
            latency_ms=250,
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.0001,
            success=True,
            error_reason=None,
        )

    MockLLMAuditLog.assert_called_once_with(
        agent_name="test_agent",
        prompt_hash=expected_prompt_hash,
        model="gpt-4o-mini",
        provider="azure_openai",
        latency_ms=250,
        input_tokens=100,
        output_tokens=50,
        token_count=150,
        cost_usd=0.0001,
        success=True,
        error_reason=None,
    )
    session.add.assert_called_once()


def test_log_extraction_event_failure() -> None:
    """Failure path: success=False and error_reason propagated to LLMAuditLog."""
    prompt = "pong"
    expected_prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    session = MagicMock()

    with (
        patch("agents.common.llm_adapter.session_scope", _session_scope_mock(session)),
        patch("agents.common.llm_adapter.LLMAuditLog") as MockLLMAuditLog,
    ):
        log_extraction_event(
            agent_name="test_agent",
            prompt=prompt,
            model="gpt-4o-mini",
            provider="azure_openai",
            latency_ms=0,
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            success=False,
            error_reason="timeout",
        )

    MockLLMAuditLog.assert_called_once_with(
        agent_name="test_agent",
        prompt_hash=expected_prompt_hash,
        model="gpt-4o-mini",
        provider="azure_openai",
        latency_ms=0,
        input_tokens=0,
        output_tokens=0,
        token_count=0,
        cost_usd=0.0,
        success=False,
        error_reason="timeout",
    )


@pytest.mark.parametrize(
    ("input_t", "output_t"),
    [(77, 23), (100, 50), (0, 0)],
)
def test_log_extraction_event_token_count_equals_sum(input_t: int, output_t: int) -> None:
    """token_count on LLMAuditLog must equal input_tokens + output_tokens."""
    session = MagicMock()

    with (
        patch("agents.common.llm_adapter.session_scope", _session_scope_mock(session)),
        patch("agents.common.llm_adapter.LLMAuditLog") as MockLLMAuditLog,
    ):
        log_extraction_event(
            agent_name="a",
            prompt="x",
            model="m",
            provider="p",
            latency_ms=1,
            input_tokens=input_t,
            output_tokens=output_t,
            cost_usd=0.0,
            success=True,
        )

    _, kwargs = MockLLMAuditLog.call_args
    assert kwargs["token_count"] == input_t + output_t


def test_log_extraction_event_uses_fresh_session_per_concurrent_call() -> None:
    """Concurrent audit writes should not share or leak SQLAlchemy sessions."""
    created_sessions: list[MagicMock] = []
    exited_sessions: list[MagicMock] = []
    lock = threading.Lock()

    def _session_scope_factory():
        session = MagicMock()
        with lock:
            created_sessions.append(session)

        @contextmanager
        def _scope():
            try:
                yield session
            finally:
                session.close()
                with lock:
                    exited_sessions.append(session)

        return _scope()

    def _write_one(i: int) -> None:
        log_extraction_event(
            agent_name=f"agent-{i}",
            prompt=f"prompt-{i}",
            model="gpt-4o-mini",
            provider="azure_openai",
            latency_ms=25,
            input_tokens=10,
            output_tokens=5,
            cost_usd=0.001,
            success=True,
        )

    with (
        patch("agents.common.llm_adapter.session_scope", side_effect=_session_scope_factory),
        patch("agents.common.llm_adapter.LLMAuditLog", side_effect=lambda **kwargs: kwargs),
        ThreadPoolExecutor(max_workers=6) as executor,
    ):
        list(executor.map(_write_one, range(12)))

    assert len(created_sessions) == 12
    assert len({id(session) for session in created_sessions}) == 12
    assert len(exited_sessions) == 12
    assert {id(session) for session in exited_sessions} == {id(session) for session in created_sessions}
    for session in created_sessions:
        session.add.assert_called_once()
        session.close.assert_called_once()
