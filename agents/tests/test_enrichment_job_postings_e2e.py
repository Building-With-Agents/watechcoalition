"""PostgreSQL E2E tests for enrichment ``job_postings`` promotion (Decision #8).

Requires ``PYTHON_DATABASE_URL`` and a full ``dbo`` schema (postal_geo_data, companies,
company_addresses, job_postings, normalized_jobs, extracted_intelligence). Skips if
seed fails (e.g. column naming differs from Prisma/pgloader expectations).
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.classifiers.spam_preview import SpamPreviewResult
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
                    SELECT quality_score, is_spam, spam_score, field_confidence, temporal_period
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
