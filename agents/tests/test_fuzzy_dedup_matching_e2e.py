"""Real fuzzy dedup matching E2E (PostgreSQL + Azure embeddings).

Requires ``PYTHON_DATABASE_URL`` and Azure embedding env vars
(``AZURE_OPENAI_EMBEDDING_*``). Requires ``run_migrations()`` so
``dedup_embedding`` / ``dedup_text_hash`` exist.

Run (repo root)::

    pytest agents/tests/test_fuzzy_dedup_matching_e2e.py -m fuzzy_dedup_e2e -v

Or from ``agents/``::

    pytest tests/test_fuzzy_dedup_matching_e2e.py -m fuzzy_dedup_e2e -v
"""

from __future__ import annotations

import os
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from agents.tests.db_seed_enrichment_e2e import seed_enrichment_e2e, teardown_enrichment_e2e
from agents.tests.fuzzy_dedup_e2e_helpers import (
    SecondCompany,
    add_normalized_job_and_extracted,
    anchor_now,
    audit_log_ready,
    dedup_columns_ready,
    delete_job_posting,
    delete_normalized_chain,
    embedding_env_ready,
    fetch_audit_count,
    fetch_dedup_columns,
    fetch_embedding_meta,
    insert_job_posting,
    insert_second_company,
    run_dedup_and_persist,
    session_factory_for,
    teardown_second_company,
    update_job_publish_date,
    update_job_text,
    update_normalized_job_fields,
)

pytestmark = [
    pytest.mark.fuzzy_dedup_e2e,
    pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="PYTHON_DATABASE_URL not set"),
    pytest.mark.skipif(not embedding_env_ready(), reason="Azure embedding env incomplete"),
]

SHARED_TITLE = "E2E Dedup Shared Title Acme Widget"
SHARED_BODY = ("E2E shared near-duplicate body text for cosine match. " * 40)[:2000]

DIFF_SURVIVOR_TITLE = "E2E Zebra Assembler Completely Different Role"
DIFF_SURVIVOR_BODY = "Zebra line builds mechanical assemblies in sector nine. " * 30

DIFF_CURRENT_TITLE = "E2E Apple Software Engineer Cloud Platform"
DIFF_CURRENT_BODY = "Apple team ships distributed systems and APIs for payments. " * 30


@pytest.fixture(scope="module")
def e2e_engine() -> Engine:
    url = os.getenv("PYTHON_DATABASE_URL")
    assert url
    return create_engine(url, future=True)


@pytest.fixture(scope="module", autouse=True)
def _require_dedup_migration(e2e_engine: Engine) -> None:
    try:
        if not dedup_columns_ready(e2e_engine):
            pytest.skip("dbo.job_postings.dedup_embedding missing; run run_migrations(get_engine())")
        if not audit_log_ready(e2e_engine):
            pytest.skip("dbo.llm_audit_log missing; run run_migrations(get_engine())")
    except Exception as exc:
        pytest.skip(f"database unreachable or schema check failed: {exc}")


def _seed_or_skip(engine: Engine):
    try:
        return seed_enrichment_e2e(engine)
    except Exception as exc:
        pytest.skip(f"e2e seed failed: {exc}")


