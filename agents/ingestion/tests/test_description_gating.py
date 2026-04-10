"""Tests for description substantive gate (JSearch detail backfill)."""

from __future__ import annotations

import pytest

from agents.ingestion.description_gating import (
    description_gate_reason,
    description_min_chars_from_env,
    is_substantive_description,
)


def test_below_min_length_not_substantive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DESCRIPTION_MIN_CHARS", "10")
    assert is_substantive_description("123456789") is False
    assert description_gate_reason("123456789") == "below_min_length"


def test_at_min_length_substantive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DESCRIPTION_MIN_CHARS", "5")
    assert is_substantive_description("12345") is True
    assert description_gate_reason("12345") == "ok"


def test_whitespace_only_not_substantive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DESCRIPTION_MIN_CHARS", "1")
    assert is_substantive_description("   \n\t  ") is False
    assert description_gate_reason("   \n\t  ") == "empty"


def test_none_not_substantive() -> None:
    assert is_substantive_description(None) is False
    assert description_gate_reason(None) == "null"


def test_default_min_chars_clamps_invalid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DESCRIPTION_MIN_CHARS", "not-int")
    assert description_min_chars_from_env() == 200


def test_strips_before_length(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DESCRIPTION_MIN_CHARS", "3")
    assert is_substantive_description("  ab c  ") is True
