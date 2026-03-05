"""
Pipeline config from environment only. No secrets in code; safe path resolution.

This package path is the canonical import target for walking-skeleton config
helpers because `agents.common.config` resolves to this package, not the
adjacent legacy `config.py` module.
"""

from __future__ import annotations

import os
from pathlib import Path


def _agents_root() -> Path:
    """Repo root: directory containing the `agents` package."""
    return Path(__file__).resolve().parents[2]


def get_fixture_path(env_var: str, default_relative: str) -> Path:
    """
    Resolve a fixture path from env or default under `agents/data/fixtures`.

    Absolute paths and parent traversal are rejected so fixture overrides stay
    scoped to the checked-in fixtures directory.
    """
    base = _agents_root() / "data" / "fixtures"
    raw = os.getenv(env_var)
    if raw:
        if Path(raw).is_absolute():
            return base / default_relative
        resolved = (base / raw).resolve()
        try:
            resolved.relative_to(base)
        except ValueError:
            return base / default_relative
        if resolved.is_file():
            return resolved
    return base / default_relative


DEFAULT_INPUT_FIXTURE = "fallback_scrape_sample.json"
FIXTURE_SKILLS_EXTRACTED = "fixture_skills_extracted.json"
FIXTURE_ENRICHED = "fixture_enriched.json"
FIXTURE_ANALYTICS_REFRESHED = "fixture_analytics_refreshed.json"

ENV_PIPELINE_INPUT = "PIPELINE_INPUT_PATH"

__all__ = [
    "DEFAULT_INPUT_FIXTURE",
    "ENV_PIPELINE_INPUT",
    "FIXTURE_ANALYTICS_REFRESHED",
    "FIXTURE_ENRICHED",
    "FIXTURE_SKILLS_EXTRACTED",
    "get_fixture_path",
]
