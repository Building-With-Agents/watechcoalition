"""
EXP-003: Exact-Match deduplication tests.

Uses ground_truth_dataset.json to evaluate pure-hash (source + external_id + title
+ company + date_posted) duplicate detection.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def generate_pure_hash(job_record: dict) -> str:
    """Generate a SHA-256 hash for exact-match deduplication.

    Combines source, external_id, title, company, and date_posted. Any null/None
    field is normalized to empty string before hashing to avoid TypeErrors.
    """
    source = job_record.get("source")
    external_id = job_record.get("external_id")
    title = job_record.get("title")
    company = job_record.get("company")
    date_posted = job_record.get("date_posted")

    if source is None:
        source = ""
    else:
        source = str(source)
    if external_id is None:
        external_id = ""
    else:
        external_id = str(external_id)
    if title is None:
        title = ""
    else:
        title = str(title)
    if company is None:
        company = ""
    else:
        company = str(company)
    if date_posted is None:
        date_posted = ""
    else:
        date_posted = str(date_posted)

    payload = f"{source}{external_id}{title}{company}{date_posted}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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


def test_pure_hash_strategy():
    """Load ground truth, compute pure hash per job, track duplicates, print total."""
    dataset_path = Path(__file__).parent / "ground_truth_dataset.json"
    if not dataset_path.exists():
        pytest.skip("ground_truth_dataset.json not found; run fetch_ground_truth.py first")

    try:
        with open(dataset_path, encoding="utf-8") as f:
            jobs = json.load(f)
    except json.JSONDecodeError as e:
        pytest.skip(f"ground_truth_dataset.json is invalid or truncated: {e}")

    # hash -> list of indices (or count); we use list length to count duplicates
    hash_to_indices: dict[str, list[int]] = {}

    for i, job in enumerate(jobs):
        if not isinstance(job, dict):
            continue
        h = generate_pure_hash(job)
        if h not in hash_to_indices:
            hash_to_indices[h] = []
        hash_to_indices[h].append(i)

    # Total duplicates = for each hash with count > 1, (count - 1) are duplicates
    total_duplicates = sum(
        len(indices) - 1 for indices in hash_to_indices.values() if len(indices) > 1
    )

    print(f"\nExact-match (pure hash) strategy: {total_duplicates} duplicate(s) found.")

    assert total_duplicates >= 0, "duplicate count must be non-negative"
    assert len(hash_to_indices) > 0, "expected at least one job in dataset"
