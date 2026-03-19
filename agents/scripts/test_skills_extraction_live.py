# ruff: noqa: T201
"""Live skills extraction test — makes a real LLM call.

Usage (from repo root with venv activated):
    python agents/scripts/test_skills_extraction_live.py
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
    from agents.common.types import JobRecord
    from agents.skills_extraction.extractors.skills import extract_skills

    job = JobRecord(
        raw_job_id=0,
        ingestion_run_id="test",
        region_id="",
        source="test",
        external_id="test-llm",
        title="Machine Learning Engineer",
        company="AI Corp",
        description=(
            "Build ML pipelines using Python, TensorFlow, and PyTorch. "
            "Deploy models on AWS SageMaker. "
            "Experience with MLOps, CI/CD, and Docker required."
        ),
        requirements="5+ years Python, 3+ years deep learning frameworks",
    )

    print("Running live skills extraction (real LLM call)...")
    skills, meta = extract_skills(job, pass1_tools=[])

    success = meta.get("success")
    cost = meta.get("cost_usd", 0)
    print(f"Extracted {len(skills)} skills (success={success}, cost=${cost:.4f})")
    for s in skills:
        print(f"  {s.skill_name:30s}  type={s.type:15s}  confidence={s.confidence:.2f}")

    if not success:
        print(f"\nERROR: {meta.get('error_reason', 'unknown')}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
