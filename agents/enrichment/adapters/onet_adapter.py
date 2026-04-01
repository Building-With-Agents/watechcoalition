"""O*NET Web Services adapter — occupation details (Phase 1 mock).

Phase 2: use ``httpx`` against ``https://services.onetcenter.org`` with credentials from
``os.getenv("ONET_CLIENT_ID")`` / ``os.getenv("ONET_API_KEY")`` — never hardcode secrets.
"""

from __future__ import annotations

import asyncio
import re

import structlog

from agents.enrichment.adapters.base import AbstractONETAdapter
from agents.enrichment.adapters.models import OccupationProfile, SOCMatch

log = structlog.get_logger()

_ONET_BY_SOC: dict[str, OccupationProfile] = {
    "15-1252": OccupationProfile(
        soc_code="15-1252",
        title="Software Developers",
        description=(
            "Research, design, and develop computer and network software or specialized utilities. "
            "Analyze user needs and develop software solutions, applying principles of computer science "
            "and engineering."
        ),
        tasks=[
            "Analyze user needs and software requirements",
            "Design or customize applications for client use",
            "Modify existing software to correct errors or improve performance",
        ],
        skills=[
            "Programming",
            "Critical Thinking",
            "Complex Problem Solving",
            "Systems Analysis",
        ],
        education="Bachelor's degree typical",
        source="mock",
    ),
    "15-1211": OccupationProfile(
        soc_code="15-1211",
        title="Computer Systems Analysts",
        description=(
            "Analyze science, engineering, business, and other data processing problems "
            "to implement and improve computer systems."
        ),
        tasks=[
            "Expand or modify system capabilities",
            "Test and troubleshoot programs",
            "Consult with management on system requirements",
        ],
        skills=["Systems Analysis", "Reading Comprehension", "Active Listening"],
        education="Bachelor's degree typical",
        source="mock",
    ),
    "15-1299": OccupationProfile(
        soc_code="15-1299",
        title="Computer Occupations, All Other",
        description="All computer occupations not listed separately.",
        tasks=["Perform specialized computing tasks as assigned"],
        skills=["Computers and Electronics", "Problem Solving"],
        education="Varies",
        source="mock",
    ),
}


def _normalize_soc(soc_code: str) -> str:
    """Strip O*NET-style SOC decimals before lookup (e.g. ``15-1252.00`` → ``15-1252``).

    Canonical convention: `.cursor/rules/integration-schema.mdc` § SOC / O*NET normalization.
    Matches BLS adapter normalization in `bls_adapter._normalize_soc`.
    """
    s = (soc_code or "").strip()
    if not s:
        return ""
    return s.split(".")[0].strip()


_TITLE_KEYWORDS: list[tuple[re.Pattern[str], list[SOCMatch]]] = [
    (
        re.compile(r"software|developer|engineer.*dev", re.I),
        [
            SOCMatch(soc_code="15-1252", title="Software Developers", confidence_score=0.92),
            SOCMatch(
                soc_code="15-1256", title="Software Quality Assurance Analysts and Testers", confidence_score=0.55
            ),
        ],
    ),
    (
        re.compile(r"analyst|systems analyst", re.I),
        [
            SOCMatch(soc_code="15-1211", title="Computer Systems Analysts", confidence_score=0.88),
            SOCMatch(soc_code="15-1252", title="Software Developers", confidence_score=0.45),
        ],
    ),
    (
        re.compile(r"data\s+engineer|data scientist", re.I),
        [
            SOCMatch(soc_code="15-2051", title="Data Scientists", confidence_score=0.78),
            SOCMatch(soc_code="15-1252", title="Software Developers", confidence_score=0.62),
        ],
    ),
]


class MockONETAdapter(AbstractONETAdapter):
    """Phase 1 mock O*NET data; implements :class:`AbstractONETAdapter`."""

    async def get_occupation_details(self, soc_code: str) -> OccupationProfile | None:
        await asyncio.sleep(0)
        try:
            code = _normalize_soc(soc_code)
            if not code:
                log.warning(
                    "onet_adapter_get_occupation_invalid_input",
                    reason="empty_soc_code",
                )
                return None
            profile = _ONET_BY_SOC.get(code)
            if profile is None:
                log.info("onet_adapter_unknown_soc", soc_code=code)
                return None
            return profile.model_copy()
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "onet_adapter_get_occupation_failed",
                soc_code=soc_code,
                error=str(exc),
            )
            return None

    async def get_soc_crosswalk(self, title: str) -> list[SOCMatch]:
        await asyncio.sleep(0)
        try:
            t = (title or "").strip()
            if not t:
                return []
            for pattern, matches in _TITLE_KEYWORDS:
                if pattern.search(t):
                    return [m.model_copy() for m in matches]
            return [
                SOCMatch(soc_code="15-1299", title="Computer Occupations, All Other", confidence_score=0.35),
            ]
        except Exception as exc:  # noqa: BLE001
            log.warning("onet_adapter_crosswalk_failed", title=title, error=str(exc))
            return []


ONETAdapter = MockONETAdapter
