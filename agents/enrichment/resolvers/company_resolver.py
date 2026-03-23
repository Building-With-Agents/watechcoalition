"""Company name normalization helpers (Phase 2 resolvers — name matching utilities)."""

from __future__ import annotations

import re

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
