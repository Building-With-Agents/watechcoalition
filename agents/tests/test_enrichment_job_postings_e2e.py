"""PostgreSQL E2E tests for enrichment ``job_postings`` promotion (Decision #8).

Requires ``PYTHON_DATABASE_URL`` and a full ``dbo`` schema (postal_geo_data, companies,
company_addresses, job_postings, normalized_jobs, extracted_intelligence). Skips if
seed fails (e.g. column naming differs from Prisma/pgloader expectations).

Run ``python agents/scripts/db_check.py migrate`` so ``job_postings`` has ``naics_code``,
``soc_code``, and ``employer_profile_id`` before the extended promotion test.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from agents.common.data_store.database import session_scope
from agents.common.event_envelope import EventEnvelope
from agents.common.types.job_profile import EmployerProfile
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.classifiers.spam_preview import SpamPreviewResult
from agents.enrichment.job_postings_promotion import (
    derive_enrichment_output_fields,
    resolve_job_posting_row,
)
from agents.tests.db_seed_enrichment_e2e import (
    EnrichmentE2ESeed,
    seed_enrichment_e2e,
    teardown_enrichment_e2e,
)


@pytest.fixture(scope="module")
def e2e_engine() -> Engine:
    url = os.getenv("PYTHON_DATABASE_URL")
    if not url:
        pytest.skip("PYTHON_DATABASE_URL not set")
    return create_engine(url, future=True)


@pytest.fixture(scope="module", autouse=True)
def _e2e_require_uuid_employer_profiles(e2e_engine: Engine) -> None:
    """Promotion + employer upsert require UUID PK ``employer_profiles`` (post-migration schema)."""
    insp = inspect(e2e_engine)
    if not insp.has_table("employer_profiles", schema="dbo"):
        pytest.skip("dbo.employer_profiles missing — run agents/scripts/db_check.py migrate")
    with e2e_engine.connect() as conn:
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
        pytest.skip(
            "dbo.employer_profiles.id must be type uuid for these E2E tests "
            "(run migrations; legacy SERIAL tables are dropped by migrate on PostgreSQL)."
        )


@pytest.fixture(autouse=True)
def _e2e_patch_heavy_enrichment_classifiers() -> object:
    """Avoid live LLM / rate limits; DB promotion + quality/spam paths stay real."""

    async def _fake_soc(*_a: object, **_kw: object) -> str:
        return "15-1252.00"

    with (
        patch("agents.enrichment.agent.classify_naics", return_value="541512"),
        patch("agents.enrichment.agent.classify_soc", side_effect=_fake_soc),
        patch(
            "agents.enrichment.agent.build_employer_profile",
            return_value=EmployerProfile(),
        ),
    ):
        yield None


def _seed_or_skip(engine: Engine) -> EnrichmentE2ESeed:
    try:
        return seed_enrichment_e2e(engine)
    except Exception as exc:
        pytest.skip(f"e2e seed failed: {exc}")


def _fetch_enrichment_columns(engine: Engine, job_posting_id: str) -> dict:
    with engine.connect() as conn:
        return dict(
            conn.execute(
                text(
                    """
                    SELECT quality_score, is_spam, spam_score, field_confidence, temporal_period,
                           borderplex_subregion
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


