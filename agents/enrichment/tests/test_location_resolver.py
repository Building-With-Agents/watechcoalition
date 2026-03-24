"""Tests for location resolution."""

from __future__ import annotations

from unittest.mock import MagicMock

from agents.enrichment.resolvers.location_resolver import resolve_location


def test_resolve_location_known_match_returns_confidence_and_no_raw() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = 42
    session.execute.return_value = exec_result

    loc_id, conf, raw_keep, borderplex = resolve_location("Seattle, WA", session)

    assert (loc_id, conf, raw_keep, borderplex) == (42, 0.90, None, None)


def test_resolve_location_unknown_returns_raw_text() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    session.execute.return_value = exec_result

    raw = "Portland, OR"
    loc_id, conf, raw_keep, borderplex = resolve_location(raw, session)

    assert (loc_id, conf, raw_keep, borderplex) == (None, 0.0, raw, None)


def test_resolve_location_el_paso_borderplex() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    session.execute.return_value = exec_result

    raw = "El Paso, TX"
    loc_id, conf, raw_keep, borderplex = resolve_location(raw, session)

    assert borderplex == "el_paso"
    assert loc_id is None
    assert conf == 0.0
    assert raw_keep == raw


def test_resolve_location_las_cruces_borderplex() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    session.execute.return_value = exec_result

    raw = "Las Cruces, NM"
    _, _, _, borderplex = resolve_location(raw, session)

    assert borderplex == "las_cruces"


def test_resolve_location_ciudad_juarez_borderplex() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    session.execute.return_value = exec_result

    raw = "Ciudad Juarez"
    _, _, _, borderplex = resolve_location(raw, session)

    assert borderplex == "ciudad_juarez"


def test_resolve_location_austin_no_borderplex() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    session.execute.return_value = exec_result

    raw = "Austin, TX"
    _, _, _, borderplex = resolve_location(raw, session)

    assert borderplex is None
