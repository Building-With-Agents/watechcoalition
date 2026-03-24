"""Map role classification strings to industry_sectors rows."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from agents.common.data_store.models import IndustrySector

ROLE_TO_SECTOR: dict[str, str] = {
    "Software Engineering": "technology",
    "Data Engineering": "technology",
    "Machine Learning": "technology",
    "Data Science": "technology",
    "Data Analytics": "technology",
    "DevOps": "technology",
    "ML Platform": "technology",
}


def _normalize_sector_token(value: str) -> str:
    return " ".join(value.lower().split()).strip()


def resolve_sector(role_classification: str | None, session: Any) -> str | None:
    """
    Return ``industry_sectors.industry_sector_id`` for the mapped sector name, if present in DB.

    ``session`` may be ``None`` (no DB yet); returns ``None`` without querying.
    """
    if session is None:
        return None
    if not role_classification:
        return None
    if role_classification not in ROLE_TO_SECTOR:
        return None

    sector_name = _normalize_sector_token(ROLE_TO_SECTOR[role_classification])
    stmt = (
        select(IndustrySector.industry_sector_id)
        .where(IndustrySector.sector_title == sector_name)
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()
