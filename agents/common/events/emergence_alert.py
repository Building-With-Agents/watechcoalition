"""EmergenceAlert payload builder for canonical-role clustering (Pair C Week 7).

Orchestration Agent is the sole subscriber for *Alert events (message bus policy).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.analytics.clustering.types import EmergenceCandidate, RankedSkill, RankedTool
from agents.common.event_envelope import EventEnvelope


def _ranked_skills_payload(skills: list[RankedSkill]) -> list[dict[str, Any]]:
    return [{"skill_name": s.skill_name, "count": s.count} for s in skills]


def _ranked_tools_payload(tools: list[RankedTool]) -> list[dict[str, Any]]:
    return [{"tool_name": t.tool_name, "count": t.count} for t in tools]


class EmergenceAlertPayload(BaseModel):
    """Validated payload shape for EmergenceAlert (orchestration-only consumer)."""

    model_config = {"extra": "forbid"}

    event_type: str = Field(default="EmergenceAlert")
    correlation_id: str
    posting_ids: list[str]
    candidate_role_label: str
    posting_count: int
    top_skills: list[dict[str, Any]]
    top_tools: list[dict[str, Any]]
    nearest_canonical_role: str | None = None
    filter_reason: str | None = None
    schema_version: str = "1.0"


def build_emergence_alert_payload(
    candidate: EmergenceCandidate,
    *,
    correlation_id: str,
    cluster_id_to_role_id: dict[str, str],
) -> dict[str, Any]:
    """Map emergence candidate to bus payload; resolve nearest_cluster_id to stable role_id."""
    nearest: str | None = None
    if candidate.nearest_cluster_id:
        nearest = cluster_id_to_role_id.get(candidate.nearest_cluster_id)

    label = (candidate.candidate_role_label or "").strip() or "emergence_candidate"

    body = EmergenceAlertPayload(
        correlation_id=correlation_id,
        posting_ids=list(candidate.posting_ids),
        candidate_role_label=label,
        posting_count=candidate.posting_count,
        top_skills=_ranked_skills_payload(list(candidate.top_skills)),
        top_tools=_ranked_tools_payload(list(candidate.top_tools)),
        nearest_canonical_role=nearest,
        filter_reason=candidate.filter_reason,
    )
    return body.model_dump()


def build_emergence_alert_envelope(
    candidate: EmergenceCandidate,
    *,
    correlation_id: str,
    cluster_id_to_role_id: dict[str, str],
) -> EventEnvelope:
    """Build EventEnvelope for one emergence candidate (analytics-agent produces)."""
    return EventEnvelope(
        correlation_id=correlation_id,
        agent_id="analytics-agent",
        schema_version="1.0",
        payload=build_emergence_alert_payload(
            candidate,
            correlation_id=correlation_id,
            cluster_id_to_role_id=cluster_id_to_role_id,
        ),
    )
