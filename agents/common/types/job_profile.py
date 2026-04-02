"""JobProfile — fully enriched job posting in the pipeline.

Extends JobRecord with enrichment outputs (Week 6: SOC/NAICS classification).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from agents.common.types.job_record import JobRecord

CompanySize = Literal["startup", "smb", "mid_market", "enterprise", "unknown"]
AiMaturitySignal = Literal["ai_native", "ai_adopting", "ai_exploring", "traditional", "unknown"]

_COMPANY_SIZES: frozenset[str] = frozenset({"startup", "smb", "mid_market", "enterprise", "unknown"})
_AI_MATURITY: frozenset[str] = frozenset({"ai_native", "ai_adopting", "ai_exploring", "traditional", "unknown"})


class EmployerProfile(BaseModel):
    """Employer-level enrichment; unknowns use the literal value ``unknown`` or safe defaults."""

    company_size: CompanySize = "unknown"
    ai_maturity_signal: AiMaturitySignal = "unknown"
    sector: str = "unknown"
    is_known_employer: bool = False

    @field_validator("company_size", mode="before")
    @classmethod
    def company_size_coerce(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "unknown"
        if not isinstance(v, str):
            return "unknown"
        s = v.strip().lower()
        return s if s in _COMPANY_SIZES else "unknown"

    @field_validator("ai_maturity_signal", mode="before")
    @classmethod
    def ai_maturity_coerce(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "unknown"
        if not isinstance(v, str):
            return "unknown"
        s = v.strip().lower()
        return s if s in _AI_MATURITY else "unknown"

    @field_validator("sector", mode="before")
    @classmethod
    def sector_coerce(cls, v: object) -> str:
        if v is None:
            return "unknown"
        if isinstance(v, str):
            t = v.strip()
            return t if t else "unknown"
        return str(v).strip() or "unknown"


class JobProfile(JobRecord):
    """A normalized job record plus enrichment fields."""

    soc_code: str | None = None
    naics_code: str | None = None
    employer: EmployerProfile = Field(default_factory=EmployerProfile)
