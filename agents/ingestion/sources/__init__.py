"""Source adapters for the Ingestion Agent.

Provides a registry of available source adapters and a factory function
to instantiate them by name.
"""

from agents.ingestion.sources.base_adapter import SourceAdapter
from agents.ingestion.sources.jsearch_adapter import JSearchAdapter
from agents.ingestion.sources.scraper_adapter import Crawl4AIAdapter, ScraperAdapter

ADAPTER_REGISTRY: dict[str, type[SourceAdapter]] = {
    "jsearch": JSearchAdapter,
    "crawl4ai": Crawl4AIAdapter,
}


def get_adapter(source_name: str) -> SourceAdapter:
    """Instantiate and return a source adapter by name.

    Raises ``ValueError`` if the source name is not in the registry.
    """
    cls = ADAPTER_REGISTRY.get(source_name)
    if cls is None:
        raise ValueError(f"Unknown source: {source_name!r}. Available: {list(ADAPTER_REGISTRY)}")
    return cls()


__all__ = [
    "ADAPTER_REGISTRY",
    "Crawl4AIAdapter",
    "JSearchAdapter",
    "ScraperAdapter",
    "SourceAdapter",
    "get_adapter",
]
