"""Centralized LLM adapter — cost tracking, audit logging, and guardrails.

All LLM calls across agents MUST go through this adapter so that:
- Every call is logged to the llm_audit_log table
- Token usage and cost are tracked per call
- Extraction outputs are validated against schemas
- Failures are handled with retry and back-off

Week 4 implementation (Juan + Enrique):
- compute_extraction_cost(): per-tier pricing (Sonnet vs Haiku)
- log_extraction_event(): write to llm_audit_log table
- validate_extraction_result(): schema conformance checks + warnings
- handle_extraction_failure(): retry, back-off, SkillsExtractionAlert

Reference: ARCHITECTURE_DEEP.md § Cost Tracking, ARCHITECTURAL_DECISIONS.md
Decision #32 (Model tier routing), Decision #33 (Token cost budget).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def compute_extraction_cost(
    tokens_used: int,
    model_tier: str,
) -> float:
    """Compute the cost of an LLM extraction call.

    Parameters
    ----------
    tokens_used : int
        Total tokens (input + output) consumed by the call.
    model_tier : str
        Model tier identifier: "sonnet" or "haiku".

    Returns
    -------
    float
        Cost in USD as a float (use Decimal internally for precision).
    """
    # Stub — returns 0.0.
    # Week 4: Implement per-tier pricing from env vars (SONNET_COST_PER_1K, HAIKU_COST_PER_1K).
    return 0.0


def log_extraction_event(
    *,
    agent_name: str,
    prompt_hash: str,
    model: str,
    provider: str,
    latency_ms: int,
    token_count: int,
    cost_usd: float,
    success: bool,
    error_reason: str | None = None,
) -> None:
    """Log an LLM call to the llm_audit_log table.

    This function is the single point of audit logging for all LLM calls
    across all agents. It must be called from the adapter, not from
    individual agents.

    Parameters
    ----------
    agent_name : str
        Canonical agent identifier (e.g. "skills-extraction-agent").
    prompt_hash : str
        SHA-256 hash of the prompt sent to the LLM.
    model : str
        Model identifier (e.g. "claude-sonnet-4-5").
    provider : str
        Provider name (e.g. "anthropic", "azure-openai").
    latency_ms : int
        Round-trip latency of the LLM call in milliseconds.
    token_count : int
        Total tokens consumed (input + output).
    cost_usd : float
        Computed cost of this call.
    success : bool
        Whether the call completed successfully.
    error_reason : str | None
        Error description if success is False.
    """
    # Stub — no-op.
    # Week 4: Write to llm_audit_log table via SQLAlchemy.
    pass


def validate_extraction_result(
    result: Any,
    schema_type: str,
) -> list[str]:
    """Validate extraction output against the expected schema.

    Parameters
    ----------
    result : Any
        The extraction output to validate (list of SkillRecord, ToolRecord, etc.).
    schema_type : str
        Which schema to validate against: "skills", "tools", "tasks",
        "responsibilities", "context".

    Returns
    -------
    list[str]
        List of warning messages. Empty list means validation passed.
    """
    # Stub — returns no warnings.
    # Week 4: Check schema conformance, missing fields, low confidence,
    # empty source_span, null esco_uri on non-raw skills.
    return []


def handle_extraction_failure(
    error: Exception,
    agent_name: str,
    retry_count: int = 0,
) -> dict[str, Any]:
    """Handle LLM extraction failures with retry and back-off.

    Parameters
    ----------
    error : Exception
        The exception raised by the LLM call.
    agent_name : str
        Canonical agent identifier.
    retry_count : int
        Number of retries already attempted for this call.

    Returns
    -------
    dict
        Action to take: {"action": "retry", "delay_ms": ...} or
        {"action": "fail", "extraction_failed": True} or
        {"action": "alert", "event": "SkillsExtractionAlert"}.
    """
    # Stub — always returns fail.
    # Week 4: Implement retry once on timeout, exponential back-off on 429,
    # SkillsExtractionAlert after 3 back-off cycles.
    return {"action": "fail", "extraction_failed": True}
