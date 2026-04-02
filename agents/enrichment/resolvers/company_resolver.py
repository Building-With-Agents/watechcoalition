"""Company name normalization and resolution (#95).

Phase 2 name-matching utilities; implementation lives here (not
``agents/enrichment/resolution.py`` from the issue text).
"""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session
from thefuzz import fuzz

from agents.common.data_store.models import Company

FUZZY_THRESHOLD = 85

# Longest first so e.g. "corporation" wins over "corp", "llp" over "lp".
_LEGAL_SUFFIXES: tuple[str, ...] = (
    "corporation",
    "incorporated",
    "limited",
    "llc",
    "llp",
    "corp",
    "inc",
    "ltd",
    "lp",
    "co",
)

_SUFFIX_TAIL = re.compile(
    r"(?:,\s*|\s+)(" + "|".join(re.escape(s) for s in _LEGAL_SUFFIXES) + r")\.?$",
    re.IGNORECASE,
)


def normalize_company_name(raw: str) -> str:
    """Lowercase, collapse whitespace, strip common legal entity suffixes from the end."""
    s = " ".join(raw.lower().split())
    while True:
        m = _SUFFIX_TAIL.search(s)
        if not m or m.end() != len(s):
            break
        s = s[: m.start()].rstrip(" ,")
    return s.strip()


def lookup_company_exact(normalized_name: str, session: Session) -> str | None:
    """Return ``companies.company_id`` when ``normalize_company_name(company_name)`` matches."""
    for company_id, company_name in session.execute(select(Company.company_id, Company.company_name)).all():
        if normalize_company_name(company_name) == normalized_name:
            return company_id
    return None


def find_best_fuzzy_match(normalized_name: str, session: Session) -> tuple[str, float] | tuple[None, float]:
    """
    Load all companies and return the best weighted fuzzy match at or above
    ``FUZZY_THRESHOLD``, else ``(None, best_score)``.
    """
    rows = session.execute(select(Company.company_id, Company.company_name)).all()
    if not rows:
        return (None, 0.0)

    best_id: str | None = None
    best_score = -1.0
    for company_id, candidate in rows:
        score = (fuzz.token_sort_ratio(normalized_name, candidate) * 0.6) + (
            fuzz.partial_ratio(normalized_name, candidate) * 0.4
        )
        if score > best_score:
            best_score = score
            best_id = company_id

    if best_score >= FUZZY_THRESHOLD:
        return (best_id, best_score)
    return (None, best_score)


def create_placeholder_company(raw_name: str, _normalized_name: str, session: Session) -> str:
    """Insert a placeholder company row; flush only — caller must commit."""
    company = Company(
        company_id=str(uuid.uuid4()),
        company_name=raw_name,
    )
    session.add(company)
    session.flush()
    return company.company_id


def resolve_company(raw_name: str, session: Session) -> tuple[str, float]:
    """
    Resolve ``raw_name`` to a company id and a confidence score for ``field_confidence``.

    Order: exact normalized match → fuzzy match (above threshold) → placeholder.
    """
    normalized = normalize_company_name(raw_name)
    exact_id = lookup_company_exact(normalized, session)
    if exact_id is not None:
        return (exact_id, 0.95)
    fuzzy_id, fuzzy_score = find_best_fuzzy_match(normalized, session)
    if fuzzy_id is not None:
        return (fuzzy_id, fuzzy_score / 100.0)
    placeholder_id = create_placeholder_company(raw_name, normalized, session)
    return (placeholder_id, 0.40)
