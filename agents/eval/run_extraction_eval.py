# ruff: noqa: T201
"""CLI: run extraction eval with optional snapshot + prompt backlog artifacts.

Usage (repo root, venv active):
    python -m agents.eval.run_extraction_eval --mode stub
    python -m agents.eval.run_extraction_eval --mode pipeline --label my-run --limit 5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agents.eval.extraction_eval_core import (
    load_ground_truth,
    print_console,
    run_eval_dataset,
)

_DEFAULT_GT = Path(__file__).resolve().parent / "extraction_ground_truth.json"
_DEFAULT_RUNS = Path(__file__).resolve().parent / "runs"
_DEFAULT_BACKLOG = Path(__file__).resolve().parent / "prompt_backlog"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run extraction eval (stub or pipeline).")
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=_DEFAULT_GT,
        help="Path to extraction_ground_truth.json",
    )
    parser.add_argument(
        "--mode",
        choices=("stub", "pipeline"),
        default="stub",
        help="stub: keyword heuristic; pipeline: Pass-1 tools + LLM skills (needs Azure env)",
    )
    parser.add_argument("--label", default="", help="Tag for backlog/snapshot filenames")
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only first N jobs")
    parser.add_argument(
        "--output-runs-dir",
        type=Path,
        default=_DEFAULT_RUNS,
        help="Directory for JSON snapshots",
    )
    parser.add_argument(
        "--output-backlog-dir",
        type=Path,
        default=_DEFAULT_BACKLOG,
        help="Directory for Markdown prompt backlog files",
    )
    parser.add_argument(
        "--no-artifacts",
        action="store_true",
        help="Print metrics only; do not write runs/ or prompt_backlog/",
    )
    args = parser.parse_args(argv)

    if not args.ground_truth.exists():
        print(f"ERROR: ground truth not found: {args.ground_truth}", file=sys.stderr)
        return 1

    data = load_ground_truth(args.ground_truth)
    result = run_eval_dataset(
        data,
        mode=args.mode,
        limit=args.limit,
        ground_truth_path=str(args.ground_truth.resolve()),
        run_label=args.label,
        write_artifacts=not args.no_artifacts,
        output_runs_dir=args.output_runs_dir if not args.no_artifacts else None,
        output_backlog_dir=args.output_backlog_dir if not args.no_artifacts else None,
    )
    print_console(result.console_lines)

    if result.snapshot_path and result.backlog_path:
        print(f"\nWrote snapshot: {result.snapshot_path}")
        print(f"Wrote backlog:  {result.backlog_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
