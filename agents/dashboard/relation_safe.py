"""Soft-fail reads when PostgreSQL relations are missing (partial DB snapshots)."""

from __future__ import annotations

from typing import Any

import pandas as pd


def is_undefined_relation_error(exc: BaseException) -> bool:
    """True for typical Postgres/SQLAlchemy \"relation does not exist\" failures."""
    msg = str(exc).lower()
    if "does not exist" not in msg:
        return False
    return "relation" in msg or "table" in msg


def read_sql_relation_safe(
    query: str,
    engine: Any,
    *,
    params: dict[str, Any] | None = None,
    user_hint: str | None = None,
) -> tuple[pd.DataFrame, str | None]:
    """Run ``pd.read_sql``; on missing-relation errors return an empty frame and a hint.

    Other exceptions are re-raised so real connectivity/SQL bugs still surface.
    """
    try:
        df = (
            pd.read_sql(query, engine, params=params)
            if params is not None
            else pd.read_sql(query, engine)
        )
        return df, None
    except Exception as exc:
        if is_undefined_relation_error(exc):
            hint = user_hint or (
                "A required table is missing in this database (migrations not applied or a partial snapshot)."
            )
            return pd.DataFrame(), hint
        raise
