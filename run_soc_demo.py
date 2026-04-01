from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select, func

from agents.common.data_store.database import session_scope
from agents.common.data_store.models import NormalizedJob, SOCC
from agents.common.llm_client import invoke_skills_llm
from agents.common.types.job_record import JobRecord
from agents.enrichment.classification import build_job_profile_with_soc


def _load_env() -> None:
    repo_root = Path(__file__).resolve().parent
    load_dotenv(repo_root / ".env", override=False)


def _llm_provider() -> str:
    return os.getenv("LLM_PROVIDER", "anthropic").strip().lower().replace("-", "_")


def _azure_openai_configured() -> bool:
    if not os.getenv("AZURE_OPENAI_ENDPOINT", "").strip():
        return False
    if not os.getenv("AZURE_OPENAI_API_KEY", "").strip():
        return False
    deployment = (
        os.getenv("EXTRACTION_DEPLOYMENT_SKILLS")
        or os.getenv("EXTRACTION_MODEL_SKILLS")
        or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    )
    return bool(deployment and deployment.strip())


def _ensure_llm_configured_or_exit() -> None:
    if os.getenv("SOC_DEMO_SKIP_LLM", "").strip() in ("1", "true", "yes"):
        return
    provider = _llm_provider()
    if provider != "azure_openai":
        print(
            "run_soc_demo.py calls agents.common.llm_client.invoke_skills_llm() (Azure OpenAI only). "
            f"Set LLM_PROVIDER=azure_openai (current: {provider!r}), or run with SOC_DEMO_SKIP_LLM=1.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not _azure_openai_configured():
        print(
            "Missing Azure OpenAI configuration. invoke_skills_llm() needs:\n"
            "  AZURE_OPENAI_ENDPOINT\n"
            "  AZURE_OPENAI_API_KEY\n"
            "  AZURE_OPENAI_DEPLOYMENT_NAME (or EXTRACTION_DEPLOYMENT_SKILLS / EXTRACTION_MODEL_SKILLS)\n"
            "Add these to repo-root .env, or run with SOC_DEMO_SKIP_LLM=1.",
            file=sys.stderr,
        )
        raise SystemExit(1)


def normalized_job_to_record(row: NormalizedJob) -> JobRecord:
    return JobRecord(
        raw_job_id=row.raw_job_id or 0,
        ingestion_run_id=row.ingestion_run_id,
        region_id=row.region_id or "",
        source=row.source,
        external_id=row.external_id,
        title=row.title,
        company=row.company,
        description=row.description,
        requirements=row.requirements,
        responsibilities=row.responsibilities,
        job_url=row.job_url,
        city=row.city,
        state_province=row.state_province,
        country=row.country,
        work_arrangement=row.work_arrangement,
        is_remote=row.is_remote,
        date_posted=row.date_posted,
        salary_raw=row.salary_raw,
        salary_min=row.salary_min,
        salary_max=row.salary_max,
        salary_currency=row.salary_currency,
        salary_period=row.salary_period,
        employment_type=row.employment_type,
        experience_level=row.experience_level,
        occupation_code=row.occupation_code,
        mapper_used=row.mapper_used or "",
    )


def make_soc_llm() -> Callable[[str], str]:
    if os.getenv("SOC_DEMO_SKIP_LLM", "").strip() in ("1", "true", "yes"):
        return lambda _prompt: "unclassified"

    def llm(prompt: str) -> str:
        try:
            text, meta = invoke_skills_llm(
                prompt,
                agent_name="soc-enrichment-demo",
            )
        except TypeError as exc:
            if "api_key" in str(exc).lower() or "auth" in str(exc).lower():
                print(
                    f"LLM authentication failed (missing key?). "
                    f"Check AZURE_OPENAI_* env vars. Detail: {exc}",
                    file=sys.stderr,
                )
                return "unclassified"
            raise
        if not meta.get("success") or meta.get("extraction_failed"):
            return "unclassified"
        return (text or "").strip()

    return llm


async def main() -> None:
    _load_env()
    if not os.getenv("PYTHON_DATABASE_URL"):
        raise SystemExit("Set PYTHON_DATABASE_URL (postgresql+psycopg2://...)")
    _ensure_llm_configured_or_exit()

    with session_scope() as session:
        row = session.scalars(
            select(NormalizedJob).order_by(NormalizedJob.id.desc()).limit(1)
        ).first()
        if row is None:
            print("No rows in dbo.normalized_jobs — seed or ingest data first.")
            return

        job_record = normalized_job_to_record(row)
        print("title:", job_record.title)
        print("company:", job_record.company)

        # --- Tier 1 candidate lookup (always runs) ---
        first_word = job_record.title.lower().split()[0]
        candidates = session.execute(
            select(SOCC.code, SOCC.title)
            .where(func.lower(SOCC.title).contains(first_word))
            .where(SOCC.version == "2018")
            .limit(5)
        ).all()

        if candidates:
            print("\nSOC candidates from dbo.socc:")
            for r in candidates:
                print(f"  {r.code}: {r.title}")
        else:
            print("\nNo SOC candidates found in dbo.socc for this title.")

        if os.getenv("SOC_DEMO_SKIP_LLM", "").strip() in ("1", "true", "yes"):
            print("\n-- SKIP_LLM mode: skipping LLM classification --")
            return

        # --- Full classification with LLM ---
        job_profile = await build_job_profile_with_soc(
            job_record,
            session,
            make_soc_llm(),
        )
        print("\nsoc_code:", job_profile.soc_code)


if __name__ == "__main__":
    asyncio.run(main())
