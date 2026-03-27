"""Tests for location resolution (Company select, #110)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.enrichment.resolvers.location_resolver import (
    normalize_location_text,
    resolve_location,
)


def _session_no_match() -> MagicMock:
    """Session mock: no normalized_location row; no city/state rows."""
    session = MagicMock()
    r1 = MagicMock()
    r1.scalar_one_or_none.return_value = None
    r2 = MagicMock()
    r2.__iter__ = lambda self: iter(())
    session.execute.side_effect = [r1, r2]
    return session


def test_normalize_location_text_strips_noise() -> None:
    assert normalize_location_text("  Seattle,  WA!!!  ") == "seattle, wa"


def test_resolve_location_no_db_match_returns_raw_and_zero_confidence() -> None:
    session = _session_no_match()

    loc_id, conf, raw_keep, borderplex = resolve_location("Seattle, WA", session)

    assert (loc_id, conf, borderplex) == (None, 0.0, None)
    assert raw_keep == "Seattle, WA"
    assert session.execute.call_count == 2


def test_resolve_location_unknown_returns_raw_text() -> None:
    session = _session_no_match()

    raw = "Portland, OR"
    loc_id, conf, raw_keep, borderplex = resolve_location(raw, session)

    assert (loc_id, conf, raw_keep, borderplex) == (None, 0.0, raw, None)


def test_resolve_location_el_paso_borderplex() -> None:
    session = _session_no_match()

    raw = "El Paso, TX"
    loc_id, conf, raw_keep, borderplex = resolve_location(raw, session)

    assert borderplex == "el_paso"
    assert loc_id is None
    assert conf == 0.0
    assert raw_keep == raw


def test_resolve_location_las_cruces_borderplex() -> None:
    session = _session_no_match()

    raw = "Las Cruces, NM"
    _, _, _, borderplex = resolve_location(raw, session)

    assert borderplex == "las_cruces"


def test_resolve_location_ciudad_juarez_borderplex() -> None:
    session = _session_no_match()

    raw = "Ciudad Juarez"
    _, _, _, borderplex = resolve_location(raw, session)

    assert borderplex == "ciudad_juarez"


def test_resolve_location_austin_no_borderplex() -> None:
    session = _session_no_match()

    raw = "Austin, TX"
    _, _, _, borderplex = resolve_location(raw, session)

    assert borderplex is None


def test_resolve_location_match_on_normalized_location_column() -> None:
    session = MagicMock()
    r1 = MagicMock()
    r1.scalar_one_or_none.return_value = "550e8400-e29b-41d4-a716-446655440099"
    session.execute.side_effect = [r1]

    loc_id, conf, raw_keep, borderplex = resolve_location("Seattle, WA", session)

    assert loc_id == "550e8400-e29b-41d4-a716-446655440099"
    assert conf == pytest.approx(0.90)
    assert raw_keep == "Seattle, WA"
    assert borderplex is None
    session.execute.assert_called_once()


def test_resolve_location_match_on_city_state_composite() -> None:
    session = MagicMock()
    r1 = MagicMock()
    r1.scalar_one_or_none.return_value = None
    r2 = MagicMock()
    r2.__iter__ = lambda self: iter(
        (("aaaaaaaa-bbbb-cccc-dddd-eeeeeeee0001", "Seattle", "WA"),)
    )
    session.execute.side_effect = [r1, r2]

    loc_id, conf, raw_keep, borderplex = resolve_location("Seattle, WA", session)

    assert loc_id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeee0001"
    assert conf == pytest.approx(0.82)
    assert raw_keep == "Seattle, WA"
    assert session.execute.call_count == 2


def test_resolve_location_empty_string_no_queries() -> None:
    session = MagicMock()
    loc_id, conf, raw_keep, borderplex = resolve_location("   ", session)
    assert (loc_id, conf) == (None, 0.0)
    assert raw_keep is None
    session.execute.assert_not_called()
