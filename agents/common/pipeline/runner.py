"""
Single sequential pipeline runner for all agents.

- One correlation_id per run.
- Depends on BaseAgent and get_stages(); no concrete agent imports here.
- Add or reorder agents in pipeline/stages.py; this file stays unchanged (Open/Closed).
- Graceful failure: on None or exception, log and return events collected so far.
- Config from environment only; no secrets in logs.
"""

import uuid
from typing import Any

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.events.base import AgentEvent
from agents.common.pipeline.stages import get_stages

log = structlog.get_logger()


def _all_agents() -> list[BaseAgent]:
    """Return agent instances in pipeline order (for health_check or runner)."""
    return [stage() for stage in get_stages()]


def health_check_all() -> dict[str, dict[str, Any]]:
    """
    Call health_check() on every agent. Used by the runner before a run and by
    the Operations dashboard. Returns a dict mapping agent_id -> health_check result.
    """
    result: dict[str, dict[str, Any]] = {}
    for agent in _all_agents():
        try:
            h = agent.health_check()
            result[h.get("agent", "unknown")] = h
        except Exception as e:
            log.warning(
                "agent_health_check_failed",
                agent_id=agent.agent_id,
                error_type=type(e).__name__,
            )
            result[agent.agent_id] = {"status": "down", "error": type(e).__name__}
    return result


def run_pipeline(skip_health_check: bool = False) -> list[dict[str, Any]]:
    """
    Run the full pipeline once in STAGES order. Returns a list of event dicts
    (to_dict()) for the Journey dashboard. On agent failure (None or exception),
    logs and returns events collected so far instead of raising.
    """
    correlation_id = f"run-{uuid.uuid4().hex[:12]}"
    events_out: list[dict[str, Any]] = []
    log.info("pipeline_run_start", correlation_id=correlation_id)

    health: dict[str, dict[str, Any]] = {}
    if not skip_health_check:
        health = health_check_all()

    prev: AgentEvent | None = None
    for agent in _all_agents():
        try:
            # Ingestion gets no input event and needs correlation_id; others get prev event.
            next_ev = (
                agent.process(None, correlation_id=correlation_id)
                if prev is None
                else agent.process(prev)
            )
            if next_ev is None:
                agent_id = agent.AGENT_ID
                log.error(
                    "pipeline_stopped",
                    agent_id=agent_id,
                    correlation_id=correlation_id,
                    reason="no_event",
                )
                return events_out
            events_out.append(next_ev.to_dict())
            prev = next_ev
            # One line per stage: agent, health status, and event id for traceability.
            status = health.get(agent.agent_id, {}).get("status", "?") if health else "?"
            log.info(
                "pipeline_stage_done",
                agent_id=agent.agent_id,
                status=status,
                event_id=next_ev.event_id,
                correlation_id=correlation_id,
            )
        except Exception as e:
            agent_id = agent.AGENT_ID
            log.exception(
                "pipeline_step_failed",
                agent_id=agent_id,
                correlation_id=correlation_id,
                error_type=type(e).__name__,
            )
            return events_out

    log.info(
        "pipeline_run_complete",
        correlation_id=correlation_id,
        event_count=len(events_out),
    )
    return events_out
