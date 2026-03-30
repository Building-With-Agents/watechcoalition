"""Tests for sector_resolver."""

from __future__ import annotations

from unittest.mock import MagicMock

from agents.enrichment.resolvers.sector_resolver import resolve_sector


def test_software_engineering_returns_sector_when_row_exists() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = 101
    session.execute.return_value = exec_result

    assert resolve_sector("Software Engineering", session) == 101
    session.execute.assert_called_once()


def test_machine_learning_returns_sector_when_row_exists() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = 202
    session.execute.return_value = exec_result

    assert resolve_sector("Machine Learning", session) == 202


def test_unknown_role_returns_none() -> None:
    session = MagicMock()
    assert resolve_sector("Product Management", session) is None
    session.execute.assert_not_called()


def test_none_role_returns_none() -> None:
    session = MagicMock()
    assert resolve_sector(None, session) is None
    session.execute.assert_not_called()


def test_known_role_sector_missing_in_table_returns_none() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    session.execute.return_value = exec_result

    assert resolve_sector("Software Engineering", session) is None
