"""NAICS 2022 industry classification using ``dbo.naics`` reference rows only.

Mirrors the defensive pattern in :mod:`agents.enrichment.classifiers.soc_classifier`:
narrow candidates from the database, prompt the LLM to pick exactly one code or
``unknown``, then re-validate against the candidate set.

LLM calls use :func:`agents.common.llm_client.invoke_structured_extraction_llm` so
token usage and cost are written to ``llm_audit_log`` via ``log_extraction_event``.
"""

from __future__ import annotations

import re

import structlog
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from agents.common.data_store.models import NAICS
from agents.common.llm_client import invoke_structured_extraction_llm
from agents.enrichment.classification import tokenize

log = structlog.get_logger()

AUDIT_AGENT_NAICS = "enrichment-naics-classifier"

_NAICS_DEPLOYMENT_KEYS: tuple[str, ...] = (
    "EXTRACTION_DEPLOYMENT_NAICS",
    "EXTRACTION_DEPLOYMENT_SKILLS",
    "EXTRACTION_MODEL_SKILLS",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
)

# NAICS codes are numeric strings; allow LLM typos like trailing spaces.
_CODE_IN_TEXT = re.compile(r"\b\d{2,6}\b")


class NAICSClassificationOutput(BaseModel):
    """Structured LLM response: one catalog code or ``unknown``."""

    naics_code: str = Field(
        ...,
        description='Exactly one NAICS code from the candidate list, or the literal "unknown".',
    )


def _needles_from_job(title: str, description: str | None) -> list[str]:
    needles: list[str] = []
    for part in (title or "").strip().split():
        low = part.lower().strip(".,;:!?()[]\"'")
        if len(low) >= 3:
            needles.append(low)
            if len(needles) >= 3:
                break
    if len(needles) < 3 and description:
        toks = sorted(tokenize(description[:1200]), key=len, reverse=True)
        for t in toks:
            if t not in needles and len(t) >= 3:
                needles.append(t)
            if len(needles) >= 5:
                break
    return needles[:5]


def get_naics_candidates(
    session: Session,
    title: str,
    description: str | None,
    *,
    limit: int = 25,
) -> list[dict[str, str]]:
    """Return up to *limit* ``{code, title}`` rows whose titles match job text needles."""
    needles = _needles_from_job(title, description)
    if not needles:
        return []

    conds = [func.lower(NAICS.title).contains(n) for n in needles]
    stmt = select(NAICS.naics_code, NAICS.title).where(or_(*conds)).distinct().limit(limit)
    rows = session.execute(stmt).all()
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for r in rows:
        code, tit = str(r[0]).strip(), str(r[1]).strip()
        if code and code not in seen:
            seen.add(code)
            out.append({"code": code, "title": tit})
    return out


def _resolve_llm_naics_pick(raw: str, candidate_codes: set[str]) -> str:
    """Map free-form LLM text to a member of *candidate_codes* or ``unknown``."""
    s = (raw or "").strip()
    if not s or s.lower() == "unknown":
        return "unknown"
    if s in candidate_codes:
        return s
    unquoted = s.strip("`\"'")
    if unquoted in candidate_codes:
        return unquoted
    contained = [c for c in candidate_codes if c and c in s]
    if len(contained) == 1:
        return contained[0]
    if len(contained) > 1:
        return "unknown"
    regex_hits = [m.group(0) for m in _CODE_IN_TEXT.finditer(s) if m.group(0) in candidate_codes]
    unique = list(dict.fromkeys(regex_hits))
    if len(unique) == 1:
        return unique[0]
    return "unknown"


def _build_prompt(
    title: str,
    description: str | None,
    candidates: list[dict[str, str]],
) -> str:
    lines = [f'{c["code"]}: {c["title"]}' for c in candidates]
    block = "\n".join(lines)
    desc = (description or "").strip()
    return f"""Classify this job into one NAICS 2022 industry from the list below.

Job title: {title}
Job description: {desc}

NAICS candidates (choose exactly one code from this list, or unknown):
{block}

Rules:
- Respond with structured data only.
- Field naics_code must be exactly one of the numeric codes shown above, or the literal unknown.
- Use unknown if the job text does not clearly fit any single listed industry."""


def classify_naics(job_title: str, job_description: str | None, session: Session) -> str:
    """
    Return a ``naics_code`` present in ``dbo.naics`` or ``unknown``.

    On LLM failure or empty candidates, returns ``unknown`` (no exception).
    """
    title = (job_title or "").strip()
    desc = job_description if isinstance(job_description, str) else None

    try:
        candidates = get_naics_candidates(session, title, desc)
    except Exception as exc:
        log.warning("naics_candidate_query_failed", error=str(exc))
        return "unknown"

    if not candidates:
        return "unknown"

    candidate_codes = {c["code"] for c in candidates}
    prompt = _build_prompt(title, desc, candidates)

    try:
        parsed, meta = invoke_structured_extraction_llm(
            prompt,
            NAICSClassificationOutput,
            agent_name=AUDIT_AGENT_NAICS,
            deployment_env_keys=_NAICS_DEPLOYMENT_KEYS,
            model_tier_for_cost="haiku",
        )
    except Exception as exc:
        log.warning("naics_llm_invoke_failed", error=str(exc))
        return "unknown"

    if meta.get("extraction_failed") or parsed is None:
        log.info(
            "naics_classification_degraded",
            extraction_failed=meta.get("extraction_failed"),
            error_reason=meta.get("error_reason"),
        )
        return "unknown"

    picked = _resolve_llm_naics_pick(parsed.naics_code, candidate_codes)
    if picked not in candidate_codes:
        return "unknown"
    return picked
