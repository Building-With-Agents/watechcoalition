# ruff: noqa: T201
"""Interactive taxonomy resolution test.

Usage (from repo root with venv activated):
    python agents/scripts/test_taxonomy_resolution.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


def main() -> int:
    from agents.skills_extraction.extractors.taxonomy import (
        resolution_stats,
        resolve_taxonomy,
        resolve_taxonomy_batch,
    )

    result = resolve_taxonomy("Python")
    print(f"Python -> step {result.resolution_step}, esco_uri={result.esco_uri}, confidence={result.confidence:.2f}")

    labels = ["Python", "Machine Learning", "React", "nonexistent-skill-xyz"]
    results = resolve_taxonomy_batch(labels)
    for label, res in zip(labels, results, strict=True):
        uri = res.esco_uri or "(unresolved)"
        print(f"  {label:30s} -> step {res.resolution_step}, uri={uri}")

    stats = resolution_stats(results)
    print(f"Coverage: {stats['coverage']:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
