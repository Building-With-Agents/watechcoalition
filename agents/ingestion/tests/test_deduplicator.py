"""
EXP-003: Deduplication experiment tests.

Evaluates:
- Pure exact hash: platform-level only, cannot detect cross-source duplicates
- Hybrid: exact + logical (title+company+date_posted) for cross-source detection
- Database enforcement: simulated UNIQUE constraint rejects duplicates (INSERT ON CONFLICT DO NOTHING)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def generate_pure_hash(job_record: dict) -> str:
    """Exact-match hash: sha256(source + external_id + title + company + date_posted).

    Platform-level uniqueness only; cannot detect cross-source duplicates.
    """
    source = job_record.get("source")
    external_id = job_record.get("external_id")
    title = job_record.get("title")
    company = job_record.get("company")
    date_posted = job_record.get("date_posted")
    source = "" if source is None else str(source)
    external_id = "" if external_id is None else str(external_id)
    title = "" if title is None else str(title)
    company = "" if company is None else str(company)
    date_posted = "" if date_posted is None else str(date_posted)
    payload = f"{source}{external_id}{title}{company}{date_posted}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_logical_hash(job_record: dict) -> str:
    """Logical hash for cross-source detection: sha256(normalized_title + normalized_company + date_posted).

    Normalization: lowercase, strip whitespace. Used to detect same job across sources.
    """
    title = job_record.get("title")
    company = job_record.get("company")
    date_posted = job_record.get("date_posted")
    title = "" if title is None else str(title)
    company = "" if company is None else str(company)
    date_posted = "" if date_posted is None else str(date_posted)
    normalized_title = title.lower().strip()
    normalized_company = company.lower().strip()
    payload = f"{normalized_title}{normalized_company}{date_posted}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class RawIngestedJobsTableSimulator:
    """Simulates raw_ingested_jobs table UNIQUE(raw_payload_hash) and INSERT ... ON CONFLICT DO NOTHING.

    For EXP-003 spike only; not production code.
    """

    def __init__(self) -> None:
        self.unique_payload_hashes: set[str] = set()

    def insert_on_conflict_do_nothing(self, payload_hash: str) -> bool:
        """Simulate INSERT ... ON CONFLICT (raw_payload_hash) DO NOTHING.

        Returns True if insert succeeded (hash was new), False if duplicate (conflict).
        """
        if payload_hash in self.unique_payload_hashes:
            return False
        self.unique_payload_hashes.add(payload_hash)
        return True


def test_generate_pure_hash_normalizes_none():
    """Null/None fields are normalized to empty string before hashing (no TypeError)."""
    job = {
        "source": "JSearch",
        "external_id": "abc",
        "title": "Engineer",
        "company": "Acme",
        "date_posted": None,
    }
    h = generate_pure_hash(job)
    assert isinstance(h, str)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_generate_pure_hash_deterministic():
    """Same inputs produce the same hash."""
    job = {"source": "JSearch", "external_id": "1", "title": "Dev", "company": "Co", "date_posted": "2026-01-01"}
    assert generate_pure_hash(job) == generate_pure_hash(job)


def test_generate_logical_hash_normalization():
    """Logical hash normalizes title/company (lowercase, strip) and ignores source/external_id."""
    job1 = {"source": "JSearch", "external_id": "a", "title": " Engineer ", "company": "ACME", "date_posted": "2026-01-01"}
    job2 = {"source": "costco.com", "external_id": "b", "title": "engineer", "company": "acme", "date_posted": "2026-01-01"}
    assert generate_logical_hash(job1) == generate_logical_hash(job2)
    assert generate_pure_hash(job1) != generate_pure_hash(job2)


def _load_ground_truth() -> list[dict]:
    """Load ground_truth_dataset.json; skip if missing or invalid."""
    dataset_path = Path(__file__).parent / "ground_truth_dataset.json"
    if not dataset_path.exists():
        pytest.skip("ground_truth_dataset.json not found; run fetch_ground_truth.py first")
    try:
        with open(dataset_path, encoding="utf-8") as f:
            jobs = json.load(f)
    except json.JSONDecodeError as e:
        pytest.skip(f"ground_truth_dataset.json is invalid or truncated: {e}")
    return [j for j in jobs if isinstance(j, dict)]


def test_pure_hash_strategy():
    """Pure exact hash detects 0 duplicates (cross-source blind spot)."""
    jobs = _load_ground_truth()
    hash_to_indices: dict[str, list[int]] = {}
    for i, job in enumerate(jobs):
        h = generate_pure_hash(job)
        hash_to_indices.setdefault(h, []).append(i)
    total_duplicates = sum(len(indices) - 1 for indices in hash_to_indices.values() if len(indices) > 1)
    assert total_duplicates == 0, "pure exact hash cannot detect cross-source duplicates; expected 0"
    assert len(hash_to_indices) > 0, "expected at least one job in dataset"


def test_hybrid_strategy():
    """Hybrid (exact + logical hash) detects 5 cross-source duplicates."""
    jobs = _load_ground_truth()
    exact_seen: set[str] = set()
    logical_seen: set[str] = set()
    duplicate_count = 0
    for job in jobs:
        exact_hash = generate_pure_hash(job)
        logical_hash = generate_logical_hash(job)
        if exact_hash in exact_seen or logical_hash in logical_seen:
            duplicate_count += 1
        else:
            exact_seen.add(exact_hash)
            logical_seen.add(logical_hash)
    # Expected: 5 cross-source duplicates (Costco, SAIC, Allied Universal, TravelCenters, Rockforce).
    # Actual count depends on dataset: injected records must match JSearch base on title+company+date_posted.
    assert duplicate_count >= 5, f"hybrid strategy should detect cross-source duplicates; got {duplicate_count}"


def test_database_enforcement_layer():
    """Simulated DB UNIQUE(raw_payload_hash) + INSERT ON CONFLICT DO NOTHING rejects 5 cross-source duplicates."""
    table_sim = RawIngestedJobsTableSimulator()
    dedup_counter = 0
    jobs = _load_ground_truth()
    for job in jobs:
        title = job.get("title")
        company = job.get("company")
        date_posted = job.get("date_posted")
        title = "" if title is None else str(title).strip().lower()
        company = "" if company is None else str(company).strip().lower()
        date_posted = "" if date_posted is None else str(date_posted).strip().lower()
        payload = f"{title}{company}{date_posted}"
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if not table_sim.insert_on_conflict_do_nothing(payload_hash):
            dedup_counter += 1
    # 5 = injected cross-source duplicates; dataset may have additional same-logical-identity rows (e.g. within JSearch)
    assert dedup_counter >= 5, f"simulated DB enforcement should reject at least 5 duplicates; got {dedup_counter}"
