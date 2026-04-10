"""Map role classification strings to industry_sectors rows."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from agents.common.data_store.models import IndustrySector

ROLE_TO_SECTOR: dict[str, str] = {
    "Software Engineering": "Information Technology",
    "Data Engineering": "Information Technology",
    "Machine Learning": "Information Technology",
    "Data Science": "Information Technology",
    "Data Analytics": "Information Technology",
    "DevOps": "Information Technology",
    "ML Platform": "Information Technology",
}

_FALLBACK_SECTOR_TITLE = "Other"


def _resolve_sector_by_title(session: Any, title: str) -> str | None:
    stmt = select(IndustrySector.industry_sector_id).where(IndustrySector.sector_title == title).limit(1)
    return session.execute(stmt).scalar_one_or_none()


def resolve_sector(role_classification: str | None, session: Any) -> str | None:
    """
    Return ``industry_sectors.industry_sector_id`` for the mapped sector name, if present in DB.

    Falls back to the ``Other`` sector id when the role is unmapped or the primary sector title
    is not found in the DB. Returns ``None`` only when ``session`` is ``None`` or both lookups
    miss.

    ``session`` may be ``None`` (no DB yet); returns ``None`` without querying.
    """
    if session is None:
        return None

    sector_title: str | None = ROLE_TO_SECTOR.get(role_classification or "")
    if sector_title is not None:
        result = _resolve_sector_by_title(session, sector_title)
        if result is not None:
            return result

    return _resolve_sector_by_title(session, _FALLBACK_SECTOR_TITLE)
