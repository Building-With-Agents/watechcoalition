"""Tests for location resolution."""

from __future__ import annotations

from unittest.mock import MagicMock

from agents.enrichment.resolvers.location_resolver import resolve_location


def test_resolve_location_no_db_match_returns_raw_and_zero_confidence() -> None:
    """Consolidated schema: no company_addresses; Company has no geo ORM fields yet (#110)."""
    session = MagicMock()

    loc_id, conf, raw_keep, borderplex = resolve_location("Seattle, WA", session)

    assert (loc_id, conf, borderplex) == (None, 0.0, None)
    assert raw_keep == "Seattle, WA"
    session.execute.assert_not_called()


def test_resolve_location_unknown_returns_raw_text() -> None:
    session = MagicMock()

    raw = "Portland, OR"
    loc_id, conf, raw_keep, borderplex = resolve_location(raw, session)

    assert (loc_id, conf, raw_keep, borderplex) == (None, 0.0, raw, None)
    session.execute.assert_not_called()


def test_resolve_location_el_paso_borderplex() -> None:
    session = MagicMock()

    raw = "El Paso, TX"
    loc_id, conf, raw_keep, borderplex = resolve_location(raw, session)

    assert borderplex == "el_paso"
    assert loc_id is None
    assert conf == 0.0
    assert raw_keep == raw


def test_resolve_location_las_cruces_borderplex() -> None:
    session = MagicMock()

    raw = "Las Cruces, NM"
    _, _, _, borderplex = resolve_location(raw, session)

    assert borderplex == "las_cruces"


def test_resolve_location_ciudad_juarez_borderplex() -> None:
    session = MagicMock()

    raw = "Ciudad Juarez"
    _, _, _, borderplex = resolve_location(raw, session)

    assert borderplex == "ciudad_juarez"


def test_resolve_location_austin_no_borderplex() -> None:
    session = MagicMock()

    raw = "Austin, TX"
    _, _, _, borderplex = resolve_location(raw, session)

    assert borderplex is None
