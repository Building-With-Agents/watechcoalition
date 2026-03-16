"""Backward-compatibility shim — use ``agents.normalization.mappers.crawl4ai_indeed`` instead."""

from agents.normalization.mappers.crawl4ai_indeed import Crawl4AIIndeedMapper  # noqa: F401

# Keep the old name importable
ScraperMapper = Crawl4AIIndeedMapper

__all__ = ["Crawl4AIIndeedMapper", "ScraperMapper"]
