"""Unit tests for NAICS classification (no live LLM or DB)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agents.enrichment.classifiers.naics_classifier import (
    NAICSClassificationOutput,
    _resolve_llm_naics_pick,
    classify_naics,
    get_naics_candidates,
)


def test_resolve_llm_naics_pick_exact_code() -> None:
    codes = {"541511", "541512"}
    assert _resolve_llm_naics_pick("541511", codes) == "541511"


def test_resolve_llm_naics_pick_unknown_literal() -> None:
    assert _resolve_llm_naics_pick("unknown", {"11"}) == "unknown"
    assert _resolve_llm_naics_pick("", {"11"}) == "unknown"


def test_resolve_llm_naics_pick_embedded_code() -> None:
    codes = {"541511"}
    assert _resolve_llm_naics_pick("The code is 541511 for this industry.", codes) == "541511"


def test_naics_classification_output_model() -> None:
    m = NAICSClassificationOutput(naics_code="unknown")
    assert m.naics_code == "unknown"


@patch("agents.enrichment.classifiers.naics_classifier.invoke_structured_extraction_llm")
def test_classify_naics_returns_unknown_when_no_candidates(mock_llm: MagicMock) -> None:
    session = MagicMock()
    session.execute.return_value.all.return_value = []
    out = classify_naics("x", "y", session)
    assert out == "unknown"
    mock_llm.assert_not_called()


@patch("agents.enrichment.classifiers.naics_classifier.invoke_structured_extraction_llm")
def test_classify_naics_validates_against_candidates(mock_llm: MagicMock) -> None:
    session = MagicMock()
    session.execute.return_value.all.return_value = [
        ("541511", "Custom Computer Programming Services"),
    ]

    mock_llm.return_value = (
        NAICSClassificationOutput(naics_code="541511"),
        {"extraction_failed": False},
    )
    out = classify_naics("Software Engineer", "we build custom software", session)
    assert out == "541511"


@patch("agents.enrichment.classifiers.naics_classifier.invoke_structured_extraction_llm")
def test_classify_naics_unknown_when_llm_returns_invalid_code(mock_llm: MagicMock) -> None:
    session = MagicMock()
    session.execute.return_value.all.return_value = [
        ("541511", "Custom Computer Programming Services"),
    ]

    mock_llm.return_value = (
        NAICSClassificationOutput(naics_code="999999"),
        {"extraction_failed": False},
    )
    out = classify_naics("Software Engineer", "we build software", session)
    assert out == "unknown"


def test_get_naics_candidates_empty_title_and_description() -> None:
    session = MagicMock()
    assert get_naics_candidates(session, "", None) == []
    session.execute.assert_not_called()
