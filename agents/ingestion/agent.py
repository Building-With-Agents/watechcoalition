"""Ingestion agent — ingests from JSearch and Crawl4AI, deduplicates, stages to raw_ingested_jobs."""


def health_check():
    """Return agent health status. Required on every agent."""
    return {"status": "ok", "agent": "ingestion", "last_run": "", "metrics": {}}
