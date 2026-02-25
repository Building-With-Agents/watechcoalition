"""Orchestration agent — scheduler, retries, sole consumer of *Failed/*Alert events."""


def health_check():
    """Return agent health status. Required on every agent."""
    return {"status": "ok", "agent": "orchestration", "last_run": "", "metrics": {}}
