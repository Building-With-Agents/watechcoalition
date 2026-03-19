# ruff: noqa: T201
"""Verify the extraction ground truth dataset.

Usage (from repo root with venv activated):
    python agents/scripts/test_ground_truth.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    gt_path = Path("agents/eval/extraction_ground_truth.json")
    if not gt_path.exists():
        print(f"ERROR: {gt_path} not found")
        return 1

    gt = json.loads(gt_path.read_text())
    print(f"Ground truth records: {len(gt)}")
    if gt:
        print(f"Sample keys: {list(gt[0].keys())}")
        print(f"First title: {gt[0].get('title', 'N/A')}")
    else:
        print("Dataset is empty")
    return 0


if __name__ == "__main__":
    sys.exit(main())
