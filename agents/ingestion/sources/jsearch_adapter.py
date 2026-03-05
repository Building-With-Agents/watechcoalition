"""JSearch API adapter via RapidAPI.

Reads ``JSEARCH_API_KEY`` from environment.  Uses httpx with retry/backoff
per CLAUDE.md retry policy (5 max, exponential + jitter).
"""

from __future__ import annotations

import asyncio
import os
import random

import httpx
import structlog

from agents.ingestion.sources.base_adapter import SourceAdapter

log = structlog.get_logger()

_JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com/search"
_MAX_RETRIES = 5
_BASE_DELAY = 1.0  # seconds


def _map_jsearch_record(raw: dict) -> dict:
    """Map a JSearch API result to our canonical raw record shape."""
    city = raw.get("job_city") or ""
    state = raw.get("job_state") or ""
    location_parts = [p for p in (city, state) if p]

    return {
        "external_id": str(raw.get("job_id", "")),
        "source": "jsearch",
        "title": raw.get("job_title", ""),
        "company": raw.get("employer_name", ""),
        "location": ", ".join(location_parts) if location_parts else None,
        "raw_text": raw.get("job_description", ""),
        "url": raw.get("job_apply_link") or raw.get("job_google_link", ""),
        "date_posted": raw.get("job_posted_at_datetime_utc", ""),
        "raw_payload": raw,
    }


class JSearchAdapter(SourceAdapter):
    """Fetches job postings from JSearch API (RapidAPI)."""

    source_name = "jsearch"

    def __init__(self) -> None:
        self._api_key = os.getenv("JSEARCH_API_KEY", "")

    async def fetch(
        self, *, limit: int = 50, query: str = "software engineer", location: str = "Washington state"
    ) -> list[dict]:
        if not self._api_key:
            log.warning("jsearch_no_api_key", note="JSEARCH_API_KEY not set, returning empty")
            return []

        headers = {
            "X-RapidAPI-Key": self._api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }

        all_records: list[dict] = []
        page = 1

        async with httpx.AsyncClient(timeout=30.0) as client:
            while len(all_records) < limit:
                params = {
                    "query": f"{query} in {location}",
                    "page": str(page),
                    "num_pages": "1",
                }

                data = await self._request_with_retry(client, headers, params)
                if data is None:
                    break

                results = data.get("data", [])
                if not results:
                    break

                for raw in results:
                    if len(all_records) >= limit:
                        break
                    all_records.append(_map_jsearch_record(raw))

                page += 1

        log.info("jsearch_fetch_complete", count=len(all_records), query=query, location=location)
        return all_records

    async def _request_with_retry(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> dict | None:
        """Make a single API request with exponential backoff + jitter."""
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                resp = await client.get(_JSEARCH_BASE_URL, headers=headers, params=params)

                if resp.status_code == 429:
                    delay = _BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 1)
                    log.warning("jsearch_rate_limited", attempt=attempt, delay_s=round(delay, 2))
                    await asyncio.sleep(delay)
                    continue

                resp.raise_for_status()
                return resp.json()

            except httpx.HTTPStatusError as exc:
                log.warning("jsearch_http_error", status=exc.response.status_code, attempt=attempt)
                if attempt == _MAX_RETRIES:
                    return None
                delay = _BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 1)
                await asyncio.sleep(delay)

            except httpx.RequestError as exc:
                log.warning("jsearch_request_error", error=str(exc), attempt=attempt)
                if attempt == _MAX_RETRIES:
                    return None
                delay = _BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 1)
                await asyncio.sleep(delay)

        return None

    async def health_check(self) -> bool:
        return bool(self._api_key)
