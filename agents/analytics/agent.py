"""Analytics agent — aggregates, text-to-SQL guardrails, weekly insights."""


def health_check():
    """Return agent health status. Required on every agent."""
    return {"status": "ok", "agent": "analytics", "last_run": "", "metrics": {}}
