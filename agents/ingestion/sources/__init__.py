"""Source adapters for the Ingestion Agent.

Provides a registry of available source adapters and a factory function
to instantiate them by name.
"""

from agents.ingestion.sources.base_adapter import SourceAdapter
from agents.ingestion.sources.crawl4ai_indeed import Crawl4AIIndeedAdapter
from agents.ingestion.sources.crawl4ai_usajobs import Crawl4AIUSAJobsAdapter
from agents.ingestion.sources.jsearch_adapter import JSearchAdapter

ADAPTER_REGISTRY: dict[str, type[SourceAdapter]] = {
    "jsearch": JSearchAdapter,
    "crawl4ai_indeed": Crawl4AIIndeedAdapter,
    "crawl4ai_usajobs": Crawl4AIUSAJobsAdapter,
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
    "Crawl4AIIndeedAdapter",
    "Crawl4AIUSAJobsAdapter",
    "JSearchAdapter",
    "SourceAdapter",
    "get_adapter",
]
