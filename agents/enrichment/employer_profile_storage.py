"""PostgreSQL upsert for ``dbo.employer_profiles`` (company-scoped enrichment)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

# Explicit timestamps: many deployed DBs (e.g. Azure) define ``created_at`` / ``updated_at``
# as NOT NULL without table defaults; omitting them caused NotNullViolation on INSERT.
_UPSERT_EMPLOYER_PROFILE_SQL = text(
    """
    INSERT INTO dbo.employer_profiles (
        id,
        company_id,
        company_size,
        ai_maturity_signal,
        sector,
        is_known_employer,
        created_at,
        updated_at
    ) VALUES (
        gen_random_uuid(),
        :company_id,
        :company_size,
        :ai_maturity_signal,
        :sector,
        :is_known_employer,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (company_id) DO UPDATE SET
        company_size = EXCLUDED.company_size,
        ai_maturity_signal = EXCLUDED.ai_maturity_signal,
        sector = EXCLUDED.sector,
        is_known_employer = EXCLUDED.is_known_employer,
        updated_at = CURRENT_TIMESTAMP
    RETURNING id
    """
)


def _str_or_unknown(v: object, *, max_len: int) -> str:
    if v is None:
        return "unknown"
    s = str(v).strip() if not isinstance(v, str) else v.strip()
    if not s:
        return "unknown"
    return s[:max_len]


def _sector_for_db(v: object) -> str | None:
    if v is None:
        return None
    if isinstance(v, str):
        t = v.strip()
        return t if t else None
    s = str(v).strip()
    return s if s else None


def upsert_employer_profile_by_company_id(
    session: Session,
    company_id: str,
    employer_metadata: dict[str, Any],
) -> uuid.UUID:
    """Insert or update one row keyed by ``company_id``; return primary key."""
    cid = str(company_id).strip()
    if not cid:
        raise ValueError("company_id must be non-empty")

    raw_known = employer_metadata.get("is_known_employer")
    is_known = bool(raw_known) if raw_known is not None else False

    params = {
        "company_id": cid,
        "company_size": _str_or_unknown(employer_metadata.get("company_size"), max_len=20),
        "ai_maturity_signal": _str_or_unknown(employer_metadata.get("ai_maturity_signal"), max_len=20),
        "sector": _sector_for_db(employer_metadata.get("sector")),
        "is_known_employer": is_known,
    }
    row = session.execute(_UPSERT_EMPLOYER_PROFILE_SQL, params).scalar_one()
    return row if isinstance(row, uuid.UUID) else uuid.UUID(str(row))
