"""Build normalized dedup text for fuzzy near-duplicate detection (IMP-018)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

# CONTEXT.md: first 500 chars of requirements-rich body
_DEDUP_REQUIREMENTS_MAX_CHARS = 500

# Strip HTML-ish tags and collapse whitespace
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_boilerplate_noise(raw: str) -> str:
    """Light normalization: no PII; stable strings for hashing."""
    s = _TAG_RE.sub(" ", raw)
    s = _WS_RE.sub(" ", s).strip()
    return s


def build_dedup_text(
    job_title: str | None,
    company_name: str | None,
    requirements_or_description: str | None,
) -> str:
    """
    Concatenate title, company, truncated requirements/description (CONTEXT.md).

    Order: title | company | first N chars of body (after strip).
    """
    title = strip_boilerplate_noise((job_title or "").strip())
    company = strip_boilerplate_noise((company_name or "").strip())
    body = strip_boilerplate_noise((requirements_or_description or "").strip())[:_DEDUP_REQUIREMENTS_MAX_CHARS]
    parts = [p for p in (title, company, body) if p]
    return " | ".join(parts)


def dedup_text_hash(normalized_dedup_text: str) -> str:
    """SHA-256 hex digest of UTF-8 dedup string."""
    return hashlib.sha256(normalized_dedup_text.encode("utf-8")).hexdigest()


def row_requirements_fallback(row: dict[str, Any]) -> str:
    """Prefer normalized_jobs.requirements; fall back to job_description."""
    req = row.get("requirements")
    if isinstance(req, str) and req.strip():
        return req
    desc = row.get("job_description")
    return desc if isinstance(desc, str) else ""
