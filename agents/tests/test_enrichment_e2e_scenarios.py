"""Live LLM integration: diverse job scenarios through ``EnrichmentAgent`` → ``job_postings``.

**Requires** ``PYTHON_DATABASE_URL``, migrated schema, populated ``dbo.socc`` and ``dbo.naics``,
Azure/OpenAI (or configured provider), and ``pytest --live``.

**Run (see logs on stdout):**

    cd agents
    pytest tests/test_enrichment_e2e_scenarios.py --live -s

No LLM mocks — classifiers and spam preview call real endpoints.

Assertions:

- **SOC:** ``soc_code`` must be non-null and digit-grounded in ``dbo.socc`` (checked
  before NAICS so failures still prove SOC).
- **NAICS:** ``naics_code`` is always non-null text: a 6-digit code grounded in ``dbo.naics``,
  or the literal ``unknown`` (same pattern as employer categorical fields).
- **Employer:** all four ``employer_profiles`` fields non-null with scenario-specific bands.
- **Audit:** aggregate and per-``agent_name`` token sums from ``dbo.llm_audit_log`` for the run window.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.classifiers.employer_classifier import AUDIT_AGENT_EMPLOYER
from agents.enrichment.classifiers.naics_classifier import AUDIT_AGENT_NAICS
from agents.enrichment.classifiers.spam_preview import AUDIT_AGENT_SPAM_PREVIEW
from agents.tests.db_seed_enrichment_e2e import (
    EnrichmentE2ESeed,
    seed_enrichment_e2e,
    teardown_enrichment_e2e,
)

log = logging.getLogger("enrichment_e2e_scenarios")

pytestmark = pytest.mark.live_llm

# SOC resolution logs under this name (see ``agents.enrichment.agent._enrichment_soc_llm``).
AUDIT_AGENT_SOC = "enrichment-agent"

# Expected enrichment classifiers / spam preview (for ordered logging and soft checks).
ENRICHMENT_AUDIT_AGENT_NAMES: tuple[str, ...] = (
    AUDIT_AGENT_SOC,
    AUDIT_AGENT_NAICS,
    AUDIT_AGENT_EMPLOYER,
    AUDIT_AGENT_SPAM_PREVIEW,
)


def _soc_digits_key(code: str) -> str:
    """Match ``soc_classifier`` normalization (digits only) for grounding queries."""
    return re.sub(r"\D", "", code or "")


@dataclass(frozen=True)
class LiveJobScenario:
    """One synthetic posting: text shown to the LLM + acceptable employer label sets."""

    slug: str
    job_title: str
    job_description: str
    company_short_name: str
    company_legal_name: str
    allowed_company_size: frozenset[str] = field(
        default_factory=lambda: frozenset({"startup", "smb", "mid_market", "enterprise", "unknown"})
    )
    allowed_ai_maturity: frozenset[str] = field(
        default_factory=lambda: frozenset({"ai_native", "ai_adopting", "ai_exploring", "traditional", "unknown"})
    )
    allowed_sector: frozenset[str] = field(
        default_factory=lambda: frozenset(
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
    )


SCENARIOS: tuple[LiveJobScenario, ...] = (
    LiveJobScenario(
        slug="senior_ai_engineer_startup",
        job_title="Senior AI Engineer",
        job_description=(
            "We are a 5-person seed-stage startup building LLM-powered document intelligence. "
            "You will own our RAG pipeline, fine-tune open models, and ship to production weekly. "
            "Equity-heavy comp; fully remote; we move fast and iterate with customers daily."
        ),
        company_short_name="NeuralSpark Labs",
        company_legal_name="NeuralSpark Labs Inc",
        allowed_company_size=frozenset({"startup", "smb", "unknown"}),
        allowed_ai_maturity=frozenset({"ai_native", "ai_adopting", "ai_exploring", "unknown"}),
        allowed_sector=frozenset({"technology", "unknown"}),
    ),
    LiveJobScenario(
        slug="store_manager_retail_enterprise",
        job_title="Store Manager",
        job_description=(
            "Lead daily operations for a high-traffic big-box retail location with 120+ associates. "
            "Own P&L, inventory, merchandising standards, and compliance. "
            "Fortune 500 parent company; structured processes, multi-shift coverage, minimal technology in daily work."
        ),
        company_short_name="BigBox Retail Co",
        company_legal_name="National Retail Holdings LLC",
        allowed_company_size=frozenset({"enterprise", "mid_market", "smb", "unknown"}),
        allowed_ai_maturity=frozenset({"traditional", "ai_exploring", "unknown", "ai_adopting"}),
        allowed_sector=frozenset({"retail", "unknown"}),
    ),
    LiveJobScenario(
        slug="government_it_contractor",
        job_title="IT Systems Analyst",
        job_description=(
            "Support a state agency ERP and case-management systems. "
            "Public-sector procurement rules, security clearance friendly, on-site hybrid in capital city. "
            "Work with vendors under fixed-price SOWs; change requests require formal approval."
        ),
        company_short_name="CivicTech Partners",
        company_legal_name="CivicTech Partners Government Services",
        allowed_company_size=frozenset({"smb", "mid_market", "enterprise", "unknown"}),
        allowed_ai_maturity=frozenset({"traditional", "ai_exploring", "ai_adopting", "unknown"}),
        allowed_sector=frozenset({"government", "consulting", "technology", "unknown"}),
    ),
    LiveJobScenario(
        slug="healthcare_data_analyst",
        job_title="Healthcare Data Analyst",
        job_description=(
            "Analyze patient flow, readmission rates, and payer mix for a 400-bed hospital system. "
            "SQL, Epic/Caboodle extracts, HIPAA environment, collaborate with clinical quality teams."
        ),
        company_short_name="River Valley Health",
        company_legal_name="River Valley Health System",
        allowed_company_size=frozenset({"enterprise", "mid_market", "smb", "unknown"}),
        allowed_ai_maturity=frozenset({"traditional", "ai_exploring", "ai_adopting", "ai_native", "unknown"}),
        allowed_sector=frozenset({"healthcare", "technology", "unknown"}),
    ),
)


@pytest.fixture(scope="module", autouse=True)
def _configure_stdlib_logging_for_pytest_cap() -> None:
    """So ``pytest -s`` shows INFO lines from this module (structlog is unchanged)."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s %(name)s %(message)s",
        )
    else:
        root.setLevel(logging.INFO)
        logging.getLogger("enrichment_e2e_scenarios").setLevel(logging.INFO)


