# agents/common/events/catalog.py
"""Phase 1 event type names and payload contracts. No Phase 2 events (DemandSignalsUpdated, DemandAnomaly) here."""

# Event type constants — use these for subscription and routing
INGEST_BATCH = "IngestBatch"
NORMALIZATION_COMPLETE = "NormalizationComplete"
SKILLS_EXTRACTED = "SkillsExtracted"
RECORD_ENRICHED = "RecordEnriched"
ANALYTICS_REFRESHED = "AnalyticsRefreshed"
RENDER_COMPLETE = "RenderComplete"

# Failure / alert events — Orchestrator is sole consumer
SOURCE_FAILURE = "SourceFailure"
NORMALIZATION_FAILED = "NormalizationFailed"
SKILLS_EXTRACTION_FAILED = "SkillsExtractionFailed"
ENRICHMENT_FAILED = "EnrichmentFailed"
ANALYTICS_FAILED = "AnalyticsFailed"
RENDER_FAILED = "RenderFailed"
VISUALIZATION_DEGRADED = "VisualizationDegraded"
ALERT = "Alert"
