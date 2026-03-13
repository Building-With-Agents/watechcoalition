"""
Fetch ground-truth dataset for deduplication experiment.

Uses JSearch API (RapidAPI) to pull job postings for the El Paso / Borderplex
region, maps them to RawJobRecord, saves to JSON, and prints unique company names
for manual career-page scraping.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

from agents.common.types.raw_job_record import RawJobRecord

# Load .env from repo root so JSEARCH_API_KEY is available when set there
_repo_root = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_repo_root / ".env")

TARGET_COUNT = 200
REGION_ID = "el_paso_borderplex"
SOURCE = "JSearch"
# Broader query so API returns more results; we still tag region_id as el_paso_borderplex
QUERY = "jobs in El Paso Texas"
OUTPUT_FILE = Path(__file__).parent / "ground_truth_dataset.json"
BASE_URL = "https://jsearch.p.rapidapi.com/search"


def _parse_date_posted(value) -> datetime | None:
    """Parse date_posted from API (timestamp or ISO string)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(value)
        except (ValueError, OSError):
            return None
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(value.replace("Z", "").split(".")[0], fmt)
            except ValueError:
                continue
    return None


def _compute_raw_payload_hash(
    source: str, external_id: str, title: str, company: str, date_posted: datetime | None
) -> str:
    """SHA-256 fingerprint per ARCHITECTURE_DEEP.md."""
    date_str = date_posted.isoformat() if date_posted else ""
    payload = f"{source}{external_id}{title}{company}{date_str}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _map_job_to_raw_record(job: dict) -> RawJobRecord | None:
    """Map a JSearch API job object to RawJobRecord. Returns None if invalid."""
    external_id = job.get("job_id")
    title = job.get("job_title")
    company = job.get("employer_name")

    if not external_id or not title or not company:
        return None

    external_id = str(external_id).strip()
    title = str(title).strip()
    company = str(company).strip()

    if not external_id or not title or not company:
        return None

    date_posted = _parse_date_posted(
        job.get("job_posted_at_timestamp") or job.get("job_posted_at_datetime_utc")
    )
    raw_payload_hash = _compute_raw_payload_hash(SOURCE, external_id, title, company, date_posted)

    # Salary
    salary_min = job.get("job_min_salary")
    salary_max = job.get("job_max_salary")
    if salary_min is not None and not isinstance(salary_min, (int, float)):
        salary_min = None
    if salary_max is not None and not isinstance(salary_max, (int, float)):
        salary_max = None

    return RawJobRecord(
        external_id=external_id,
        source=SOURCE,
        region_id=REGION_ID,
        raw_payload_hash=raw_payload_hash,
        title=title,
        company=company,
        description=str(job.get("job_description") or "").strip() or "",
        city=job.get("job_city") or None,
        state=job.get("job_state") or None,
        country=job.get("job_country") or None,
        is_remote=job.get("job_is_remote") if isinstance(job.get("job_is_remote"), bool) else None,
        date_posted=date_posted,
        salary_raw=None,
        salary_min=float(salary_min) if salary_min is not None else None,
        salary_max=float(salary_max) if salary_max is not None else None,
        salary_currency=job.get("job_salary_currency") or None,
        salary_period=job.get("job_salary_period") or None,
        employment_type=job.get("job_employment_type") or None,
        experience_level=job.get("job_required_experience", {}).get("required_experience_level")
        if isinstance(job.get("job_required_experience"), dict)
        else job.get("job_required_experience"),
        job_url=job.get("job_apply_link") or job.get("job_google_link") or job.get("job_link"),
        source_url=job.get("job_publisher") or "",
        raw_payload=dict(job),
    )


def fetch_jobs(api_key: str) -> list[RawJobRecord]:
    """Fetch up to TARGET_COUNT jobs from JSearch API.

    JSearch returns up to 10 jobs per page. Request num_pages in a single call
    to get multiple pages (e.g. num_pages=20 for up to 200 jobs). Pagination via
    separate page=2, page=3 requests is unreliable for this API.
    """
    records: list[RawJobRecord] = []
    seen_ids: set[str] = set()

    # Request enough pages in one go (10 jobs/page; 20 pages = 200 jobs)
    num_pages = max(1, (TARGET_COUNT + 9) // 10)

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    params = {
        "query": QUERY,
        "page": "1",
        "num_pages": str(min(num_pages, 50)),  # API allows 1-50 pages
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.get(BASE_URL, headers=headers, params=params)

    if resp.status_code != 200:
        print(f"API error: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
        return records

    data = resp.json()
    if data.get("status") != "OK":
        print(f"API returned status: {data.get('status', 'unknown')}", file=sys.stderr)
        return records

    raw = data.get("data") or []
    # API may return a flat list of jobs or a list of pages (each page = list of jobs)
    if raw and isinstance(raw[0], list):
        jobs = [job for page in raw for job in page if isinstance(job, dict)]
    else:
        jobs = [j for j in raw if isinstance(j, dict)]
    for job in jobs:
        if isinstance(job, dict):
            rec = _map_job_to_raw_record(job)
            if rec and rec.external_id not in seen_ids:
                seen_ids.add(rec.external_id)
                records.append(rec)
                if len(records) >= TARGET_COUNT:
                    break

    return records


def main() -> None:
    api_key = os.getenv("JSEARCH_API_KEY", "").strip()
    if not api_key:
        print("Error: JSEARCH_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    records = fetch_jobs(api_key)
    print(f"Fetched {len(records)} job records (target was {TARGET_COUNT}).")

    output_data = [r.model_dump(mode="json") for r in records]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Saved to {OUTPUT_FILE}")

    companies = sorted({r.company for r in records})
    print("\n--- Unique company names (for manual career-page scraping) ---")
    for name in companies:
        print(name)


if __name__ == "__main__":
    main()