@pytest.fixture(scope="module")
def scenarios_e2e_engine() -> Engine:
    url = os.getenv("PYTHON_DATABASE_URL")
    if not url:
        pytest.skip("PYTHON_DATABASE_URL not set")
    return create_engine(url, future=True)


@pytest.fixture(scope="module", autouse=True)
def _scenarios_require_uuid_employer_profiles(scenarios_e2e_engine: Engine) -> None:
    insp = inspect(scenarios_e2e_engine)
    if not insp.has_table("employer_profiles", schema="dbo"):
        pytest.skip("dbo.employer_profiles missing — run agents/scripts/db_check.py migrate")
    with scenarios_e2e_engine.connect() as conn:
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
        pytest.skip("dbo.employer_profiles.id must be uuid (run migrations).")


def test_reference_tables_socc_and_naics_have_rows(scenarios_e2e_engine: Engine) -> None:
    """Pre-check: SOC and NAICS catalogs must be populated for grounded classification."""
    with scenarios_e2e_engine.connect() as conn:
        socc_n = conn.execute(text("SELECT COUNT(*) FROM dbo.socc")).scalar() or 0
        naics_n = conn.execute(text("SELECT COUNT(*) FROM dbo.naics")).scalar() or 0
    assert int(socc_n) > 0, "dbo.socc is empty — seed SOC reference data"
    assert int(naics_n) > 0, "dbo.naics is empty — seed NAICS reference data"
    log.info("reference_data_counts socc=%s naics=%s", socc_n, naics_n)


def _fetch_job_posting_promotion(engine: Engine, job_posting_id: str) -> dict[str, Any]:
    with engine.connect() as conn:
        return dict(
            conn.execute(
                text(
                    """
                    SELECT naics_code, soc_code, employer_profile_id::text AS employer_profile_id,
                           quality_score
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


def _occupation_code_grounded_in_socc(engine: Engine, occupation_code: str) -> bool:
    digits = _soc_digits_key(occupation_code)
    if not digits:
        return False
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT 1 FROM dbo.socc
                WHERE regexp_replace(code, '[^0-9]', '', 'g') = :digits
                LIMIT 1
                """
            ),
            {"digits": digits},
        ).first()
    return row is not None


def _naics_code_grounded(engine: Engine, naics_code: str) -> bool:
    if not naics_code or not str(naics_code).strip():
        return False
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT 1 FROM dbo.naics WHERE naics_code = :code LIMIT 1"),
            {"code": str(naics_code).strip()},
        ).first()
    return row is not None


