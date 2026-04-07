"""Export a Langfuse dataset back to ground truth JSON.

Round-trip companion to upload_langfuse_dataset.py. Reads dataset items
from Langfuse and writes them as extraction_ground_truth.json format.

Usage:
  python agents/scripts/export_langfuse_dataset.py
  python agents/scripts/export_langfuse_dataset.py --dataset-name my-custom-name --output custom.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_REPO_ROOT / ".env")

from langfuse import Langfuse  # noqa: E402

DEFAULT_DATASET_NAME = "extraction-ground-truth-v1"
DEFAULT_OUTPUT = _REPO_ROOT / "agents" / "eval" / "extraction_ground_truth.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Langfuse dataset to ground truth JSON")
    parser.add_argument(
        "--dataset-name", default=DEFAULT_DATASET_NAME,
        help=f"Langfuse dataset name (default: {DEFAULT_DATASET_NAME})",
    )
    parser.add_argument(
        "--output", default=str(DEFAULT_OUTPUT),
        help=f"Output JSON path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    client = Langfuse()
    dataset = client.get_dataset(args.dataset_name)

    records = []
    for item in dataset.items:
        input_data = item.input or {}
        expected = item.expected_output or {}
        meta = item.metadata or {}

        record = {
            "ground_truth_id": meta.get("ground_truth_id", ""),
            "external_id": meta.get("external_id", ""),
            "source": meta.get("source", "JSearch"),
            "title": input_data.get("title", ""),
            "company": input_data.get("company", ""),
            "city": meta.get("city"),
            "state": meta.get("state"),
            "description": input_data.get("description", ""),
            "requirements": input_data.get("requirements", ""),
            "responsibilities": input_data.get("responsibilities", ""),
            "skills": expected.get("skills", []),
            "tools": expected.get("tools", []),
            "tasks": expected.get("tasks", []),
            "labeled_responsibilities": expected.get("responsibilities", []),
            "context": expected.get("context", []),
            "labeler_notes": {},
        }
        records.append(record)

    # Sort by ground_truth_id for deterministic output
    records.sort(key=lambda r: r.get("ground_truth_id", ""))

    output_path = Path(args.output)
    output_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
