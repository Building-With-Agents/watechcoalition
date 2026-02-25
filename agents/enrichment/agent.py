"""Enrichment agent — role/seniority/quality/spam classifiers, company_id resolution (Phase 1 lite)."""


def health_check():
    """Return agent health status. Required on every agent."""
    return {"status": "ok", "agent": "enrichment", "last_run": "", "metrics": {}}
