"""Helpers for fuzzy dedup matching E2E tests (PostgreSQL + Azure embeddings)."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from agents.common.data_store.models import NormalizedJob
from agents.enrichment.dedup.fuzzy_dedup import run_fuzzy_dedup
from agents.enrichment.job_postings_promotion import apply_fuzzy_dedup_result


def embedding_env_ready() -> bool:
    return bool(
        (os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT") or "").strip()
        and (os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY") or "").strip()
        and (os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME") or "").strip()
    )


def sync_normalized_jobs_id_sequence(engine: Engine) -> None:
    """Advance ``normalized_jobs.id`` sequence past ``MAX(id)``.

    Prevents ``UniqueViolation: Key (id)=(n) already exists`` when the PostgreSQL
    sequence is behind the table (common after restores or manual inserts).
    """
    with engine.begin() as conn:
        seq_name = conn.execute(text("SELECT pg_get_serial_sequence('dbo.normalized_jobs', 'id')")).scalar()
        if not seq_name:
            return
        max_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM dbo.normalized_jobs")).scalar()
        max_id = int(max_id or 0)
        conn.execute(text("SELECT setval(CAST(:seq AS regclass), :v, true)"), {"seq": seq_name, "v": max_id})


def _sync_sequence_from_session_bind(session: Session) -> None:
    bind = session.get_bind()
    if bind is None:
        return
    if isinstance(bind, Engine):
        sync_normalized_jobs_id_sequence(bind)
    elif isinstance(bind, Connection):
        sync_normalized_jobs_id_sequence(bind.engine)


def dedup_columns_ready(engine: Engine) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'dbo'
                  AND table_name = 'job_postings'
                  AND column_name = 'dedup_embedding'
                """
            )
        ).first()
        return row is not None


def audit_log_ready(engine: Engine) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'dbo'
                  AND table_name = 'llm_audit_log'
                """
            )
        ).first()
        return row is not None


def fetch_audit_count(engine: Engine, *, agent_name: str) -> int:
    with engine.connect() as conn:
        count = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM dbo.llm_audit_log
                WHERE agent_name = :agent_name
                """
            ),
            {"agent_name": agent_name},
        ).scalar()
        return int(count or 0)


def _job_postings_ts_fragment(insp) -> tuple[str, str]:
    cols = {c["name"] for c in insp.get_columns("job_postings", schema="dbo")}
    if "createdAt" in cols and "updatedAt" in cols:
        return ", createdAt, updatedAt", ", NOW(), NOW()"
    if "created_at" in cols and "updated_at" in cols:
        return ", created_at, updated_at", ", NOW(), NOW()"
    return "", ""


def insert_job_posting(
    engine: Engine,
    *,
    company_id: str,
    location_id: str,
    zip_code: str,
    publish_date: datetime,
    unpublish_date: datetime,
    job_title: str,
    job_description: str,
    source: str,
    external_id: str,
) -> str:
    """Insert dbo.job_postings row; return job_posting_id text."""
    insp = inspect(engine)
    jp_ts_cols, jp_ts_vals = _job_postings_ts_fragment(insp)
    job_posting_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
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
                    {jp_ts_cols}
                )
                VALUES (
                    CAST(:jpid AS uuid),
                    CAST(:cid AS uuid),
                    CAST(:lid AS uuid),
                    :title,
                    :desc,
                    false,
                    true,
                    'full-time',
                    'Remote',
                    'n/a',
                    'E2E',
                    :zip,
                    :pd,
                    :ud,
                    :source,
                    :eid
                    {jp_ts_vals}
                )
                """
            ),
            {
                "jpid": job_posting_id,
                "cid": company_id,
                "lid": location_id,
                "title": job_title,
                "desc": job_description,
                "zip": zip_code,
                "pd": publish_date,
                "ud": unpublish_date,
                "source": source,
                "eid": external_id,
            },
        )
    return job_posting_id


def add_normalized_job_and_extracted(
    session: Session,
    *,
    source: str,
    external_id: str,
    title: str,
    company: str,
    description: str,
    requirements: str | None = None,
) -> int:
    _sync_sequence_from_session_bind(session)
    nj = NormalizedJob(
        raw_job_id=None,
        ingestion_run_id=f"e2e-dedup-{uuid.uuid4().hex[:8]}",
        region_id="e2e",
        source=source,
        external_id=external_id,
        title=title,
        company=company,
        description=description,
        requirements=requirements,
        normalization_status="success",
    )
    session.add(nj)
    session.flush()
    nj_id = nj.id
    session.execute(
        text(
            """
            INSERT INTO dbo.extracted_intelligence (
                normalized_job_id,
                extraction_version,
                extracted_at,
                extraction_model,
                extraction_tokens_used,
                extraction_cost_usd,
                skills,
                tools,
                tasks,
                responsibilities,
                context,
                extraction_warnings,
                extraction_failed
            )
            VALUES (
                :nj_id,
                'e2e-dedup',
                NOW(),
                'stub',
                0,
                0.0,
                '[]'::jsonb,
                '[]'::jsonb,
                '[]'::jsonb,
                '[]'::jsonb,
                '[]'::jsonb,
                '[]'::jsonb,
                false
            )
            """
        ),
        {"nj_id": nj_id},
    )
    return nj_id


def delete_normalized_chain(engine: Engine, normalized_job_id: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM dbo.extracted_intelligence WHERE normalized_job_id = :id"),
            {"id": normalized_job_id},
        )
        conn.execute(
            text("DELETE FROM dbo.normalized_jobs WHERE id = :id"),
            {"id": normalized_job_id},
        )


def delete_job_posting(engine: Engine, job_posting_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM dbo.job_postings WHERE job_posting_id::text = :jpid"),
            {"jpid": job_posting_id},
        )


def run_dedup_and_persist(session: Session, job_posting_id: str) -> None:
    result = run_fuzzy_dedup(session, job_posting_id)
    apply_fuzzy_dedup_result(session, job_posting_id, result)


def fetch_dedup_columns(engine: Engine, job_posting_id: str) -> dict:
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


def fetch_embedding_meta(engine: Engine, job_posting_id: str) -> dict:
    with engine.connect() as conn:
        return dict(
            conn.execute(
                text(
                    """
                    SELECT
                        dedup_text_hash IS NOT NULL AS has_hash,
                        dedup_embedding IS NOT NULL AS has_embedding
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


