"""Normalization agent — maps source fields to canonical JobRecord, quarantines violations."""


def health_check():
    """Return agent health status. Required on every agent."""
    return {"status": "ok", "agent": "normalization", "last_run": "", "metrics": {}}
