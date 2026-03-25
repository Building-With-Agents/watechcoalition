"""Location text normalization and Borderplex tagging (enrichment)."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

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
    raw_location: str, _session: Session
) -> tuple[None, float, str | None, str | None]:
    """
    Normalize location text and detect Borderplex subregion.

    Does not query the database; ``location_id`` is not resolved in Phase 1.

    Returns ``(location_id, confidence, raw_text_for_storage, borderplex_subregion)``.
    ``location_id`` is always ``None``; ``raw_text_for_storage`` is the original
    ``raw_location`` for persistence on ``job_postings``.
    """
    normalized = normalize_location_text(raw_location)
    borderplex = _borderplex_subregion(normalized)
    return (None, 0.0, raw_location, borderplex)