def _fetch_job_postings_naics_soc_employer_columns(engine: Engine, job_posting_id: str) -> dict:
    """Includes NAICS / SOC / employer FK columns (requires current agent migrations)."""
    with engine.connect() as conn:
        return dict(
            conn.execute(
                text(
                    """
                    SELECT quality_score, naics_code, soc_code, employer_profile_id
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


def _run_agent_with_spam_mock(
    seed: EnrichmentE2ESeed,
    spam_ret: SpamPreviewResult,
) -> None:
    with patch("agents.enrichment.agent.score_spam_preview", return_value=spam_ret):
        _run_agent_process(seed)


def _run_agent_process(seed: EnrichmentE2ESeed) -> None:
    agent = EnrichmentAgent()
    ev = EventEnvelope(
        correlation_id="e2e-promotion",
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
    agent.process(ev)


def _run_agent_capture_profile_and_payload(
    seed: EnrichmentE2ESeed,
    spam_ret: SpamPreviewResult,
) -> tuple[dict, dict]:
    with (
        patch("agents.enrichment.agent.score_spam_preview", return_value=spam_ret),
        patch(
            "agents.enrichment.agent.EnrichedJobProfile",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ) as mock_profile,
    ):
        agent = EnrichmentAgent()
        ev = EventEnvelope(
            correlation_id="e2e-consistency",
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
        out = agent.process(ev)
    return mock_profile.call_args.kwargs, out.payload


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_enrichment_promotion_clean_tier(e2e_engine: Engine) -> None:
    seed = _seed_or_skip(e2e_engine)
    try:
        spam_ret = SpamPreviewResult(
            spam_score=0.25,
            is_spam=False,
            tier="clean",
            field_confidence={"spam_score": 0.9},
            overall_confidence=0.9,
            rationale="e2e",
            degraded=False,
            extraction_note=None,
            used_heuristic=False,
        )
        _run_agent_with_spam_mock(seed, spam_ret)
        row = _fetch_enrichment_columns(e2e_engine, seed.job_posting_id)
        assert row.get("quality_score") is not None
        assert row.get("is_spam") is False
        assert row.get("spam_score") is not None
        assert abs(float(row["spam_score"]) - 0.25) < 1e-5
        assert row.get("field_confidence") is not None
        assert row.get("temporal_period") == "post_gpt4"
        assert row.get("borderplex_subregion") == "el_paso"
    finally:
        teardown_enrichment_e2e(e2e_engine, seed)


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_enrichment_promotion_flagged_tier(e2e_engine: Engine) -> None:
    seed = _seed_or_skip(e2e_engine)
    try:
        spam_ret = SpamPreviewResult(
            spam_score=0.8,
            is_spam=None,
            tier="flagged",
            field_confidence={"spam_score": 0.7},
            overall_confidence=0.7,
            rationale="e2e",
            degraded=False,
            extraction_note=None,
            used_heuristic=False,
        )
        _run_agent_with_spam_mock(seed, spam_ret)
        row = _fetch_enrichment_columns(e2e_engine, seed.job_posting_id)
        assert row.get("spam_score") is not None
        assert abs(float(row["spam_score"]) - 0.8) < 1e-5
        assert row.get("is_spam") is None
        assert row.get("quality_score") is not None
    finally:
        teardown_enrichment_e2e(e2e_engine, seed)


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_enrichment_promotion_rejected_skips_update(e2e_engine: Engine) -> None:
    seed = _seed_or_skip(e2e_engine)
    try:
        before = _fetch_enrichment_columns(e2e_engine, seed.job_posting_id)
        spam_ret = SpamPreviewResult(
            spam_score=0.95,
            is_spam=True,
            tier="rejected",
            field_confidence={"spam_score": 0.99},
            overall_confidence=0.99,
            rationale="e2e",
            degraded=False,
            extraction_note=None,
            used_heuristic=False,
        )
        _run_agent_with_spam_mock(seed, spam_ret)
        after = _fetch_enrichment_columns(e2e_engine, seed.job_posting_id)
        assert after.get("quality_score") == before.get("quality_score")
        assert after.get("spam_score") == before.get("spam_score")
        assert after.get("is_spam") == before.get("is_spam")
    finally:
        teardown_enrichment_e2e(e2e_engine, seed)


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_pair_a_fields_match_across_derivation_profile_payload_and_db(e2e_engine: Engine) -> None:
    seed = _seed_or_skip(e2e_engine)
    try:
        spam_ret = SpamPreviewResult(
            spam_score=0.25,
            is_spam=False,
            tier="clean",
            field_confidence={"spam_score": 0.9},
            overall_confidence=0.9,
            rationale="e2e",
            degraded=False,
            extraction_note=None,
            used_heuristic=False,
        )
        with session_scope() as session:
            resolved = resolve_job_posting_row(session, seed.normalized_job_id)
            derived = derive_enrichment_output_fields(resolved)

        profile_kwargs, payload = _run_agent_capture_profile_and_payload(seed, spam_ret)
        row = _fetch_enrichment_columns(e2e_engine, seed.job_posting_id)

        assert derived["temporal_period"] == "post_gpt4"
        assert derived["borderplex_subregion"] == "el_paso"
        assert profile_kwargs["temporal_period"] == derived["temporal_period"]
        assert profile_kwargs["borderplex_subregion"] == derived["borderplex_subregion"]
        assert payload["temporal_period"] == derived["temporal_period"]
        assert payload["borderplex_subregion"] == derived["borderplex_subregion"]
        assert row["temporal_period"] == derived["temporal_period"]
        assert row["borderplex_subregion"] == derived["borderplex_subregion"]
    finally:
        teardown_enrichment_e2e(e2e_engine, seed)


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_enrichment_promotion_writes_naics_soc_employer_profile_to_job_postings(
    e2e_engine: Engine,
) -> None:
    """Real ``process()`` + DB session: NAICS, SOC→soc_code, employer profile land on ``job_postings``.

    Classifiers are patched for deterministic outputs; spam preview stays mocked. When
    ``dbo.naics`` exists, :func:`seed_enrichment_e2e` inserts reference code ``999998``;
    ``classify_naics`` is patched to return that code so the written value matches the
    seeded row when present.
    """
    try:
        seed = seed_enrichment_e2e(e2e_engine)
    except Exception as exc:
        pytest.skip(f"e2e seed failed: {exc}")

    naics_expected = seed.e2e_naics_code or "999998"
    soc_expected = "17-3029.01"
    fake_ep = EmployerProfile(
        company_size="smb",
        ai_maturity_signal="ai_adopting",
        sector="technology",
        is_known_employer=True,
    )

    async def _fake_soc(*_a: object, **_kw: object) -> str:
        return soc_expected

    spam_ret = SpamPreviewResult(
        spam_score=0.25,
        is_spam=False,
        tier="clean",
        field_confidence={"spam_score": 0.9},
        overall_confidence=0.9,
        rationale="e2e",
        degraded=False,
        extraction_note=None,
        used_heuristic=False,
    )

    try:
        with (
            patch("agents.enrichment.agent.score_spam_preview", return_value=spam_ret),
            patch("agents.enrichment.agent.classify_naics", return_value=naics_expected),
            patch("agents.enrichment.agent.classify_soc", side_effect=_fake_soc),
            patch("agents.enrichment.agent.build_employer_profile", return_value=fake_ep),
        ):
            _run_agent_process(seed)

        try:
            row = _fetch_job_postings_naics_soc_employer_columns(e2e_engine, seed.job_posting_id)
        except ProgrammingError as exc:
            pytest.skip(f"job_postings missing expected columns (run migrations): {exc}")

        assert row.get("quality_score") is not None
        assert row.get("naics_code") == naics_expected
        assert row.get("soc_code") == soc_expected
        assert row.get("employer_profile_id") is not None
    finally:
        teardown_enrichment_e2e(e2e_engine, seed)
