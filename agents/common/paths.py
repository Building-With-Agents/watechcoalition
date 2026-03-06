"""
Shared path constants for agents (staging, data dirs).
Single source of truth so scraper and dashboard stay in sync.
"""
from pathlib import Path

_THIS_FILE = Path(__file__).resolve()
_AGENTS_ROOT = _THIS_FILE.parents[1]  # agents/common -> agents/

STAGING_DIR = _AGENTS_ROOT / "data" / "staging"
RAW_SCRAPE_SAMPLE_PATH = STAGING_DIR / "raw_scrape_sample.json"

# Fixtures for walking skeleton (Task 2.2) — single source of truth for agent stubs
FIXTURES_DIR = _AGENTS_ROOT / "data" / "fixtures"
FALLBACK_SCRAPE_PATH = FIXTURES_DIR / "fallback_scrape_sample.json"
FIXTURE_SKILLS_EXTRACTED_PATH = FIXTURES_DIR / "fixture_skills_extracted.json"
FIXTURE_ENRICHED_PATH = FIXTURES_DIR / "fixture_enriched.json"
FIXTURE_ANALYTICS_REFRESHED_PATH = FIXTURES_DIR / "fixture_analytics_refreshed.json"

# Pipeline runner output (Task 2.3)
OUTPUT_DIR = _AGENTS_ROOT / "data" / "output"
PIPELINE_RUN_JSON = OUTPUT_DIR / "pipeline_run.json"
