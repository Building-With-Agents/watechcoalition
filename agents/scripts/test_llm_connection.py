"""Test that the skills-extraction LLM (Azure OpenAI) can be created and invoked.

Usage (from repo root with venv activated):
  python -m agents.scripts.test_llm_connection

Requires: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and one of
  AZURE_OPENAI_DEPLOYMENT_NAME, EXTRACTION_DEPLOYMENT_SKILLS, EXTRACTION_MODEL_SKILLS.
"""
# ruff: noqa: T201  # CLI script; print to stdout is intentional

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Load .env from repo root so Azure vars are available
try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


def main() -> int:
    from agents.common.llm_client import _get_llm, invoke_skills_llm

    print("Testing LLM connection for skills extraction...")
    print()

    # 1. Build the model (validates env vars)
    try:
        llm = _get_llm()
        deployment = (
            getattr(llm, "azure_deployment", None)
            or getattr(llm, "deployment_name", None)
            or getattr(llm, "model_name", None)
            or os.getenv("EXTRACTION_DEPLOYMENT_SKILLS")
            or os.getenv("EXTRACTION_MODEL_SKILLS")
            or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            or "unknown"
        )
        print(f"  LLM created successfully. Deployment: {deployment}")
    except ValueError as e:
        print(f"  ERROR (config): {e}")
        return 1
    except ImportError as e:
        print(f"  ERROR (import): {e}")
        return 1

    # 2. One minimal invoke
    print("  Invoking LLM with prompt: 'Reply with exactly: OK' ...")
    try:
        text, meta = invoke_skills_llm("Reply with exactly: OK")
        print(f"  Response: {repr(text)}")
        print(
            f"  Meta: success={meta.get('success')}, tokens_used={meta.get('tokens_used')}, cost_usd={meta.get('cost_usd')}, latency_ms={meta.get('latency_ms')}"
        )
        if not meta.get("success"):
            print(f"  ERROR: {meta.get('error_reason', 'unknown')}")
            return 1
        print()
        print("  LLM API test passed.")
        return 0
    except Exception as e:
        print(f"  ERROR (invoke): {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
