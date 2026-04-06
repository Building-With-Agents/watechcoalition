"""Integration tests: EnrichmentAgent promotion → ``dbo.job_postings`` + ``dbo.employer_profiles``.

Requires ``PYTHON_DATABASE_URL``, migrated schema (``naics_code``, ``soc_code``,
``employer_profile_id``, UUID ``employer_profiles``). Uses :func:`seed_enrichment_e2e` /
:func:`teardown_enrichment_e2e`.

**Default (CI / fast):** LLM-facing calls are mocked; asserts exact expected codes.

**Live:** ``pytest tests/test_enrichment_promotion_e2e.py --live`` runs
``@pytest.mark.live_llm`` without mocks (real Azure/OpenAI + reference tables).
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from agents.common.event_envelope import EventEnvelope
from agents.common.types.job_profile import EmployerProfile
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.classifiers.spam_preview import SpamPreviewResult
from agents.tests.db_seed_enrichment_e2e import (
    EnrichmentE2ESeed,
    seed_enrichment_e2e,
    teardown_enrichment_e2e,
)

# ---------------------------------------------------------------------------
# Engine + schema guards (module-scoped)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def promotion_e2e_engine() -> Engine:
    url = os.getenv("PYTHON_DATABASE_URL")
    if not url:
        pytest.skip("PYTHON_DATABASE_URL not set")
    return create_engine(url, future=True)


@pytest.fixture(scope="module", autouse=True)
def _promotion_e2e_require_uuid_employer_profiles(promotion_e2e_engine: Engine) -> None:
    insp = inspect(promotion_e2e_engine)
    if not insp.has_table("employer_profiles", schema="dbo"):
        pytest.skip("dbo.employer_profiles missing — run: python agents/scripts/db_check.py migrate")
    with promotion_e2e_engine.connect() as conn:
        dt = conn.execute(
            text(
                """
                SELECT data_type FROM information_schema.columns
                WHERE table_schema = 'dbo' AND table_name = 'employer_profiles'
                  AND column_name = 'id'
                """
            )
        ).scalar()
    if (dt or "").lower() != "uuid":
        pytest.skip("dbo.employer_profiles.id must be uuid (run migrations; legacy SERIAL dropped on PostgreSQL).")


# ---------------------------------------------------------------------------
# Seed + teardown fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def enrichment_promotion_bundle(promotion_e2e_engine: Engine) -> Iterator[tuple[Engine, EnrichmentE2ESeed]]:
    """Insert E2E chain via ``seed_enrichment_e2e``; always ``teardown_enrichment_e2e`` after."""
    try:
        seed = seed_enrichment_e2e(promotion_e2e_engine)
    except Exception as exc:
        pytest.skip(f"e2e seed failed: {exc}")
    try:
        yield promotion_e2e_engine, seed
    finally:
        teardown_enrichment_e2e(promotion_e2e_engine, seed)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _skills_extracted_envelope(seed: EnrichmentE2ESeed) -> EventEnvelope:
    return EventEnvelope(
        correlation_id="promotion-e2e",
        agent_id="skills-extraction-agent",
        payload={
            "event_type": "SkillsExtracted",
            "posting_id": 999001,
            "normalized_job_id": seed.normalized_job_id,
            "title": "E2E Title",
            "description": "E2E description body for enrichment promotion test.",
            "company": "E2E Co",
            "skills": [],
        },
    )


def _run_enrichment_agent(seed: EnrichmentE2ESeed) -> None:
    EnrichmentAgent().process(_skills_extracted_envelope(seed))


def _fetch_job_postings_promotion_columns(engine: Engine, job_posting_id: str) -> dict[str, Any]:
    with engine.connect() as conn:
        return dict(
            conn.execute(
                text(
                    """
                    SELECT quality_score, spam_score, is_spam, naics_code, soc_code,
                           employer_profile_id::text AS employer_profile_id,
                           temporal_period, borderplex_subregion
                    FROM dbo.job_postings
                    WHERE job_posting_id::text = :jpid
                    """
                ),
                {"jpid": job_posting_id},
            )
            .mappings()
            .first()
            or {}
        )


def _fetch_employer_profile_row(engine: Engine, company_id: str) -> dict[str, Any]:
    with engine.connect() as conn:
        return dict(
            conn.execute(
                text(
                    """
                    SELECT company_size, ai_maturity_signal, sector, is_known_employer
                    FROM dbo.employer_profiles
                    WHERE company_id::text = :cid
                    """
                ),
                {"cid": company_id},
            )
            .mappings()
            .first()
            or {}
        )


@contextmanager
def _mocked_llm_promotion_stack(
    *,
    naics_code: str,
    soc_code: str,
    employer: EmployerProfile,
    spam: SpamPreviewResult,
) -> Iterator[None]:
    async def _fake_soc(*_a: object, **_kw: object) -> str:
        return soc_code

    with (
        patch("agents.enrichment.agent.score_spam_preview", return_value=spam),
        patch("agents.enrichment.agent.classify_naics", return_value=naics_code),
        patch("agents.enrichment.agent.classify_soc", side_effect=_fake_soc),
        patch("agents.enrichment.agent.build_employer_profile", return_value=employer),
    ):
        yield None


def _clean_spam_preview() -> SpamPreviewResult:
    return SpamPreviewResult(
        spam_score=0.25,
        is_spam=False,
        tier="clean",
        field_confidence={"spam_score": 0.9},
        overall_confidence=0.9,
        rationale="promotion-e2e",
        degraded=False,
        extraction_note=None,
        used_heuristic=False,
    )


# ---------------------------------------------------------------------------
# Mocked pipeline (default)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_mocked_skills_extracted_event_writes_naics_soc_and_employer_fk_to_job_postings(
    enrichment_promotion_bundle: tuple[Engine, EnrichmentE2ESeed],
) -> None:
    engine, seed = enrichment_promotion_bundle
    naics_expected = seed.e2e_naics_code or "999998"
    soc_expected = "17-3029.01"
    fake_employer = EmployerProfile(
        company_size="smb",
        ai_maturity_signal="ai_adopting",
        sector="technology",
        is_known_employer=True,
    )

    with _mocked_llm_promotion_stack(
        naics_code=naics_expected,
        soc_code=soc_expected,
        employer=fake_employer,
        spam=_clean_spam_preview(),
    ):
        _run_enrichment_agent(seed)

    try:
        row = _fetch_job_postings_promotion_columns(engine, seed.job_posting_id)
    except ProgrammingError as exc:
        pytest.skip(f"job_postings missing expected columns (run migrations): {exc}")

    assert row.get("quality_score") is not None
    assert row.get("naics_code") == naics_expected
    assert row.get("soc_code") == soc_expected
    assert row.get("employer_profile_id") is not None
    uuid.UUID(str(row["employer_profile_id"]))


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_employer_profiles_table_stores_all_four_mocked_dimensions(
    enrichment_promotion_bundle: tuple[Engine, EnrichmentE2ESeed],
) -> None:
    engine, seed = enrichment_promotion_bundle
    fake_employer = EmployerProfile(
        company_size="mid_market",
        ai_maturity_signal="ai_exploring",
        sector="healthcare",
        is_known_employer=False,
    )
    naics = seed.e2e_naics_code or "999998"

    with _mocked_llm_promotion_stack(
        naics_code=naics,
        soc_code="15-1252.00",
        employer=fake_employer,
        spam=_clean_spam_preview(),
    ):
        _run_enrichment_agent(seed)

    ep = _fetch_employer_profile_row(engine, seed.company_id)
    assert ep, "expected dbo.employer_profiles row for seeded company_id"
    assert ep.get("company_size") == "mid_market"
    assert ep.get("ai_maturity_signal") == "ai_exploring"
    assert ep.get("sector") == "healthcare"
    assert ep.get("is_known_employer") is False


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_mocked_unknown_naics_soc_and_partial_employer_fields_persist_without_errors(
    enrichment_promotion_bundle: tuple[Engine, EnrichmentE2ESeed],
) -> None:
    """NAICS ``unknown`` / SOC ``unclassified`` → literal ``unknown`` + null SOC on posting; employer literals."""
    engine, seed = enrichment_promotion_bundle
    unknown_employer = EmployerProfile(
        company_size="unknown",
        ai_maturity_signal="unknown",
        sector="unknown",
        is_known_employer=False,
    )

    async def _soc_unclassified(*_a: object, **_kw: object) -> str:
        return "unclassified"

    spam = _clean_spam_preview()
    with (
        patch("agents.enrichment.agent.score_spam_preview", return_value=spam),
        patch("agents.enrichment.agent.classify_naics", return_value="unknown"),
        patch("agents.enrichment.agent.classify_soc", side_effect=_soc_unclassified),
        patch("agents.enrichment.agent.build_employer_profile", return_value=unknown_employer),
    ):
        _run_enrichment_agent(seed)

    try:
        jp = _fetch_job_postings_promotion_columns(engine, seed.job_posting_id)
    except ProgrammingError as exc:
        pytest.skip(f"job_postings missing expected columns (run migrations): {exc}")

    assert jp.get("quality_score") is not None
    assert str(jp.get("naics_code") or "").strip().lower() == "unknown"
    assert jp.get("soc_code") is None
    assert jp.get("employer_profile_id") is not None

    ep = _fetch_employer_profile_row(engine, seed.company_id)
    assert ep
    # Upsert stores non-null strings for size / maturity; sector may be unknown text
    assert ep.get("company_size") is not None and str(ep["company_size"]).lower() == "unknown"
    assert ep.get("ai_maturity_signal") is not None and str(ep["ai_maturity_signal"]).lower() == "unknown"
    assert ep.get("sector") is not None
    assert str(ep["sector"]).lower() == "unknown"
    assert ep.get("is_known_employer") is False


# ---------------------------------------------------------------------------
# Live LLM (``pytest --live`` only)
# ---------------------------------------------------------------------------


@pytest.mark.live_llm
@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_live_llm_promotion_writes_job_postings_and_employer_profile_without_constraint_violations(
    enrichment_promotion_bundle: tuple[Engine, EnrichmentE2ESeed],
) -> None:
    """Real ``score_spam_preview``, ``classify_naics``, ``classify_soc``, ``build_employer_profile``.

    Assertions are intentionally soft: values depend on model + ``dbo.naics`` / ``dbo.socc``.
    We require successful commit and core promotion fields present.
    """
    engine, seed = enrichment_promotion_bundle
    _run_enrichment_agent(seed)

    try:
        jp = _fetch_job_postings_promotion_columns(engine, seed.job_posting_id)
    except ProgrammingError as exc:
        pytest.skip(f"job_postings missing expected columns (run migrations): {exc}")

    assert jp.get("quality_score") is not None, "promotion requires quality_score"
    assert jp.get("spam_score") is not None
    assert jp.get("employer_profile_id") is not None, "company_id present on seed → employer upsert expected"
    uuid.UUID(str(jp["employer_profile_id"]))

    ep = _fetch_employer_profile_row(engine, seed.company_id)
    assert ep, "employer_profiles row should exist after live promotion"
    for col in ("company_size", "ai_maturity_signal", "sector"):
        assert ep.get(col) is not None, f"{col} must be non-null text in DB"
        assert str(ep[col]).strip() != "", f"{col} must not be empty string"
