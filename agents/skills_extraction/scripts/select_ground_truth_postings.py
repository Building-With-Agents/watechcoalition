#!/usr/bin/env python3
"""Select a set of job postings for ground-truth labeling (eval harness).

Reads from a fixture or list of posting IDs and prints selected IDs (e.g. 30–50)
for human labeling. Usage:

  python -m agents.skills_extraction.scripts.select_ground_truth_postings
  python -m agents.skills_extraction.scripts.select_ground_truth_postings --limit 40
  python -m agents.skills_extraction.scripts.select_ground_truth_postings --fixture path/to/fixture.json

Output: one posting_id per line, suitable for feeding into an eval labeling workflow.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import structlog


def main() -> None:
    parser = argparse.ArgumentParser(description="Select postings for ground-truth labeling")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path(__file__).parent.parent.parent / "data" / "fixtures" / "fixture_skills_extracted.json",
        help="JSON array of postings with posting_id (or similar).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max number of posting IDs to output (default 50).",
    )
    parser.add_argument(
        "--id-key",
        default="posting_id",
        help="Key for posting ID in each object (default: posting_id).",
    )
    args = parser.parse_args()

    log = structlog.get_logger()
    if not args.fixture.exists():
        log.error("fixture_not_found", path=str(args.fixture))
        return

    with args.fixture.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    ids = []
    for item in data:
        if isinstance(item, dict) and args.id_key in item:
            ids.append(item[args.id_key])
        if len(ids) >= args.limit:
            break

    for pid in ids[: args.limit]:
        sys.stdout.write(f"{pid}\n")


if __name__ == "__main__":
    main()
