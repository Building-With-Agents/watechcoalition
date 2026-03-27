"""Location text normalization and Borderplex tagging (enrichment).

``company_addresses`` is not used (#110). The consolidated ORM for ``dbo.companies``
does not yet map city, state, or HQ location fields (same as ``origin/development``),
so there is no database row to resolve free-text ``raw_location`` against. When
those columns exist on ``companies``, extend :class:`~agents.common.data_store.models.Company`
and add a ``select`` on ``Company`` here.

Returns ``(location_id, confidence, raw_text_for_storage, borderplex_subregion)``.
``location_id`` is intended to align with ``job_postings`` location keys (UUID text)
when a match exists; it is ``None`` until HQ/geo fields are available for lookup.
"""

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
    raw_location: str,
    _session: Session,
) -> tuple[str | None, float, str | None, str | None]:
    """
    Derive Borderplex subregion from normalized location text.

    Does not query removed ``company_addresses`` or ``Company`` until geo columns
    are mapped on ``companies``.

    Returns ``(location_id, confidence, raw_text_for_storage, borderplex_subregion)``.
    """
    normalized = normalize_location_text(raw_location)
    borderplex = _borderplex_subregion(normalized)
    raw_keep = raw_location if raw_location.strip() else None
    return (None, 0.0, raw_keep, borderplex)
