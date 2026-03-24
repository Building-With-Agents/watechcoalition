"""Legacy extraction eval CLI — stub extractor only (no skills_extraction imports).

Usage:
    python -m agents.eval.extraction_eval
"""

from __future__ import annotations

from pathlib import Path

from agents.eval.extraction_eval_core import run_eval_legacy_console

GROUND_TRUTH_PATH = Path(__file__).parent / "extraction_ground_truth.json"


def run_eval(ground_truth_path: str | Path) -> None:
    run_eval_legacy_console(ground_truth_path)


if __name__ == "__main__":
    run_eval(GROUND_TRUTH_PATH)
