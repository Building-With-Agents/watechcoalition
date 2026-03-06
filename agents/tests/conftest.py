"""
Shared pytest fixtures for Week 2 Walking Skeleton tests.

Each fixture produces an EventEnvelope matching a specific pipeline stage,
so agent tests can feed the correct upstream event without duplicating setup.
All fixtures use correlation_id="test-1" for traceability.
"""

from __future__ import annotations

import pytest  # noqa: F401

from agents.common.event_envelope import EventEnvelope

# ---------------------------------------------------------------------------
# Raw posting (input to pipeline runner / Ingestion Agent)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_raw_posting() -> dict:
    """A single raw posting matching the fallback_scrape_sample.json shape."""
    return {
        "posting_id": 1,
        "source": "web_scrape",
        "url": "https://careers.microsoft.com/jobs/1234567",
        "timestamp": "2026-02-24T08:15:00Z",
        "title": "Senior Data Engineer",
        "company": "Microsoft",
        "location": "Redmond, WA",
        "raw_text": (
            "Microsoft is hiring a Senior Data Engineer to design and operate "
            "large-scale data pipelines using Python, Apache Spark, and SQL."
        ),
    }


@pytest.fixture
def sample_event(sample_raw_posting: dict) -> EventEnvelope:
    """Raw posting wrapped in an EventEnvelope — the pipeline runner's initial event."""
    return EventEnvelope(
        correlation_id="test-1",
        agent_id="pipeline-runner",
        payload=sample_raw_posting,
    )


# ---------------------------------------------------------------------------
# Stage-specific events (each is the output of the named agent)
# ---------------------------------------------------------------------------

@pytest.fixture
def ingest_event() -> EventEnvelope:
    """Output of IngestionAgent — input to NormalizationAgent."""
    return EventEnvelope(
        correlation_id="test-1",
        agent_id="ingestion-agent",
        payload={
            "event_type": "IngestBatch",
            "posting_id": 1,
            "source": "web_scrape",
            "url": "https://careers.microsoft.com/jobs/1234567",
            "title": "Senior Data Engineer",
            "company": "Microsoft",
            "location": "Redmond, WA",
            "timestamp": "2026-02-24T08:15:00Z",
            "raw_text": "Microsoft is hiring a Senior Data Engineer...",
            "ingestion_run_id": "test-1",
            "ingestion_timestamp": "2026-02-27T00:00:00",
            "raw_payload_hash": "stub-hash",
            "external_id": "1",
        },
    )


@pytest.fixture
def normalization_event() -> EventEnvelope:
    """Output of NormalizationAgent — input to SkillsExtractionAgent."""
    return EventEnvelope(
        correlation_id="test-1",
        agent_id="normalization-agent",
        payload={
            "event_type": "NormalizationComplete",
            "posting_id": 1,
            "title": "Senior Data Engineer",
            "company": "Microsoft",
            "location": "Redmond, WA",
            "normalized_location": "Redmond, WA",
            "employment_type": "full_time",
            "date_posted": "2026-02-24T08:15:00Z",
            "raw_text": "Microsoft is hiring a Senior Data Engineer...",
            "source": "web_scrape",
            "url": "https://careers.microsoft.com/jobs/1234567",
            "normalization_status": "success",
        },
    )


@pytest.fixture
def skills_event() -> EventEnvelope:
    """Output of SkillsExtractionAgent — input to EnrichmentAgent."""
    return EventEnvelope(
        correlation_id="test-1",
        agent_id="skills-extraction-agent",
        payload={
            "event_type": "SkillsExtracted",
            "posting_id": 1,
            "title": "Senior Data Engineer",
            "company": "Microsoft",
            "skills": [
                {"name": "Python", "type": "Technical", "confidence": 0.98},
                {"name": "SQL", "type": "Technical", "confidence": 0.97},
                {"name": "Apache Spark", "type": "Tool", "confidence": 0.95},
            ],
            "seniority": "senior",
            "extraction_status": "success",
            "llm_provider": "stub",
            "llm_model": "stub",
            "llm_call_logged": False,
        },
    )


@pytest.fixture
def enriched_event() -> EventEnvelope:
    """Output of EnrichmentAgent — input to AnalyticsAgent."""
    return EventEnvelope(
        correlation_id="test-1",
        agent_id="enrichment-agent",
        payload={
            "event_type": "RecordEnriched",
            "posting_id": 1,
            "title": "Senior Data Engineer",
            "company": "Microsoft",
            "company_id": "co-microsoft-001",
            "sector_id": "sec-technology",
            "role_classification": "Data Engineering",
            "seniority": "senior",
            "quality_score": 0.91,
            "spam_score": 0.04,
            "is_spam": False,
            "enrichment_status": "success",
            "skills": [
                {"name": "Python", "type": "Technical", "confidence": 0.98},
                {"name": "SQL", "type": "Technical", "confidence": 0.97},
            ],
        },
    )


@pytest.fixture
def analytics_event() -> EventEnvelope:
    """Output of AnalyticsAgent — input to VisualizationAgent."""
    return EventEnvelope(
        correlation_id="test-1",
        agent_id="analytics-agent",
        payload={
            "event_type": "AnalyticsRefreshed",
            "triggered_by_posting_id": 1,
            "run_id": "batch-run-001",
            "total_postings": 10,
            "top_skills": [
                {"skill": "Python", "count": 10, "type": "Technical"},
            ],
            "seniority_distribution": {"junior": 2, "mid": 4, "senior": 3, "lead": 1},
        },
    )


@pytest.fixture
def render_event() -> EventEnvelope:
    """Output of VisualizationAgent — input to OrchestrationAgent."""
    return EventEnvelope(
        correlation_id="test-1",
        agent_id="visualization-agent",
        payload={
            "event_type": "RenderComplete",
            "triggered_by_posting_id": 1,
            "pages_rendered": [
                "Pipeline Run Summary",
                "Record Journey",
                "Batch Insights",
            ],
            "render_status": "success",
            "export_formats_available": ["pdf", "csv", "json"],
            "stub": True,
        },
    )
