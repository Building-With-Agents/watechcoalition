"""Employer profile enrichment: company size, AI maturity, sector, known-employer flag.

Uses :func:`agents.common.llm_client.invoke_structured_extraction_llm` for audit and
cost tracking. All categorical fields default to ``unknown`` when signals are weak
or the LLM fails. ``is_known_employer`` is derived from an exact normalized match on
``dbo.companies`` (defensive; no fuzzy guess).
"""

from __future__ import annotations

from typing import Literal

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import update
from sqlalchemy.orm import Session

from agents.common.data_store.models import NormalizedJob
from agents.common.llm_client import invoke_structured_extraction_llm
from agents.common.types.job_profile import EmployerProfile
from agents.enrichment.employer_profile_storage import upsert_employer_profile_by_company_id
from agents.enrichment.resolvers.company_resolver import (
    lookup_company_exact,
    normalize_company_name,
)

log = structlog.get_logger()

AUDIT_AGENT_EMPLOYER = "enrichment-employer-classifier"

_EMPLOYER_DEPLOYMENT_KEYS: tuple[str, ...] = (
    "EXTRACTION_DEPLOYMENT_EMPLOYER",
    "EXTRACTION_DEPLOYMENT_NAICS",
    "EXTRACTION_DEPLOYMENT_SKILLS",
    "EXTRACTION_MODEL_SKILLS",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
)

_MAX_DESC_CHARS = 4000

# Closed set for high-level sector; anything else maps to unknown after LLM response.
_SECTOR_CANONICAL = frozenset(
    {
        "technology",
        "finance",
        "healthcare",
        "retail",
        "manufacturing",
        "education",
        "government",
        "consulting",
        "media",
        "energy",
        "logistics",
        "telecommunications",
        "real_estate",
        "hospitality",
        "nonprofit",
        "unknown",
    }
)

_SECTOR_ALIASES: dict[str, str] = {
    "tech": "technology",
    "it": "technology",
    "software": "technology",
    "fintech": "finance",
    "financial_services": "finance",
    "banking": "finance",
    "insurance": "finance",
    "health": "healthcare",
    "pharma": "healthcare",
    "biotech": "healthcare",
    "public_sector": "government",
    "ngo": "nonprofit",
}


class EmployerClassificationLLMOutput(BaseModel):
    """Structured LLM response; invalid combinations are fixed in :func:`build_employer_profile`."""

    company_size: Literal["startup", "smb", "mid_market", "enterprise", "unknown"] = Field(
        ...,
        description="startup | smb | mid_market | enterprise | unknown — use unknown unless job text clearly supports one label.",
    )
    ai_maturity_signal: Literal["ai_native", "ai_adopting", "ai_exploring", "traditional", "unknown"] = Field(
        ...,
        description="ai_native | ai_adopting | ai_exploring | traditional | unknown.",
    )
    sector: str = Field(
        ...,
        description="High-level industry: one of technology, finance, healthcare, retail, manufacturing, education, government, consulting, media, energy, logistics, telecommunications, real_estate, hospitality, nonprofit — or unknown.",
    )


def registry_has_exact_company_name(session: Session, raw_company_name: str) -> bool:
    """True when ``normalize_company_name(company_name)`` equals a row in ``dbo.companies``."""
    raw = (raw_company_name or "").strip()
    if not raw:
        return False
    try:
        norm = normalize_company_name(raw)
    except Exception as exc:
        log.warning("employer_normalize_company_failed", error=str(exc))
        return False
    if not norm:
        return False
    try:
        return lookup_company_exact(norm, session) is not None
    except Exception as exc:
        log.warning("employer_known_lookup_failed", error=str(exc))
        return False


def _canonical_sector(raw: str) -> str:
    s = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not s:
        return "unknown"
    if s in _SECTOR_CANONICAL:
        return s
    return _SECTOR_ALIASES.get(s, "unknown")


def _build_prompt(company_name: str, description: str | None) -> str:
    desc = (description or "").strip()[:_MAX_DESC_CHARS]
    sectors = ", ".join(sorted(_SECTOR_CANONICAL - {"unknown"}))
    return f"""Infer employer signals from the job posting context only. Prefer unknown over guessing.

Company name (from posting): {company_name}
Job description:
{desc}

Fields:
1) company_size — startup (early-stage / seed / small team language), smb (small business, regional, tens of employees), mid_market (hundreds, national mid-size), enterprise (Fortune-scale, global enterprise, 1000+ employees, household-name conglomerates). Use unknown if size is not clearly indicated.

2) ai_maturity_signal — ai_native (AI is the core product), ai_adopting (actively deploying ML/GenAI in products or ops), ai_exploring (pilots, R&D, evaluating AI), traditional (no meaningful AI signals). unknown if unclear.

3) sector — exactly one of: {sectors}, or unknown. Map the employer's primary industry; use unknown if ambiguous.

Respond with structured data only. Use the literal unknown for any field when evidence is weak or missing."""


def build_employer_profile(
    job_description: str | None,
    company_name: str,
    session: Session,
) -> EmployerProfile:
    """
    Return a validated :class:`~agents.common.types.job_profile.EmployerProfile`.

    On LLM failure, returns defaults with ``unknown`` literals and still sets
    ``is_known_employer`` from the companies table when lookup succeeds.
    """
    company = (company_name or "").strip()
    desc = job_description if isinstance(job_description, str) else None
    is_known = registry_has_exact_company_name(session, company)

    base = EmployerProfile(is_known_employer=is_known)

    try:
        parsed, meta = invoke_structured_extraction_llm(
            _build_prompt(company, desc),
            EmployerClassificationLLMOutput,
            agent_name=AUDIT_AGENT_EMPLOYER,
            deployment_env_keys=_EMPLOYER_DEPLOYMENT_KEYS,
            model_tier_for_cost="haiku",
        )
    except Exception as exc:
        log.warning("employer_llm_invoke_failed", error=str(exc))
        return base

    if meta.get("extraction_failed") or parsed is None:
        log.info(
            "employer_classification_degraded",
            extraction_failed=meta.get("extraction_failed"),
            error_reason=meta.get("error_reason"),
        )
        return base

    merged = EmployerProfile.model_validate(
        {
            "company_size": parsed.company_size,
            "ai_maturity_signal": parsed.ai_maturity_signal,
            "sector": _canonical_sector(parsed.sector),
            "is_known_employer": is_known,
        }
    )
    return merged


def persist_employer_metadata(
    session: Session,
    profile: EmployerProfile,
    *,
    company_id: str | None = None,
    normalized_job_id: int | None = None,
    source: str | None = None,
    external_id: str | None = None,
) -> None:
    """Persist employer enrichment: upsert ``dbo.employer_profiles`` when ``company_id`` is known.

    If ``company_id`` is missing or blank, write JSON to ``dbo.normalized_jobs.employer_metadata``
    only (no ``employer_profiles`` row).
    """
    payload = profile.model_dump(mode="json")
    cid = str(company_id).strip() if company_id is not None else ""
    if cid:
        upsert_employer_profile_by_company_id(session, cid, payload)
        return

    stmt = None
    if normalized_job_id is not None:
        stmt = update(NormalizedJob).where(NormalizedJob.id == int(normalized_job_id)).values(employer_metadata=payload)
    elif source is not None and external_id is not None and str(source).strip() and str(external_id).strip():
        stmt = (
            update(NormalizedJob)
            .where(NormalizedJob.source == str(source).strip())
            .where(NormalizedJob.external_id == str(external_id).strip())
            .values(employer_metadata=payload)
        )
    if stmt is not None:
        session.execute(stmt)
