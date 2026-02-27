"""
Tests for the Crawl4AI scraper adapter

Covers _get_targets, _extract_postings, and OUTPUT_PATH without invoking Crawl4AI/Playwright.
"""

import os
from unittest.mock import patch

import pytest

from agents.ingestion.sources.scraper_adapter import (
    DEFAULT_SCRAPING_TARGETS,
    OUTPUT_PATH,
    _extract_postings,
    _get_targets,
)


def test_get_targets_uses_default_when_env_empty() -> None:
    with patch.dict(os.environ, {"SCRAPING_TARGETS": ""}, clear=False):
        assert _get_targets() == DEFAULT_SCRAPING_TARGETS


def test_get_targets_uses_env_when_set() -> None:
    with patch.dict(os.environ, {"SCRAPING_TARGETS": "https://example.com/jobs, https://other.com"}, clear=False):
        got = _get_targets()
    assert got == ["https://example.com/jobs", "https://other.com"]


def test_get_targets_strips_whitespace_and_skips_empty() -> None:
    with patch.dict(os.environ, {"SCRAPING_TARGETS": "  a  ,  ,  b  "}, clear=False):
        assert _get_targets() == ["a", "b"]


def test_extract_postings_returns_records_with_expected_keys() -> None:
    url = "https://jobs.lever.co/test"
    markdown = "\n\n".join(
        [
            "Short.",
            "A" * 100,
            "B" * 100,
        ]
    )
    postings = _extract_postings(url, markdown, max_per_page=5)
    assert len(postings) == 2  # only sections > 80 chars
    for p in postings:
        assert p["source"] == "crawl4ai"
        assert p["url"] == url
        assert "timestamp" in p
        assert "raw_text" in p
        assert len(p["raw_text"]) > 80


def test_extract_postings_respects_max_per_page() -> None:
    url = "https://example.com"
    markdown = "\n\n".join(["X" * 90] * 10)
    postings = _extract_postings(url, markdown, max_per_page=3)
    assert len(postings) == 3


def test_output_path_under_data_staging() -> None:
    assert "data" in str(OUTPUT_PATH)
    assert "staging" in str(OUTPUT_PATH)
    assert OUTPUT_PATH.name == "raw_scrape_sample.json"
