"""Unit tests for employer_classifier (defensive defaults + sector canonicalization)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agents.common.types.job_profile import EmployerProfile
from agents.enrichment.classifiers.employer_classifier import (
    EmployerClassificationLLMOutput,
    _canonical_sector,
    build_employer_profile,
    persist_employer_metadata,
    registry_has_exact_company_name,
)


def test_canonical_sector_known_and_alias() -> None:
    assert _canonical_sector("Technology") == "technology"
    assert _canonical_sector("TECH") == "technology"
    assert _canonical_sector("tech") == "technology"
    assert _canonical_sector("  ") == "unknown"
    assert _canonical_sector("made-up-industry") == "unknown"


def test_registry_has_exact_company_name_false_when_empty_session_unused() -> None:
    session = MagicMock()
    session.execute.return_value.all.return_value = []
    assert registry_has_exact_company_name(session, "") is False
    assert registry_has_exact_company_name(session, "   ") is False


@patch("agents.enrichment.classifiers.employer_classifier.invoke_structured_extraction_llm")
def test_build_employer_profile_degraded_returns_unknown_with_known_flag(
    mock_invoke: MagicMock,
) -> None:
    mock_invoke.return_value = (None, {"extraction_failed": True, "error_reason": "x"})
    session = MagicMock()
    with patch(
        "agents.enrichment.classifiers.employer_classifier.registry_has_exact_company_name",
        return_value=True,
    ):
        out = build_employer_profile("We use AI.", "Contoso", session)
    assert out.company_size == "unknown"
    assert out.ai_maturity_signal == "unknown"
    assert out.sector == "unknown"
    assert out.is_known_employer is True


@patch("agents.enrichment.classifiers.employer_classifier.invoke_structured_extraction_llm")
def test_build_employer_profile_merges_llm_and_db_known(
    mock_invoke: MagicMock,
) -> None:
    parsed = EmployerClassificationLLMOutput(
        company_size="enterprise",
        ai_maturity_signal="ai_adopting",
        sector="finance",
    )
    mock_invoke.return_value = (parsed, {"extraction_failed": False})
    session = MagicMock()
    with patch(
        "agents.enrichment.classifiers.employer_classifier.registry_has_exact_company_name",
        return_value=False,
    ):
        out = build_employer_profile("desc", "Globex", session)
    assert out.company_size == "enterprise"
    assert out.ai_maturity_signal == "ai_adopting"
    assert out.sector == "finance"
    assert out.is_known_employer is False


def test_persist_employer_metadata_executes_update_when_id() -> None:
    session = MagicMock()
    ep = EmployerProfile(company_size="startup", is_known_employer=False)
    persist_employer_metadata(session, ep, normalized_job_id=42)
    assert session.execute.called


def test_persist_employer_metadata_skips_when_no_keys() -> None:
    session = MagicMock()
    ep = EmployerProfile()
    persist_employer_metadata(session, ep)
    session.execute.assert_not_called()
