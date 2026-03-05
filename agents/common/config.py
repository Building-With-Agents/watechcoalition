"""
Pipeline config from environment only. No secrets in code; safe path resolution.
"""

import os
from pathlib import Path


def _agents_root() -> Path:
    """Repo root: directory containing 'agents' package (parent of this file's parent)."""
    return Path(__file__).resolve().parent.parent


def get_fixture_path(env_var: str, default_relative: str) -> Path:
    """
    Resolve a fixture path from env or default. Prevents path traversal:
    only returns paths under agents/data/fixtures/.
    """
    base = _agents_root() / "data" / "fixtures"
    raw = os.getenv(env_var)
    if raw:
        # If absolute path, reject (could escape fixtures dir)
        if Path(raw).is_absolute():
            return base / default_relative
        p = (base / raw).resolve()
        try:
            p.relative_to(base)
        except ValueError:
            return base / default_relative
        if p.is_file():
            return p
    return base / default_relative


# Default fixture names (under agents/data/fixtures/)
DEFAULT_INPUT_FIXTURE = "fallback_scrape_sample.json"
FIXTURE_SKILLS_EXTRACTED = "fixture_skills_extracted.json"
FIXTURE_ENRICHED = "fixture_enriched.json"
FIXTURE_ANALYTICS_REFRESHED = "fixture_analytics_refreshed.json"

# Env var for walking skeleton input (optional)
ENV_PIPELINE_INPUT = "PIPELINE_INPUT_PATH"
