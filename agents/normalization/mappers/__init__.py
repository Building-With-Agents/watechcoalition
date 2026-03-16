"""Normalization mappers — registry and factory.

Provides a registry of per-source field mappers and a factory function
to look them up by source name.
"""

from agents.normalization.mappers.base import MapperBase
from agents.normalization.mappers.crawl4ai_indeed import Crawl4AIIndeedMapper
from agents.normalization.mappers.jsearch import JSearchMapper

MAPPER_REGISTRY: dict[str, MapperBase] = {
    "jsearch": JSearchMapper(),
    "crawl4ai": Crawl4AIIndeedMapper(),
}


def get_mapper(source_name: str) -> MapperBase | None:
    """Return the mapper for a given source, or None if not registered."""
    return MAPPER_REGISTRY.get(source_name)


__all__ = [
    "Crawl4AIIndeedMapper",
    "JSearchMapper",
    "MAPPER_REGISTRY",
    "MapperBase",
    "get_mapper",
]
