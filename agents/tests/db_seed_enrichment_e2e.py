"""Seed minimal FK rows for enrichment ``job_postings`` promotion E2E tests.

Requires a PostgreSQL database with Prisma/pgloader-shaped ``dbo`` tables:
``postal_geo_data``, ``companies``, ``company_addresses``, ``job_postings``,
``normalized_jobs``, ``extracted_intelligence``. Raises ``RuntimeError`` if
insert fails (caller should ``pytest.skip``).
"""

from __future__ import annotations

import uuid
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import Session

from agents.common.data_store.models import NormalizedJob


@dataclass
class EnrichmentE2ESeed:
    """Handles created primary keys for teardown."""

    zip_code: str
    company_id: str
    company_address_id: str
    job_posting_id: str
    normalized_job_id: int
    #: Synthetic NAICS code inserted into ``dbo.naics`` when that table exists (for E2E realism).
    e2e_naics_code: str | None = None


def _require_tables(engine: Engine) -> None:
    insp = inspect(engine)
    needed = (
        "postal_geo_data",
        "companies",
        "company_addresses",
        "job_postings",
        "normalized_jobs",
        "extracted_intelligence",
    )
    for t in needed:
        if not insp.has_table(t, schema="dbo"):
            raise RuntimeError(f"missing table dbo.{t}")


