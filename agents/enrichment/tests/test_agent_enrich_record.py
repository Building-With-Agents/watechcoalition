"""Tests for EnrichmentAgent.enrich_record."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agents.enrichment.agent import EnrichmentAgent


@patch("agents.enrichment.agent.compute_overall_confidence")
@patch("agents.enrichment.agent.compute_field_confidence")
@patch("agents.enrichment.agent.resolve_location")
@patch("agents.enrichment.agent.resolve_company")
def test_enrich_record_happy_path_has_required_keys(
    mock_resolve_company: MagicMock,
    mock_resolve_location: MagicMock,
    mock_field_confidence: MagicMock,
    mock_overall_confidence: MagicMock,
) -> None:
    mock_resolve_company.return_value = (101, 0.95)
    mock_resolve_location.return_value = (7, 0.90, None, None)
    mock_field_confidence.return_value = {
        "company_id": 0.95,
        "location_id": 0.90,
        "sector_id": 0.0,
        "seniority": 0.0,
    }
    mock_overall_confidence.return_value = 0.88

    agent = EnrichmentAgent()
    posting = {
        "company": "Acme Inc.",
        "location": "Seattle, WA",
        "quality_score": 0.9,
    }
    session = MagicMock()
    out = agent.enrich_record(posting, session)

    assert out["company_id"] == 101
    assert out["company_id"] is not None
    assert out["location_id"] == 7
    assert out["raw_location_text"] is None
    assert out["borderplex_subregion"] is None
    assert out["field_confidence"] == mock_field_confidence.return_value
    assert out["overall_confidence"] == 0.88
    assert out["company"] == "Acme Inc."
    assert "enrichment_status" not in out

    mock_resolve_company.assert_called_once_with("Acme Inc.", session)
    mock_resolve_location.assert_called_once_with("Seattle, WA", session)


@patch("agents.enrichment.agent.compute_overall_confidence")
@patch("agents.enrichment.agent.compute_field_confidence")
@patch("agents.enrichment.agent.resolve_location")
@patch("agents.enrichment.agent.resolve_company")
def test_enrich_record_degraded_on_resolve_company_failure(
    mock_resolve_company: MagicMock,
    mock_resolve_location: MagicMock,
    mock_field_confidence: MagicMock,
    mock_overall_confidence: MagicMock,
) -> None:
    mock_resolve_company.side_effect = RuntimeError("db unavailable")

    agent = EnrichmentAgent()
    posting = {"company": "Broken Co", "location": "X"}
    out = agent.enrich_record(posting, MagicMock())

    assert out["enrichment_status"] == "degraded"
    assert out["overall_confidence"] == 0.0
    assert out["company_id"] is None
    assert out["location_id"] is None
    assert out["field_confidence"] == {
        "company_id": 0.0,
        "location_id": 0.0,
        "sector_id": 0.0,
        "seniority": 0.0,
    }
    mock_resolve_location.assert_not_called()
    mock_field_confidence.assert_not_called()
    mock_overall_confidence.assert_not_called()