def _fetch_employer_profile(engine: Engine, company_id: str) -> dict[str, Any]:
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


def _sum_llm_audit_tokens_since(engine: Engine, since: datetime) -> dict[str, int]:
    insp = inspect(engine)
    if not insp.has_table("llm_audit_log", schema="dbo"):
        return {"token_count": 0, "input_tokens": 0, "output_tokens": 0, "rows": 0}
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                    SELECT
                        COALESCE(SUM(token_count), 0)::bigint AS token_count,
                        COALESCE(SUM(input_tokens), 0)::bigint AS input_tokens,
                        COALESCE(SUM(output_tokens), 0)::bigint AS output_tokens,
                        COUNT(*)::bigint AS rows
                    FROM dbo.llm_audit_log
                    WHERE created_at >= :since
                    """
                ),
                {"since": since},
            )
            .mappings()
            .first()
        )
    return {k: int(row[k] or 0) for k in ("token_count", "input_tokens", "output_tokens", "rows")}


def _llm_audit_breakdown_by_agent_since(engine: Engine, since: datetime) -> list[dict[str, Any]]:
    """Per ``agent_name`` token aggregates for rows with ``created_at >= since``."""
    insp = inspect(engine)
    if not insp.has_table("llm_audit_log", schema="dbo"):
        return []
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text(
                    """
                SELECT
                    agent_name,
                    COUNT(*)::bigint AS rows,
                    COALESCE(SUM(token_count), 0)::bigint AS token_count,
                    COALESCE(SUM(input_tokens), 0)::bigint AS input_tokens,
                    COALESCE(SUM(output_tokens), 0)::bigint AS output_tokens
                FROM dbo.llm_audit_log
                WHERE created_at >= :since
                GROUP BY agent_name
                ORDER BY agent_name
                """
                ),
                {"since": since},
            )
            .mappings()
            .all()
        )
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "agent_name": str(r["agent_name"]),
                "rows": int(r["rows"] or 0),
                "token_count": int(r["token_count"] or 0),
                "input_tokens": int(r["input_tokens"] or 0),
                "output_tokens": int(r["output_tokens"] or 0),
            }
        )
    return out


def _log_llm_audit_per_classification(slug: str, breakdown: list[dict[str, Any]]) -> None:
    known = {name: None for name in ENRICHMENT_AUDIT_AGENT_NAMES}
    for row in breakdown:
        name = row["agent_name"]
        if name in known:
            known[name] = row
    for agent_name in ENRICHMENT_AUDIT_AGENT_NAMES:
        row = known[agent_name]
        if row is None:
            log.info(
                "llm_audit_per_classification slug=%s agent=%s rows=0 token_count=0 "
                "(no rows in window — e.g. NAICS may skip LLM when there are no candidates)",
                slug,
                agent_name,
            )
            continue
        log.info(
            "llm_audit_per_classification slug=%s agent=%s rows=%s token_count=%s input_tokens=%s output_tokens=%s",
            slug,
            agent_name,
            row["rows"],
            row["token_count"],
            row["input_tokens"],
            row["output_tokens"],
        )
    for row in breakdown:
        if row["agent_name"] not in ENRICHMENT_AUDIT_AGENT_NAMES:
            log.info(
                "llm_audit_per_classification slug=%s agent=%s rows=%s token_count=%s input_tokens=%s output_tokens=%s",
                slug,
                row["agent_name"],
                row["rows"],
                row["token_count"],
                row["input_tokens"],
                row["output_tokens"],
            )


def _run_skills_extracted(seed: EnrichmentE2ESeed, scenario: LiveJobScenario) -> None:
    agent = EnrichmentAgent()
    ev = EventEnvelope(
        correlation_id=f"live-scenario-{uuid.uuid4().hex[:8]}",
        agent_id="skills-extraction-agent",
        payload={
            "event_type": "SkillsExtracted",
            "posting_id": 999001,
            "normalized_job_id": seed.normalized_job_id,
            "title": scenario.job_title,
            "description": scenario.job_description,
            "company": scenario.company_short_name,
            "skills": [],
        },
    )
    agent.process(ev)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.slug)
def test_live_enrichment_scenario_end_to_end_grounded_codes_and_employer_profile(
    scenarios_e2e_engine: Engine,
    scenario: LiveJobScenario,
) -> None:
    """Real LLM path: SOC grounded in ``dbo.socc``; NAICS never NULL (code or ``unknown``); employer bands."""
    log.info(
        "scenario_start slug=%s input_description=%s",
        scenario.slug,
        scenario.job_description[:800],
    )
    try:
        seed = seed_enrichment_e2e(
            scenarios_e2e_engine,
            job_title=scenario.job_title,
            job_description=scenario.job_description,
            company_short_name=scenario.company_short_name,
            company_legal_name=scenario.company_legal_name,
        )
    except Exception as exc:
        pytest.skip(f"seed failed: {exc}")

    audit_since = datetime.now(timezone.utc)
    try:
        _run_skills_extracted(seed, scenario)
        usage = _sum_llm_audit_tokens_since(scenarios_e2e_engine, audit_since)
        breakdown = _llm_audit_breakdown_by_agent_since(scenarios_e2e_engine, audit_since)
        log.info(
            "llm_audit_since_run slug=%s rows=%s token_count=%s input_tokens=%s output_tokens=%s",
            scenario.slug,
            usage["rows"],
            usage["token_count"],
            usage["input_tokens"],
            usage["output_tokens"],
        )
        _log_llm_audit_per_classification(scenario.slug, breakdown)

        agents_seen = {r["agent_name"] for r in breakdown}
        for req in (AUDIT_AGENT_SOC, AUDIT_AGENT_EMPLOYER, AUDIT_AGENT_SPAM_PREVIEW):
            assert req in agents_seen, (
                f"expected llm_audit_log rows for agent_name={req!r} slug={scenario.slug}, "
                f"got agents={sorted(agents_seen)}"
            )

        assert usage["rows"] > 0, "expected llm_audit_log rows for this enrichment run"
        measurable = usage["token_count"] + usage["input_tokens"] + usage["output_tokens"]
        assert measurable > 0, (
            f"expected measurable token usage in llm_audit_log for slug={scenario.slug}, got {usage!r}"
        )

        jp = _fetch_job_posting_promotion(scenarios_e2e_engine, seed.job_posting_id)
        assert jp.get("quality_score") is not None, "promotion should set quality_score"

        occ = jp.get("soc_code")
        assert occ and str(occ).strip(), f"expected soc_code on job_postings, got {occ!r}"
        log.info("extracted_soc_code slug=%s soc_code=%s", scenario.slug, occ)
        assert _occupation_code_grounded_in_socc(scenarios_e2e_engine, str(occ)), (
            f"soc_code {occ!r} not found in dbo.socc (digit-normalized match)"
        )

        naics = jp.get("naics_code")
        assert naics is not None and str(naics).strip(), (
            f"naics_code must be non-null non-empty (literal 'unknown' when uncertain), got {naics!r}"
        )
        naics_s = str(naics).strip()
        log.info("extracted_naics_code slug=%s naics_code=%s", scenario.slug, naics_s)
        if naics_s.lower() == "unknown":
            log.info("naics_uncertain_literal_unknown slug=%s (skipping dbo.naics grounding)", scenario.slug)
        else:
            assert _naics_code_grounded(scenarios_e2e_engine, naics_s), f"naics_code {naics_s!r} not found in dbo.naics"

        assert jp.get("employer_profile_id"), "employer_profile_id should be set when company_id resolves"
        ep = _fetch_employer_profile(scenarios_e2e_engine, seed.company_id)
        assert ep, "employer_profiles row expected for seeded company_id"

        cs = ep.get("company_size")
        am = ep.get("ai_maturity_signal")
        sec = ep.get("sector")
        known = ep.get("is_known_employer")
        assert cs is not None and str(cs).strip(), "company_size must be non-null text"
        assert am is not None and str(am).strip(), "ai_maturity_signal must be non-null text"
        assert sec is not None and str(sec).strip(), "sector must be non-null text"
        assert known is not None, "is_known_employer must be set (bool)"

        cs_s = str(cs).strip().lower()
        am_s = str(am).strip().lower()
        sec_s = str(sec).strip().lower()
        assert cs_s in scenario.allowed_company_size, (
            f"company_size {cs_s!r} not in allowed {scenario.allowed_company_size} for {scenario.slug}"
        )
        assert am_s in scenario.allowed_ai_maturity, (
            f"ai_maturity_signal {am_s!r} not in allowed {scenario.allowed_ai_maturity} for {scenario.slug}"
        )
        assert sec_s in scenario.allowed_sector, (
            f"sector {sec_s!r} not in allowed {scenario.allowed_sector} for {scenario.slug}"
        )
    finally:
        teardown_enrichment_e2e(scenarios_e2e_engine, seed)
