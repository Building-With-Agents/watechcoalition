"""Tests for JSearch detail HTTP client (mocked httpx)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import httpx
import pytest

from agents.ingestion.sources.jsearch_detail_client import (
    extract_description_from_detail_job,
    fetch_job_detail,
    normalize_jsearch_detail_payload,
)


def test_normalize_detail_list_payload() -> None:
    job = {"job_id": "1", "job_description": "Hello"}
    assert normalize_jsearch_detail_payload({"data": [job]}) == job


def test_normalize_detail_dict_payload() -> None:
    job = {"job_id": "1", "description": "Hi"}
    assert normalize_jsearch_detail_payload({"data": job}) == job


def test_normalize_detail_flat_payload() -> None:
    job = {"job_title": "Dev", "job_description": "Do work"}
    assert normalize_jsearch_detail_payload(job) == job


def test_extract_description_from_detail_job() -> None:
    out = extract_description_from_detail_job({"job_description": "Full text " * 20})
    assert out.startswith("Full text Full text")
    assert len(out) >= 200


def test_fetch_job_detail_429_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JSEARCH_DETAIL_MAX_429_RETRIES", "2")
    monkeypatch.setenv("JSEARCH_DETAIL_BACKOFF_BASE_SECONDS", "0.01")

    responses = [
        httpx.Response(429, request=MagicMock()),
        httpx.Response(
            200,
            json={"data": [{"job_id": "x", "job_description": "y"}]},
        ),
    ]
    call = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call
        r = responses[min(call, len(responses) - 1)]
        call += 1
        return r

    transport = httpx.MockTransport(handler)

    async def _run() -> tuple:
        async with httpx.AsyncClient(transport=transport) as client:
            return await fetch_job_detail(client, job_id="x", api_key="k")

    job, err, status = asyncio.run(_run())
    assert err is None
    assert status == 200
    assert job and job.get("job_id") == "x"


def test_fetch_job_detail_terminal_404() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={})

    transport = httpx.MockTransport(handler)

    async def _run() -> tuple:
        async with httpx.AsyncClient(transport=transport) as client:
            return await fetch_job_detail(client, job_id="missing", api_key="k")

    job, err, status = asyncio.run(_run())
    assert job is None
    assert err == "http_404"
    assert status == 404