def test_window_29d_in_merges(monkeypatch: pytest.MonkeyPatch, e2e_engine: Engine) -> None:
    monkeypatch.setenv("DEDUP_COSINE_THRESHOLD", "0.82")
    seed = _seed_or_skip(e2e_engine)
    T = anchor_now()
    ud = T + timedelta(days=400)
    suffix = uuid.uuid4().hex[:8]
    src_surv = f"e2e-dedup-surv-{suffix}"
    eid_surv = f"e2e-dedup-eid-{suffix}"
    survivor_id: str | None = None
    nj_surv: int | None = None
    try:
        survivor_id = insert_job_posting(
            e2e_engine,
            company_id=seed.company_id,
            location_id=seed.company_address_id,
            zip_code=seed.zip_code,
            publish_date=T - timedelta(days=29),
            unpublish_date=ud,
            job_title=SHARED_TITLE,
            job_description=SHARED_BODY,
            source=src_surv,
            external_id=eid_surv,
        )
        sf = session_factory_for(e2e_engine)
        with sf() as session:
            nj_surv = add_normalized_job_and_extracted(
                session,
                source=src_surv,
                external_id=eid_surv,
                title=SHARED_TITLE,
                company="E2E Co",
                description=SHARED_BODY,
                requirements=SHARED_BODY[:500],
            )
            session.commit()

        with sf() as session:
            run_dedup_and_persist(session, survivor_id)
            session.commit()

        meta_s = fetch_embedding_meta(e2e_engine, survivor_id)
        assert meta_s.get("has_embedding") is True

        update_job_publish_date(e2e_engine, seed.job_posting_id, T)
        update_job_text(e2e_engine, seed.job_posting_id, job_title=SHARED_TITLE, job_description=SHARED_BODY)
        update_normalized_job_fields(
            e2e_engine,
            seed.normalized_job_id,
            title=SHARED_TITLE,
            description=SHARED_BODY,
            requirements=SHARED_BODY[:500],
        )

        with sf() as session:
            run_dedup_and_persist(session, seed.job_posting_id)
            session.commit()

        cur = fetch_dedup_columns(e2e_engine, seed.job_posting_id)
        surv = fetch_dedup_columns(e2e_engine, survivor_id)
        assert cur.get("duplicate_cluster_id") == surv.get("duplicate_cluster_id")
        assert cur.get("duplicate_cluster_id") is not None
        assert sum(x is True for x in (cur.get("is_duplicate"), surv.get("is_duplicate"))) == 1
    finally:
        if survivor_id:
            delete_job_posting(e2e_engine, survivor_id)
        if nj_surv is not None:
            delete_normalized_chain(e2e_engine, nj_surv)
        teardown_enrichment_e2e(e2e_engine, seed)


def test_live_embedding_call_writes_llm_audit_log(e2e_engine: Engine) -> None:
    seed = _seed_or_skip(e2e_engine)
    before = fetch_audit_count(e2e_engine, agent_name="enrichment-dedup")
    sf = session_factory_for(e2e_engine)
    try:
        with sf() as session:
            run_dedup_and_persist(session, seed.job_posting_id)
            session.commit()

        meta = fetch_embedding_meta(e2e_engine, seed.job_posting_id)
        after = fetch_audit_count(e2e_engine, agent_name="enrichment-dedup")
        state = fetch_dedup_columns(e2e_engine, seed.job_posting_id)

        assert meta.get("has_embedding") is True
        assert after >= before + 1
        assert state.get("is_duplicate") is False
        assert state.get("duplicate_cluster_id") is None
    finally:
        teardown_enrichment_e2e(e2e_engine, seed)


def test_window_31d_out_no_merge(monkeypatch: pytest.MonkeyPatch, e2e_engine: Engine) -> None:
    monkeypatch.setenv("DEDUP_COSINE_THRESHOLD", "0.82")
    seed = _seed_or_skip(e2e_engine)
    T = anchor_now()
    ud = T + timedelta(days=400)
    suffix = uuid.uuid4().hex[:8]
    src_surv = f"e2e-dedup-31-{suffix}"
    eid_surv = f"e2e-dedup-31e-{suffix}"
    survivor_id: str | None = None
    nj_surv: int | None = None
    try:
        survivor_id = insert_job_posting(
            e2e_engine,
            company_id=seed.company_id,
            location_id=seed.company_address_id,
            zip_code=seed.zip_code,
            publish_date=T - timedelta(days=31),
            unpublish_date=ud,
            job_title=SHARED_TITLE,
            job_description=SHARED_BODY,
            source=src_surv,
            external_id=eid_surv,
        )
        sf = session_factory_for(e2e_engine)
        with sf() as session:
            nj_surv = add_normalized_job_and_extracted(
                session,
                source=src_surv,
                external_id=eid_surv,
                title=SHARED_TITLE,
                company="E2E Co",
                description=SHARED_BODY,
                requirements=SHARED_BODY[:500],
            )
            session.commit()

        with sf() as session:
            run_dedup_and_persist(session, survivor_id)
            session.commit()

        update_job_publish_date(e2e_engine, seed.job_posting_id, T)
        update_job_text(e2e_engine, seed.job_posting_id, job_title=SHARED_TITLE, job_description=SHARED_BODY)
        update_normalized_job_fields(
            e2e_engine,
            seed.normalized_job_id,
            title=SHARED_TITLE,
            description=SHARED_BODY,
            requirements=SHARED_BODY[:500],
        )

        with sf() as session:
            run_dedup_and_persist(session, seed.job_posting_id)
            session.commit()

        cur = fetch_dedup_columns(e2e_engine, seed.job_posting_id)
        assert cur.get("is_duplicate") is False
        assert cur.get("duplicate_cluster_id") is None
    finally:
        if survivor_id:
            delete_job_posting(e2e_engine, survivor_id)
        if nj_surv is not None:
            delete_normalized_chain(e2e_engine, nj_surv)
        teardown_enrichment_e2e(e2e_engine, seed)


