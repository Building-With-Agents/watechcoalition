"""Backward-compatibility shim — use ``agents.normalization.mappers`` instead."""

from agents.normalization.mappers.base import FieldMapper, MapperBase
from agents.normalization.mappers.crawl4ai_indeed import Crawl4AIIndeedMapper
from agents.normalization.mappers.jsearch import JSearchMapper

# Keep the old name importable
ScraperMapper = Crawl4AIIndeedMapper

__all__ = [
    "Crawl4AIIndeedMapper",
    "FieldMapper",
    "JSearchMapper",
    "MapperBase",
    "ScraperMapper",
]
