"""Integration-style tests for JSearch description backfill worker (mocked HTTP)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import agents.scripts.run_jsearch_description_backfill as backfill  # noqa: E402
from agents.common.data_store.models import RawIngestedJob  # noqa: E402


def _make_row(*, external_id: str = "job-1") -> RawIngestedJob:
    return RawIngestedJob(
        ingestion_run_id="run-1",
        region_id="r1",
        source="jsearch",
        external_id=external_id,
        raw_payload_hash="0" * 64,
        title="Engineer",
        company="Co",
        description=None,
        processing_status="awaiting_description",
        detail_fetch_attempts=0,
        raw_payload={"job_id": external_id},
    )


def test_run_backfill_promotes_when_substantive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DESCRIPTION_MIN_CHARS", "10")
    long = "word " * 5  # 30+ chars
    job_payload = {"job_id": "job-1", "job_description": long}

    async def fake_fetch(client, job_id: str, api_key: str):
        assert job_id == "job-1"
        return job_payload, None, 200

    monkeypatch.setattr(backfill, "fetch_job_detail", fake_fetch)
    row = _make_row()
    asyncio.run(backfill.run_backfill_batch([row], dry_run=False, api_key="k"))
    assert row.processing_status == "pending"
    assert row.description_source == "jsearch_detail"
    assert long.strip() in (row.description or "")


def test_run_backfill_dedup_second_row_no_second_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DESCRIPTION_MIN_CHARS", "5")
    job_payload = {"job_id": "same", "job_description": "hello world here"}
    calls: list[str] = []

    async def fake_fetch(client, job_id: str, api_key: str):
        calls.append(job_id)
        return job_payload, None, 200

    monkeypatch.setattr(backfill, "fetch_job_detail", fake_fetch)
    r1 = _make_row(external_id="same")
    r2 = _make_row(external_id="same")
    asyncio.run(backfill.run_backfill_batch([r1, r2], dry_run=False, api_key="k"))
    assert len(calls) == 1
    assert r1.processing_status == "pending"
    assert r2.processing_status == "pending"


def test_run_backfill_dry_run_no_http(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def fake_fetch(client, job_id: str, api_key: str):
        calls.append(job_id)
        return {}, None, 200

    monkeypatch.setattr(backfill, "fetch_job_detail", fake_fetch)
    row = _make_row()
    asyncio.run(backfill.run_backfill_batch([row], dry_run=True, api_key="k"))
    assert calls == []
    assert row.processing_status == "awaiting_description"