def test_same_company_different_content_no_merge(e2e_engine: Engine) -> None:
    seed = _seed_or_skip(e2e_engine)
    T = anchor_now()
    ud = T + timedelta(days=400)
    suffix = uuid.uuid4().hex[:8]
    src_surv = f"e2e-dedup-diff-{suffix}"
    eid_surv = f"e2e-dedup-diffe-{suffix}"
    survivor_id: str | None = None
    nj_surv: int | None = None
    try:
        survivor_id = insert_job_posting(
            e2e_engine,
            company_id=seed.company_id,
            location_id=seed.company_address_id,
            zip_code=seed.zip_code,
            publish_date=T - timedelta(days=5),
            unpublish_date=ud,
            job_title=DIFF_SURVIVOR_TITLE,
            job_description=DIFF_SURVIVOR_BODY,
            source=src_surv,
            external_id=eid_surv,
        )
        sf = session_factory_for(e2e_engine)
        with sf() as session:
            nj_surv = add_normalized_job_and_extracted(
                session,
                source=src_surv,
                external_id=eid_surv,
                title=DIFF_SURVIVOR_TITLE,
                company="E2E Co",
                description=DIFF_SURVIVOR_BODY,
                requirements=DIFF_SURVIVOR_BODY[:500],
            )
            session.commit()

        with sf() as session:
            run_dedup_and_persist(session, survivor_id)
            session.commit()

        update_job_publish_date(e2e_engine, seed.job_posting_id, T)
        update_job_text(
            e2e_engine,
            seed.job_posting_id,
            job_title=DIFF_CURRENT_TITLE,
            job_description=DIFF_CURRENT_BODY,
        )
        update_normalized_job_fields(
            e2e_engine,
            seed.normalized_job_id,
            title=DIFF_CURRENT_TITLE,
            description=DIFF_CURRENT_BODY,
            requirements=DIFF_CURRENT_BODY[:500],
        )

        with sf() as session:
            run_dedup_and_persist(session, seed.job_posting_id)
            session.commit()

        cur = fetch_dedup_columns(e2e_engine, seed.job_posting_id)
        surv = fetch_dedup_columns(e2e_engine, survivor_id)
        assert cur.get("is_duplicate") is False
        assert cur.get("duplicate_cluster_id") is None
        assert surv.get("is_duplicate") is False
        assert surv.get("duplicate_cluster_id") is None
    finally:
        if survivor_id:
            delete_job_posting(e2e_engine, survivor_id)
        if nj_surv is not None:
            delete_normalized_chain(e2e_engine, nj_surv)
        teardown_enrichment_e2e(e2e_engine, seed)


