"""Skills extraction agent — taxonomy linking, LLM extraction, raw_skill fallback."""


def health_check():
    """Return agent health status. Required on every agent."""
    return {"status": "ok", "agent": "skills_extraction", "last_run": "", "metrics": {}}
