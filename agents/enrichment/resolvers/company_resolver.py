"""Company name normalization helpers (Phase 2 resolvers — name matching utilities)."""

from __future__ import annotations

import re

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
    r"(?:,\s*|\s+)("
    + "|".join(re.escape(s) for s in _LEGAL_SUFFIXES)
    + r")\.?$",
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


def lookup_company_exact(normalized_name: str, session: Session) -> int | None:
    """Return ``companies.id`` for an exact ``normalized_name`` match, else ``None``."""
    stmt = select(Company.id).where(Company.normalized_name == normalized_name).limit(1)
    return session.execute(stmt).scalar_one_or_none()


def find_best_fuzzy_match(
    normalized_name: str, session: Session
) -> tuple[int, float] | tuple[None, float]:
    """
    Load all companies and return the best weighted fuzzy match at or above
    ``FUZZY_THRESHOLD``, else ``(None, best_score)``.
    """
    rows = session.execute(select(Company.id, Company.normalized_name)).all()
    if not rows:
        return (None, 0.0)

    best_id: int | None = None
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


def create_placeholder_company(raw_name: str, normalized_name: str, session: Session) -> int:
    """Insert a placeholder company row; flush only — caller must commit."""
    company = Company(
        normalized_name=normalized_name,
        raw_name=raw_name,
        is_placeholder=True,
    )
    session.add(company)
    session.flush()
    return company.id
