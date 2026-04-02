"""Location resolution against ``dbo.companies`` (#110).

``company_addresses`` is not used. Location is matched using optional HQ fields on
:class:`~agents.common.data_store.models.Company`:

1. **normalized_location** — compared to :func:`normalize_location_text` of the job
   string using case-insensitive trimmed equality (``lower(trim(column))`` vs
   normalized input).
2. **city + state** — if no ``normalized_location`` row matches, rows with both
   ``city`` and ``state`` set are scanned; we compare
   ``normalize_location_text(f"{city}, {state}")`` to the input normalization.

On match, returns ``company_id`` (text UUID) as ``location_id`` — the same stable
key used elsewhere for company resolution until a dedicated location entity exists.

Borderplex subregion is still derived only from normalized free text (no DB).
"""

from __future__ import annotations

import re

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from agents.common.data_store.models import Company

_NON_ALNUM_COMMA = re.compile(r"[^a-z0-9,\s]+")

# Confidence when ``normalized_location`` column matches
_CONF_NORMALIZED_LOCATION = 0.90
# Confidence when ``city`` + ``state`` composite matches
_CONF_CITY_STATE = 0.82


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
    session: Session,
) -> tuple[str | None, float, str | None, str | None]:
    """
    Match ``raw_location`` to ``Company`` HQ fields; derive Borderplex from text.

    Returns ``(location_id, confidence, raw_text_for_storage, borderplex_subregion)``.
    ``location_id`` is ``companies.company_id`` when a row matches, else ``None``.
    """
    normalized = normalize_location_text(raw_location)
    borderplex = _borderplex_subregion(normalized)
    raw_keep = raw_location if raw_location.strip() else None

    if not normalized:
        return (None, 0.0, raw_keep, borderplex)

    stmt_norm = (
        select(Company.company_id)
        .where(Company.normalized_location.isnot(None))
        .where(func.lower(func.trim(Company.normalized_location)) == normalized)
        .limit(1)
    )
    cid = session.execute(stmt_norm).scalar_one_or_none()
    if cid is not None:
        return (str(cid), _CONF_NORMALIZED_LOCATION, raw_keep, borderplex)

    stmt_geo = select(Company.company_id, Company.city, Company.state).where(
        and_(Company.city.isnot(None), Company.state.isnot(None))
    )
    for row in session.execute(stmt_geo):
        company_id, city, state = row[0], row[1], row[2]
        if city is None or state is None:
            continue
        if normalize_location_text(f"{city}, {state}") == normalized:
            return (str(company_id), _CONF_CITY_STATE, raw_keep, borderplex)

    return (None, 0.0, raw_keep, borderplex)