def update_job_publish_date(engine: Engine, job_posting_id: str, publish_date: datetime) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE dbo.job_postings
                SET publish_date = :pd
                WHERE job_posting_id::text = :jpid
                """
            ),
            {"jpid": job_posting_id, "pd": publish_date},
        )


def update_job_text(
    engine: Engine,
    job_posting_id: str,
    *,
    job_title: str,
    job_description: str,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE dbo.job_postings
                SET job_title = :title, job_description = :desc
                WHERE job_posting_id::text = :jpid
                """
            ),
            {"jpid": job_posting_id, "title": job_title, "desc": job_description},
        )


def update_normalized_job_fields(
    engine: Engine,
    normalized_job_id: int,
    *,
    title: str,
    description: str,
    requirements: str | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE dbo.normalized_jobs
                SET title = :title, description = :desc, requirements = :req
                WHERE id = :nid
                """
            ),
            {"nid": normalized_job_id, "title": title, "desc": description, "req": requirements},
        )


@dataclass
class SecondCompany:
    company_id: str
    company_address_id: str
    company_name: str


def insert_second_company(engine: Engine, zip_code: str) -> SecondCompany:
    """Minimal second company + address reusing existing zip."""
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns("companies", schema="dbo")}
    c_created = "createdat" if "createdat" in cols else "created_at"
    c_updated = "updatedat" if "updatedat" in cols else "updated_at"
    zip_col = (
        "zip_region"
        if "zip_region" in {c["name"] for c in insp.get_columns("company_addresses", schema="dbo")}
        else "zip"
    )
    a_created = (
        "created_at"
        if "created_at" in {c["name"] for c in insp.get_columns("company_addresses", schema="dbo")}
        else "createdAt"
    )
    a_updated = (
        "updated_at"
        if "updated_at" in {c["name"] for c in insp.get_columns("company_addresses", schema="dbo")}
        else "updatedAt"
    )

    suffix = uuid.uuid4().hex[:8]
    cid = str(uuid.uuid4())
    aid = str(uuid.uuid4())
    cname = f"E2E Dedup Other Co {suffix}"
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                INSERT INTO dbo.companies (
                    company_id, company_name, is_approved, {c_created}, {c_updated}
                )
                VALUES (CAST(:cid AS uuid), :cname, true, NOW(), NOW())
                """
            ),
            {"cid": cid, "cname": cname},
        )
        conn.execute(
            text(
                f"""
                INSERT INTO dbo.company_addresses (
                    company_address_id, company_id, {zip_col}, {a_created}, {a_updated}
                )
                VALUES (CAST(:aid AS uuid), CAST(:cid AS uuid), :zip, NOW(), NOW())
                """
            ),
            {"aid": aid, "cid": cid, "zip": zip_code},
        )
    return SecondCompany(company_id=cid, company_address_id=aid, company_name=cname)


def teardown_second_company(engine: Engine, sc: SecondCompany) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM dbo.company_addresses WHERE company_address_id::text = :aid"),
            {"aid": sc.company_address_id},
        )
        conn.execute(
            text("DELETE FROM dbo.companies WHERE company_id::text = :cid"),
            {"cid": sc.company_id},
        )


def session_factory_for(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def anchor_now() -> datetime:
    return datetime.now(timezone.utc)
