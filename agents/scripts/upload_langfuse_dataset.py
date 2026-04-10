"""Upload ground truth extraction data to Langfuse as a dataset.

Creates (or updates) a Langfuse dataset with labeled job postings from
agents/eval/extraction_ground_truth.json for annotation and evaluation.

Prerequisites:
  - Langfuse running at LANGFUSE_BASE_URL (local Docker or cloud)
  - LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY set in .env

Usage:
  python agents/scripts/upload_langfuse_dataset.py
  python agents/scripts/upload_langfuse_dataset.py --dataset-name my-custom-name
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
GT_PATH = _REPO_ROOT / "agents" / "eval" / "extraction_ground_truth.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload ground truth to Langfuse dataset")
    parser.add_argument(
        "--dataset-name", default=DEFAULT_DATASET_NAME,
        help=f"Langfuse dataset name (default: {DEFAULT_DATASET_NAME})",
    )
    args = parser.parse_args()

    client = Langfuse()

    # Create or get dataset (idempotent)
    client.create_dataset(name=args.dataset_name)

    with open(GT_PATH, encoding="utf-8") as f:
        records = json.load(f)

    for record in records:
        # Input: the job posting text (what the LLM sees)
        input_data = {
            "title": record.get("title", ""),
            "company": record.get("company", ""),
            "description": record.get("description", ""),
            "requirements": record.get("requirements", ""),
            "responsibilities": record.get("responsibilities", ""),
        }
        # Expected output: the labeled extractions
        expected_output = {
            "skills": record.get("skills", []),
            "tools": record.get("tools", []),
            "tasks": record.get("tasks", []),
            "responsibilities": record.get("labeled_responsibilities", []),
            "context": record.get("context", []),
        }

        client.create_dataset_item(
            dataset_name=args.dataset_name,
            input=input_data,
            expected_output=expected_output,
            metadata={
                "ground_truth_id": record.get("ground_truth_id", ""),
                "external_id": record.get("external_id", ""),
                "source": record.get("source", ""),
            },
        )

    client.flush()


if __name__ == "__main__":
    main()
