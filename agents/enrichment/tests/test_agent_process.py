"""Tests for EnrichmentAgent.process()."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent


def _base_payload(**overrides: object) -> dict:
    p = {
        "posting_id": 1,
        "title": "Engineer",
        "company": "Acme",
        "quality_score": 0.8,
        "spam_score": 0.2,
        "seniority": "senior",
        "role_classification": "Software Engineering",
        "skills": [],
        "batch_id": "batch-xyz",
    }
    p.update(overrides)
    return p


def test_process_is_spam_true_spam_rejected() -> None:
    agent = EnrichmentAgent()
    event = EventEnvelope(
        correlation_id="c1",
        agent_id="upstream",
        payload=_base_payload(is_spam=True),
    )
    out = agent.process(event)
    assert out.payload["enriched_count"] == 0
    assert out.payload["spam_rejected_count"] == 1
    assert out.payload["flagged_for_review_count"] == 0


def test_process_is_spam_none_flagged_for_review() -> None:
    agent = EnrichmentAgent()
    event = EventEnvelope(
        correlation_id="c1",
        agent_id="upstream",
        payload=_base_payload(is_spam=None),
    )
    out = agent.process(event)
    assert out.payload["enriched_count"] == 0
    assert out.payload["spam_rejected_count"] == 0
    assert out.payload["flagged_for_review_count"] == 1


@patch("agents.enrichment.agent.resolve_sector", return_value=None)
@patch.object(EnrichmentAgent, "enrich_record")
def test_process_is_spam_false_calls_enrich_once(
    mock_enrich: MagicMock,
    mock_sector: MagicMock,
) -> None:
    mock_enrich.return_value = {"ok": True}
    agent = EnrichmentAgent()
    event = EventEnvelope(
        correlation_id="c1",
        agent_id="upstream",
        payload=_base_payload(is_spam=False),
    )
    out = agent.process(event)

    mock_enrich.assert_called_once()
    assert out.payload["enriched_count"] == 1
    assert out.payload["spam_rejected_count"] == 0
    assert out.payload["flagged_for_review_count"] == 0


@patch("agents.enrichment.agent.resolve_sector", return_value=None)
@patch.object(EnrichmentAgent, "enrich_record")
def test_process_degraded_on_enrich_raises(
    mock_enrich: MagicMock,
    mock_sector: MagicMock,
) -> None:
    mock_enrich.side_effect = RuntimeError("boom")
    agent = EnrichmentAgent()
    event = EventEnvelope(
        correlation_id="c1",
        agent_id="upstream",
        payload=_base_payload(is_spam=False),
    )
    out = agent.process(event)

    assert out.payload["enriched_count"] == 0
    assert out.payload["spam_rejected_count"] == 0
    assert out.payload["flagged_for_review_count"] == 0
