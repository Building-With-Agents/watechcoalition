"""JSearch job-detail HTTP client (RapidAPI) — httpx, timeouts, 429 backoff.

URL and query param names are configurable via environment variables so they
can be aligned with the live RapidAPI playground without code changes
(see ``agents/docs/architecture/jsearch_description_detail.md``).
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import Any

import httpx
import structlog

from agents.ingestion.sources.jsearch_adapter import JSEARCH_HOST, jsearch_extract_description

log = structlog.get_logger()

DEFAULT_JOB_DETAIL_URL = "https://jsearch.p.rapidapi.com/job-details"
DEFAULT_JOB_ID_PARAM = "job_id"

# Permanent client errors — do not retry body
_TERMINAL_HTTP = frozenset({400, 401, 403, 404})


def _job_detail_url_from_env() -> str:
    return os.getenv("JSEARCH_JOB_DETAIL_URL", DEFAULT_JOB_DETAIL_URL).strip() or DEFAULT_JOB_DETAIL_URL


def _job_id_param_from_env() -> str:
    return os.getenv("JSEARCH_DETAIL_JOB_ID_PARAM", DEFAULT_JOB_ID_PARAM).strip() or DEFAULT_JOB_ID_PARAM


def _timeout_seconds() -> float:
    raw = os.getenv("JSEARCH_DETAIL_TIMEOUT_SECONDS", "30")
    try:
        return max(5.0, float(raw))
    except (TypeError, ValueError):
        return 30.0


def _max_429_retries() -> int:
    raw = os.getenv("JSEARCH_DETAIL_MAX_429_RETRIES", "5")
    try:
        return max(0, min(int(raw), 20))
    except (TypeError, ValueError):
        return 5


def _backoff_base_seconds() -> float:
    raw = os.getenv("JSEARCH_DETAIL_BACKOFF_BASE_SECONDS", "1.0")
    try:
        return max(0.1, float(raw))
    except (TypeError, ValueError):
        return 1.0


def normalize_jsearch_detail_payload(payload: Any) -> dict[str, Any] | None:
    """Return a single job dict from a JSearch detail JSON body, or None."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        return first if isinstance(first, dict) else None
    if isinstance(data, dict):
        return data
    if any(k in payload for k in ("job_id", "job_title", "job_description", "description")):
        return payload
    return None


async def fetch_job_detail(
    client: httpx.AsyncClient,
    *,
    job_id: str,
    api_key: str,
) -> tuple[dict[str, Any] | None, str | None, int | None]:
    """GET job detail. Returns ``(job_dict, error_reason, http_status)``.

    On success: ``(dict, None, 200)``.
    On failure: ``(None, short_reason, status_or_none)``.
    """
    url = _job_detail_url_from_env()
    param = _job_id_param_from_env()
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": JSEARCH_HOST,
    }
    params = {param: job_id}

    attempt = 0
    max_429 = _max_429_retries()
    while True:
        try:
            response = await client.get(url, params=params, headers=headers)
        except httpx.TimeoutException:
            log.warning("jsearch_detail_timeout", job_id_len=len(job_id))
            return None, "timeout", None
        except httpx.RequestError as exc:
            log.warning("jsearch_detail_request_error", error_type=type(exc).__name__)
            return None, "request_error", None

        status = response.status_code
        if status == 429:
            log.info("jsearch_429_total", endpoint="job_detail", attempt=attempt)
            if attempt >= max_429:
                return None, "too_many_429", 429
            base = _backoff_base_seconds() * (2**attempt)
            jitter = random.uniform(0, base * 0.25)
            wait = min(base + jitter, 120.0)
            log.info("jsearch_backoff_seconds", seconds=round(wait, 2), attempt=attempt)
            await asyncio.sleep(wait)
            attempt += 1
            continue

        if status in _TERMINAL_HTTP:
            return None, f"http_{status}", status

        if status >= 500:
            return None, f"http_{status}", status

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            return None, f"http_{status}", status

        try:
            body = response.json()
        except Exception:
            return None, "invalid_json", status

        job = normalize_jsearch_detail_payload(body)
        if not job:
            log.info("jsearch_detail_empty_body_total", job_id_len=len(job_id))
            return None, "no_job_in_payload", status

        log.info("jsearch_detail_success_total", job_id_len=len(job_id))
        return job, None, status


def extract_description_from_detail_job(job: dict[str, Any]) -> str:
    """Description string from a detail job dict (trimmed length cap matches search adapter)."""
    text = jsearch_extract_description(job)
    return text[:50000] if text else ""


async def fetch_job_description_detail(
    client: httpx.AsyncClient,
    *,
    job_id: str,
    api_key: str,
) -> tuple[str | None, str | None, int | None]:
    """Convenience: return ``(description, error_reason, http_status)``."""
    job, err, status = await fetch_job_detail(client, job_id=job_id, api_key=api_key)
    if err or not job:
        return None, err, status
    desc = extract_description_from_detail_job(job)
    if not desc.strip():
        return None, "empty_description", status
    return desc, None, status