def test_different_company_no_cross_merge(e2e_engine: Engine) -> None:
    """Survivor SQL filters by company_id: a lone posting in company B stays unique."""
    seed = _seed_or_skip(e2e_engine)
    T = anchor_now()
    ud = T + timedelta(days=400)
    suffix = uuid.uuid4().hex[:8]
    sc: SecondCompany | None = None
    b_job: str | None = None
    nj_b: int | None = None
    try:
        sc = insert_second_company(e2e_engine, seed.zip_code)
        src_b = f"e2e-dedup-co-b-{suffix}"
        eid_b = f"e2e-dedup-cob-{suffix}"
        b_job = insert_job_posting(
            e2e_engine,
            company_id=sc.company_id,
            location_id=sc.company_address_id,
            zip_code=seed.zip_code,
            publish_date=T,
            unpublish_date=ud,
            job_title=SHARED_TITLE,
            job_description=SHARED_BODY,
            source=src_b,
            external_id=eid_b,
        )
        sf = session_factory_for(e2e_engine)
        with sf() as session:
            nj_b = add_normalized_job_and_extracted(
                session,
                source=src_b,
                external_id=eid_b,
                title=SHARED_TITLE,
                company=sc.company_name,
                description=SHARED_BODY,
                requirements=SHARED_BODY[:500],
            )
            session.commit()

        with sf() as session:
            run_dedup_and_persist(session, b_job)
            session.commit()

        b_state = fetch_dedup_columns(e2e_engine, b_job)
        assert b_state.get("is_duplicate") is False
        assert b_state.get("duplicate_cluster_id") is None
        meta = fetch_embedding_meta(e2e_engine, b_job)
        assert meta.get("has_embedding") is True
    finally:
        if b_job:
            delete_job_posting(e2e_engine, b_job)
        if nj_b is not None:
            delete_normalized_chain(e2e_engine, nj_b)
        if sc:
            teardown_second_company(e2e_engine, sc)
        teardown_enrichment_e2e(e2e_engine, seed)


def test_repost_near_duplicate_merges(monkeypatch: pytest.MonkeyPatch, e2e_engine: Engine) -> None:
    monkeypatch.setenv("DEDUP_COSINE_THRESHOLD", "0.78")
    seed = _seed_or_skip(e2e_engine)
    T = anchor_now()
    ud = T + timedelta(days=400)
    suffix = uuid.uuid4().hex[:8]
    src_surv = f"e2e-dedup-repost-{suffix}"
    eid_surv = f"e2e-dedup-repe-{suffix}"
    survivor_id: str | None = None
    nj_surv: int | None = None
    try:
        survivor_id = insert_job_posting(
            e2e_engine,
            company_id=seed.company_id,
            location_id=seed.company_address_id,
            zip_code=seed.zip_code,
            publish_date=T - timedelta(days=5),
            unpublish_date=ud,
            job_title=SHARED_TITLE,
            job_description=SHARED_BODY,
            source=src_surv,
            external_id=eid_surv,
        )
        sf = session_factory_for(e2e_engine)
        with sf() as session:
            nj_surv = add_normalized_job_and_extracted(
                session,
                source=src_surv,
                external_id=eid_surv,
                title=SHARED_TITLE,
                company="E2E Co",
                description=SHARED_BODY,
                requirements=SHARED_BODY[:500],
            )
            session.commit()

        with sf() as session:
            run_dedup_and_persist(session, survivor_id)
            session.commit()

        update_job_publish_date(e2e_engine, seed.job_posting_id, T)
        update_job_text(e2e_engine, seed.job_posting_id, job_title=SHARED_TITLE, job_description=SHARED_BODY)
        update_normalized_job_fields(
            e2e_engine,
            seed.normalized_job_id,
            title=SHARED_TITLE,
            description=SHARED_BODY,
            requirements=SHARED_BODY[:500],
        )

        with sf() as session:
            run_dedup_and_persist(session, seed.job_posting_id)
            session.commit()

        cur = fetch_dedup_columns(e2e_engine, seed.job_posting_id)
        surv = fetch_dedup_columns(e2e_engine, survivor_id)
        assert cur.get("duplicate_cluster_id") == surv.get("duplicate_cluster_id")
        assert cur.get("duplicate_cluster_id") is not None
        dup_flags = [cur.get("is_duplicate") is True, surv.get("is_duplicate") is True]
        assert sum(dup_flags) == 1, "exactly one row should be marked duplicate in a merged pair"
    finally:
        if survivor_id:
            delete_job_posting(e2e_engine, survivor_id)
        if nj_surv is not None:
            delete_normalized_chain(e2e_engine, nj_surv)
        teardown_enrichment_e2e(e2e_engine, seed)
