"""Unit tests for raw row processing_status at staging (S3 empty-description gate)."""

from __future__ import annotations

import pytest

from agents.common.types import RawJobRecord
from agents.ingestion.agent import raw_processing_status_for_record


def _minimal_record(**kwargs: object) -> RawJobRecord:
    base = dict(
        external_id="e1",
        source="jsearch",
        region_id="r1",
        raw_payload_hash="a" * 64,
        title="T",
        company="C",
        description="",
        raw_payload={},
    )
    base.update(kwargs)
    return RawJobRecord(**base)


def test_pending_when_description_non_empty() -> None:
    r = _minimal_record(description="Build things.")
    assert raw_processing_status_for_record(r) == "pending"


def test_pending_when_description_whitespace_only_then_not_pending() -> None:
    r = _minimal_record(description="   \n\t  ")
    assert raw_processing_status_for_record(r) == "awaiting_description"


def test_awaiting_when_description_empty() -> None:
    r = _minimal_record(description="")
    assert raw_processing_status_for_record(r) == "awaiting_description"


@pytest.mark.parametrize("flag", ("1", "true", "TRUE", "yes"))
def test_allow_empty_description_pending_env(flag: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_EMPTY_DESCRIPTION_PENDING", flag)
    r = _minimal_record(description="")
    assert raw_processing_status_for_record(r) == "pending"


def test_allow_empty_description_pending_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ALLOW_EMPTY_DESCRIPTION_PENDING", raising=False)
    r = _minimal_record(description="")
    assert raw_processing_status_for_record(r) == "awaiting_description"