def _seed_optional_naics_reference(engine: Engine, insp) -> str | None:
    """Insert a dedicated NAICS row for E2E when ``dbo.naics`` exists; return code or None."""
    if not insp.has_table("naics", schema="dbo"):
        return None
    code = "999998"
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO dbo.naics (naics_code, title, seq_no, createdat, updatedat)
                VALUES (:code, 'E2E enrichment pipeline reference row', NULL, NOW(), NOW())
                ON CONFLICT (naics_code) DO NOTHING
                """
            ),
            {"code": code},
        )
    return code


def _company_ts_columns(insp) -> tuple[str, str]:
    cols = {c["name"] for c in insp.get_columns("companies", schema="dbo")}
    c_created = "createdat" if "createdat" in cols else "created_at"
    c_updated = "updatedat" if "updatedat" in cols else "updated_at"
    return c_created, c_updated


def _job_postings_ts_fragment(insp) -> tuple[str, str]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=SAWarning)
        cols = {c["name"] for c in insp.get_columns("job_postings", schema="dbo")}
    if "createdAt" in cols and "updatedAt" in cols:
        return ", createdAt, updatedAt", ", NOW(), NOW()"
    if "created_at" in cols and "updated_at" in cols:
        return ", created_at, updated_at", ", NOW(), NOW()"
    return "", ""


def _address_zip_column(insp) -> str:
    cols = {c["name"] for c in insp.get_columns("company_addresses", schema="dbo")}
    if "zip_region" in cols:
        return "zip_region"
    if "zip" in cols:
        return "zip"
    raise RuntimeError("company_addresses has no zip_region or zip column")


def _address_ts_columns(insp) -> tuple[str, str]:
    cols = {c["name"] for c in insp.get_columns("company_addresses", schema="dbo")}
    c_created = "created_at" if "created_at" in cols else "createdAt"
    c_updated = "updated_at" if "updated_at" in cols else "updatedAt"
    return c_created, c_updated


def _resync_normalized_jobs_id_sequence(engine: Engine) -> None:
    """Align ``normalized_jobs.id`` sequence with ``MAX(id)`` to avoid duplicate PK on insert.

    Shared dev databases often have rows with ids higher than the sequence's next value
    (restores, manual inserts). E2E seeds rely on autoincrement; without this, the second
    and later tests can skip with ``duplicate key ... normalized_jobs_pkey``.
    """
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as conn:
        seq = conn.execute(text("SELECT pg_get_serial_sequence('dbo.normalized_jobs', 'id')")).scalar()
        if not seq:
            return
        max_id = conn.execute(text("SELECT MAX(id) FROM dbo.normalized_jobs")).scalar()
        if max_id is None:
            conn.execute(
                text("SELECT setval(CAST(:seq AS regclass), 1, false)"),
                {"seq": seq},
            )
        else:
            conn.execute(
                text("SELECT setval(CAST(:seq AS regclass), :mx, true)"),
                {"seq": seq, "mx": int(max_id)},
            )


def seed_enrichment_e2e(
    engine: Engine,
    *,
    job_title: str | None = None,
    job_description: str | None = None,
    company_short_name: str | None = None,
    company_legal_name: str | None = None,
) -> EnrichmentE2ESeed:
    """Insert one chain of rows; returns identifiers for cleanup.

    Optional overrides customize ``job_postings`` / ``normalized_jobs`` / ``companies`` text
    for live LLM scenario tests. Defaults preserve legacy E2E literals.
    """
    _default_title = "E2E Title"
    _default_desc = "E2E description body for enrichment promotion test."
    _default_company = "E2E Co"
    title = job_title if job_title is not None else _default_title
    description = job_description if job_description is not None else _default_desc
    company = company_short_name if company_short_name is not None else _default_company

    _require_tables(engine)
    _resync_normalized_jobs_id_sequence(engine)
    insp = inspect(engine)
    e2e_naics_code = _seed_optional_naics_reference(engine, insp)
    c_created, c_updated = _company_ts_columns(insp)
    zip_col = _address_zip_column(insp)
    a_created, a_updated = _address_ts_columns(insp)
    jp_ts_cols, jp_ts_vals = _job_postings_ts_fragment(insp)

    suffix = uuid.uuid4().hex[:8]
    zip_code = f"{(int(suffix, 16) % 89999) + 10000:05d}"

    company_id = str(uuid.uuid4())
    company_address_id = str(uuid.uuid4())
    job_posting_id = str(uuid.uuid4())
    source = "e2e-enrich"
    external_id = f"e2e-ext-{suffix}"

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO dbo.postal_geo_data (zip, city, county, state_code, state, lat, lng)
                VALUES (:zip, 'E2ECity', 'E2ECo', 'TX', 'Texas', 0.0, 0.0)
                ON CONFLICT (zip) DO NOTHING
                """
            ),
            {"zip": zip_code},
        )

        cname = company_legal_name if company_legal_name is not None else f"E2E Company {suffix}"
        conn.execute(
            text(
                f"""
                INSERT INTO dbo.companies (
                    company_id, company_name, is_approved, {c_created}, {c_updated}
                )
                VALUES (
                    CAST(:cid AS uuid), :cname, true, NOW(), NOW()
                )
                """
            ),
            {"cid": company_id, "cname": cname},
        )

        conn.execute(
            text(
                f"""
                INSERT INTO dbo.company_addresses (
                    company_address_id, company_id, {zip_col}, {a_created}, {a_updated}
                )
                VALUES (
                    CAST(:aid AS uuid), CAST(:cid AS uuid), :zip, NOW(), NOW()
                )
                """
            ),
            {"aid": company_address_id, "cid": company_id, "zip": zip_code},
        )

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
                    :jtitle,
                    :jdesc,
                    false,
                    true,
                    'full-time',
                    'Remote',
                    'n/a',
                    'E2E',
                    :zip,
                    NOW(),
                    NOW(),
                    :source,
                    :eid
                    {jp_ts_vals}
                )
                """
            ),
            {
                "jpid": job_posting_id,
                "cid": company_id,
                "lid": company_address_id,
                "zip": zip_code,
                "source": source,
                "eid": external_id,
                "jtitle": title,
                "jdesc": description,
            },
        )

    factory = __import__("agents.common.data_store.database", fromlist=["get_session_factory"]).get_session_factory()
    session: Session = factory()
    try:
        nj = NormalizedJob(
            raw_job_id=None,
            ingestion_run_id=f"e2e-run-{suffix}",
            region_id="e2e",
            source=source,
            external_id=external_id,
            title=title,
            company=company,
            description=description,
            city="El Paso",
            state_province="Texas",
            country="US",
            is_remote=False,
            work_arrangement="on-site",
            date_posted=datetime(2023, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
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
                    'e2e-1',
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
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return EnrichmentE2ESeed(
        zip_code=zip_code,
        company_id=company_id,
        company_address_id=company_address_id,
        job_posting_id=job_posting_id,
        normalized_job_id=nj_id,
        e2e_naics_code=e2e_naics_code,
    )


def teardown_enrichment_e2e(engine: Engine, seed: EnrichmentE2ESeed) -> None:
    """Remove seeded rows (best-effort order)."""
    with engine.begin() as conn:
        if seed.e2e_naics_code:
            conn.execute(
                text(
                    """
                    DELETE FROM dbo.naics
                    WHERE naics_code = :code
                      AND title = 'E2E enrichment pipeline reference row'
                    """
                ),
                {"code": seed.e2e_naics_code},
            )
        conn.execute(
            text("DELETE FROM dbo.extracted_intelligence WHERE normalized_job_id = :id"),
            {"id": seed.normalized_job_id},
        )
        conn.execute(
            text("DELETE FROM dbo.normalized_jobs WHERE id = :id"),
            {"id": seed.normalized_job_id},
        )
        conn.execute(
            text("DELETE FROM dbo.job_postings WHERE job_posting_id::text = :jpid"),
            {"jpid": seed.job_posting_id},
        )
        conn.execute(
            text("DELETE FROM dbo.company_addresses WHERE company_address_id::text = :aid"),
            {"aid": seed.company_address_id},
        )
        conn.execute(
            text("DELETE FROM dbo.companies WHERE company_id::text = :cid"),
            {"cid": seed.company_id},
        )
        conn.execute(
            text("DELETE FROM dbo.postal_geo_data WHERE zip = :zip"),
            {"zip": seed.zip_code},
        )
