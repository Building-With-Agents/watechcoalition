"""Deterministic Borderplex subregion labels from structured normalized-job location fields.

Maps ``(city, state_province, country)`` plus remote flags to exactly one of
``el_paso``, ``las_cruces``, ``ciudad_juarez``, or ``regional``. **Conservative
rule:** any ambiguity, omission, conflict, or remote work → ``regional``; a
specific subregion is returned only when city + state + country signals align
unambiguously with that metro (we do **not** infer from state or country alone).

Aligned with ``dbo.job_postings.borderplex_subregion`` (TEXT). No LLM.
"""

from __future__ import annotations

import unicodedata
from typing import Literal

_US_COUNTRY = frozenset(
    {
        "us",
        "usa",
        "u.s.",
        "u.s.a.",
        "united states",
        "united states of america",
    }
)
_MX_COUNTRY = frozenset({"mx", "mex", "mexico"})
_TX = frozenset({"tx", "texas"})
_NM = frozenset({"nm", "new mexico"})
_CHIHUAHUA = frozenset({"chihuahua", "chih", "chihuahua state"})

_REMOTE_ARRANGEMENT = frozenset(
    {
        "remote",
        "fully remote",
        "work from home",
        "wfh",
        "telecommute",
        "telecommuting",
    }
)


def _fold(text: str) -> str:
    """Trim, lowercase, strip combining accents, collapse internal whitespace."""
    raw = text.strip()
    if not raw:
        return ""
    decomposed = unicodedata.normalize("NFKD", raw)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(without_accents.lower().split())


def classify_borderplex_subregion(
    *,
    city: str | None,
    state_province: str | None,
    country: str | None,
    is_remote: bool | None = None,
    work_arrangement: str | None = None,
) -> Literal["el_paso", "las_cruces", "ciudad_juarez", "regional"]:
    if is_remote is True:
        return "regional"
    if work_arrangement is not None and _fold(work_arrangement) in _REMOTE_ARRANGEMENT:
        return "regional"

    city_n = _fold(city or "")
    if not city_n:
        return "regional"

    state_n = _fold(state_province or "")
    country_n = _fold(country or "")

    def _country_us_ok() -> bool:
        return not country_n or country_n in _US_COUNTRY

    def _country_mx_ok() -> bool:
        return country_n in _MX_COUNTRY

    # --- El Paso, TX (US) ---
    if city_n == "el paso":
        if not state_n or state_n not in _TX:
            return "regional"
        if not _country_us_ok():
            return "regional"
        if country_n and country_n in _MX_COUNTRY:
            return "regional"
        return "el_paso"

    # --- Las Cruces, NM (US) ---
    if city_n == "las cruces":
        if not state_n or state_n not in _NM:
            return "regional"
        if not _country_us_ok():
            return "regional"
        if country_n and country_n in _MX_COUNTRY:
            return "regional"
        return "las_cruces"

    # --- Ciudad Juárez (MX): full city name or lone "juarez" with MX / Chihuahua ---
    is_ciudad_juarez_name = city_n == "ciudad juarez"
    is_juarez_only = city_n == "juarez"

    if is_ciudad_juarez_name or is_juarez_only:
        if state_n in _TX or state_n in _NM:
            return "regional"
        if country_n in _US_COUNTRY:
            return "regional"
        if not (_country_mx_ok() or state_n in _CHIHUAHUA):
            return "regional"
        return "ciudad_juarez"

    return "regional"
