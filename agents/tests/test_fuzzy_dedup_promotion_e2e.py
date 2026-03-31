"""PostgreSQL E2E tests for fuzzy dedup writes through enrichment promotion."""

from __future__ import annotations

import os
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.classifiers.spam_preview import SpamPreviewResult
from agents.enrichment.dedup.types import FuzzyDedupResult
from agents.tests.db_seed_enrichment_e2e import (
    EnrichmentE2ESeed,
    seed_enrichment_e2e,
    teardown_enrichment_e2e,
)

CLUSTER_ID = "00000000-0000-0000-0000-0000000000bb"


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


def _insert_peer_job_posting(engine: Engine, seed: EnrichmentE2ESeed) -> str:
    peer_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO dbo.job_postings (
                    job_posting_id,
                    company_id,
                    location_id,
                    job_title,
                    job_description,
                    is_internship,
                    is_paid,
                    employment_type,
                    location,
                    salary_range,
                    county,
                    zip,
                    publish_date,
                    unpublish_date,
                    source,
                    external_id
                )
                VALUES (
                    CAST(:jpid AS uuid),
                    CAST(:cid AS uuid),
                    CAST(:lid AS uuid),
                    'E2E Peer Title',
                    'E2E peer description body for fuzzy dedup test.',
                    false,
                    true,
                    'full-time',
                    'Remote',
                    'n/a',
                    'E2E',
                    :zip,
                    NOW() - INTERVAL '1 day',
                    NOW() + INTERVAL '29 day',
                    :source,
                    :eid
                )
                """
            ),
            {
                "jpid": peer_id,
                "cid": seed.company_id,
                "lid": seed.company_address_id,
                "zip": seed.zip_code,
                "source": "e2e-enrich-peer",
                "eid": f"e2e-peer-{peer_id[:8]}",
            },
        )
    return peer_id


def _delete_job_posting(engine: Engine, job_posting_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM dbo.job_postings WHERE job_posting_id::text = :jpid"),
            {"jpid": job_posting_id},
        )


def _fetch_dedup_columns(engine: Engine, job_posting_id: str) -> dict:
    with engine.connect() as conn:
        return dict(
            conn.execute(
                text(
                    """
                    SELECT is_duplicate, duplicate_cluster_id
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


def _run_agent_with_dedup_mock(
    seed: EnrichmentE2ESeed,
    dedup_ret: FuzzyDedupResult,
) -> None:
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
    with (
        patch("agents.enrichment.agent.score_spam_preview", return_value=spam_ret),
        patch("agents.enrichment.job_postings_promotion.run_fuzzy_dedup", return_value=dedup_ret),
    ):
        agent = EnrichmentAgent()
        ev = EventEnvelope(
            correlation_id="e2e-fuzzy-dedup",
            agent_id="skills-extraction-agent",
            payload={
                "event_type": "SkillsExtracted",
                "posting_id": 999001,
                "normalized_job_id": seed.normalized_job_id,
                "title": "E2E Title",
                "description": "E2E description body for fuzzy dedup promotion test.",
                "company": "E2E Co",
                "skills": [],
            },
        )
        agent.process(ev)


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_fuzzy_dedup_promotion_updates_current_and_survivor_rows(e2e_engine: Engine) -> None:
    seed = _seed_or_skip(e2e_engine)
    peer_id = _insert_peer_job_posting(e2e_engine, seed)
    try:
        _run_agent_with_dedup_mock(
            seed,
            FuzzyDedupResult(
                is_duplicate=True,
                duplicate_cluster_id=CLUSTER_ID,
                matched_job_posting_id=peer_id,
                survivor_job_posting_id=peer_id,
                stub=False,
            ),
        )
        current = _fetch_dedup_columns(e2e_engine, seed.job_posting_id)
        peer = _fetch_dedup_columns(e2e_engine, peer_id)
        assert current == {"is_duplicate": True, "duplicate_cluster_id": CLUSTER_ID}
        assert peer == {"is_duplicate": False, "duplicate_cluster_id": CLUSTER_ID}
    finally:
        _delete_job_posting(e2e_engine, peer_id)
        teardown_enrichment_e2e(e2e_engine, seed)
