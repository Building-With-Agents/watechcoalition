"""Location text normalization and company_addresses lookup (enrichment)."""

from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.common.data_store.models import CompanyAddress

_NON_ALNUM_COMMA = re.compile(r"[^a-z0-9,\s]+")


def normalize_location_text(raw: str) -> str:
    """Lowercase, strip punctuation except commas, collapse whitespace."""
    s = raw.lower()
    s = _NON_ALNUM_COMMA.sub(" ", s)
    return " ".join(s.split()).strip()


def _borderplex_subregion(normalized: str) -> str | None:
    """Return Borderplex tag if ``normalized`` contains a known subregion phrase."""
    if "el paso" in normalized:
        return "el_paso"
    if "las cruces" in normalized:
        return "las_cruces"
    if "ciudad juarez" in normalized:
        return "ciudad_juarez"
    if "juarez" in normalized:
        return "ciudad_juarez"
    return None


def resolve_location(
    raw_location: str, session: Session
) -> tuple[int | None, float, str | None, str | None]:
    """
    Look up ``company_addresses`` by normalized location text.

    Returns ``(location_id, confidence, raw_text_for_storage, borderplex_subregion)``.
    ``raw_text_for_storage`` is set only when no row matches (for later resolution).
    """
    normalized = normalize_location_text(raw_location)
    borderplex = _borderplex_subregion(normalized)

    stmt = (
        select(CompanyAddress.id)
        .where(CompanyAddress.normalized_location == normalized)
        .limit(1)
    )
    location_id = session.execute(stmt).scalar_one_or_none()

    if location_id is not None:
        return (location_id, 0.90, None, borderplex)
    return (None, 0.0, raw_location, borderplex)
