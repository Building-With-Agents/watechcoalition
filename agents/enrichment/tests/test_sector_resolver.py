"""Tests for sector_resolver."""

from __future__ import annotations

from unittest.mock import MagicMock, call

from agents.enrichment.resolvers.sector_resolver import (
    ROLE_TO_SECTOR,
    resolve_sector,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _session_returning(value: object) -> MagicMock:
    """Return a mock session whose execute().scalar_one_or_none() yields *value*."""
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = value
    session.execute.return_value = exec_result
    return session


def _session_returning_sequence(*values: object) -> MagicMock:
    """Return a mock session whose successive execute() calls return *values*."""
    session = MagicMock()
    side_effects = []
    for v in values:
        r = MagicMock()
        r.scalar_one_or_none.return_value = v
        side_effects.append(r)
    session.execute.side_effect = side_effects
    return session


# ---------------------------------------------------------------------------
# Mapping: known roles must resolve via "Information Technology"
# ---------------------------------------------------------------------------


def test_software_engineering_maps_to_information_technology() -> None:
    """Primary lookup must query 'Information Technology', not 'technology'."""
    assert ROLE_TO_SECTOR["Software Engineering"] == "Information Technology"


def test_all_mapped_roles_use_information_technology() -> None:
    for role, sector in ROLE_TO_SECTOR.items():
        assert sector == "Information Technology", (
            f"Role '{role}' maps to '{sector}' — expected 'Information Technology'"
        )


def test_software_engineering_returns_sector_when_row_exists() -> None:
    session = _session_returning(101)
    assert resolve_sector("Software Engineering", session) == 101
    session.execute.assert_called_once()


def test_machine_learning_returns_sector_when_row_exists() -> None:
    session = _session_returning(202)
    assert resolve_sector("Machine Learning", session) == 202


# ---------------------------------------------------------------------------
# Fallback: unknown role → "Other" sector
# ---------------------------------------------------------------------------


def test_unknown_role_falls_back_to_other_sector() -> None:
    """An unmapped role must skip the primary lookup and query 'Other' instead."""
    other_id = "sector-uuid-other"
    session = _session_returning(other_id)

    result = resolve_sector("Product Management", session)

    assert result == other_id
    # Only one execute call: straight to the "Other" fallback
    session.execute.assert_called_once()


def test_none_role_falls_back_to_other_sector() -> None:
    other_id = "sector-uuid-other"
    session = _session_returning(other_id)

    result = resolve_sector(None, session)

    assert result == other_id
    session.execute.assert_called_once()


def test_known_role_sector_missing_in_table_falls_back_to_other() -> None:
    """When the primary lookup finds nothing, resolve_sector must try 'Other'."""
    other_id = "sector-uuid-other"
    session = _session_returning_sequence(None, other_id)

    result = resolve_sector("Software Engineering", session)

    assert result == other_id
    assert session.execute.call_count == 2


def test_fallback_returns_none_when_other_not_in_table() -> None:
    """If 'Other' sector is also absent from the DB, return None."""
    session = _session_returning_sequence(None, None)

    result = resolve_sector("Software Engineering", session)

    assert result is None
    assert session.execute.call_count == 2


def test_unknown_role_returns_none_when_other_not_in_table() -> None:
    other_missing = _session_returning(None)

    result = resolve_sector("Product Management", other_missing)

    assert result is None
    other_missing.execute.assert_called_once()


# ---------------------------------------------------------------------------
# Session-None guard
# ---------------------------------------------------------------------------


def test_none_session_returns_none_without_querying() -> None:
    assert resolve_sector("Software Engineering", None) is None
