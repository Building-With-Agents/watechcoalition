"""Lightweight JSearch API client for the ground truth labeling tool.

Reuses the same JSEARCH_API_KEY env var as the ingestion agent.
Pattern borrowed from agents/ingestion/sources/jsearch_adapter.py.
"""

from __future__ import annotations

import os

import httpx

JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com/search"
JSEARCH_HOST = "jsearch.p.rapidapi.com"


def fix_mojibake(text: str) -> str:
    """Fix UTF-8 text that was decoded as Latin-1 (common JSearch issue).

    Example: 'â€¢' → '•', 'â€"' → '—', 'â€™' → '''
    """
    try:
        return text.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def get_api_key() -> str | None:
    """Return the JSearch API key from env, or None if unset."""
    return os.getenv("JSEARCH_API_KEY")


def search_jobs(query: str, num_results: int = 10) -> list[dict]:
    """Search JSearch API and return raw job dicts.

    Args:
        query: Search string (e.g. "data engineer El Paso TX").
        num_results: Max results to return (1-10 per page).

    Returns:
        List of raw job dicts from the JSearch API response.
        Each dict contains: job_id, job_title, employer_name,
        job_description, job_city, job_state, job_highlights, etc.
    """
    api_key = get_api_key()
    if not api_key:
        return []

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": JSEARCH_HOST,
    }
    params = {
        "query": query,
        "page": "1",
        "num_pages": "1",
    }

    try:
        resp = httpx.get(JSEARCH_BASE_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return data[:num_results]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        return [{"error": str(exc)}]


def parse_job_sections(job: dict) -> dict:
    """Extract labeled text sections from a JSearch job dict.

    Returns a dict with keys: title, company, city, state, external_id,
    description, requirements, responsibilities — ready for the labeler UI.
    """
    highlights = job.get("job_highlights") or {}

    # Requirements: join Qualifications array if present
    qualifications = highlights.get("Qualifications") or []
    requirements_text = "\n".join(f"- {q}" for q in qualifications) if qualifications else ""

    # Responsibilities: join Responsibilities array if present
    responsibilities_list = highlights.get("Responsibilities") or []
    responsibilities_text = (
        "\n".join(f"- {r}" for r in responsibilities_list) if responsibilities_list else ""
    )

    return {
        "external_id": job.get("job_id", ""),
        "title": fix_mojibake(job.get("job_title") or job.get("title", "")),
        "company": fix_mojibake(job.get("employer_name") or job.get("company_name", "")),
        "city": job.get("job_city", ""),
        "state": job.get("job_state", ""),
        "description": fix_mojibake(job.get("job_description") or job.get("description", "")),
        "requirements": fix_mojibake(requirements_text),
        "responsibilities": fix_mojibake(responsibilities_text),
        "job_url": job.get("job_apply_link") or job.get("job_google_link", ""),
        "is_remote": job.get("job_is_remote", False),
        "employment_type": job.get("job_employment_type", ""),
    }
