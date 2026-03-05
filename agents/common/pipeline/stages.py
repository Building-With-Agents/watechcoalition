"""
Pipeline stage list: the single place that knows concrete agent types.

- Add or reorder agents here; the runner stays unchanged (Open/Closed).
- Runner depends only on BaseAgent + this module.
"""

from agents.analytics.agent import AnalyticsAgent
from agents.common.base_agent import BaseAgent
from agents.enrichment.agent import EnrichmentAgent
from agents.ingestion.agent import IngestionAgent
from agents.normalization.agent import NormalizationAgent
from agents.skills_extraction.agent import SkillsExtractionAgent
from agents.visualization.agent import VisualizationAgent


def get_stages() -> list[type[BaseAgent]]:
    """Return the ordered list of agent classes for the pipeline. Extend or reorder here."""
    return [
        IngestionAgent,
        NormalizationAgent,
        SkillsExtractionAgent,
        EnrichmentAgent,
        AnalyticsAgent,
        VisualizationAgent,
    ]
