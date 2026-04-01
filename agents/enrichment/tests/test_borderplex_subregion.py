"""Unit tests for deterministic Borderplex subregion classification."""

from __future__ import annotations

import pytest

from agents.enrichment.classifiers.borderplex_subregion import classify_borderplex_subregion

_ALLOWED = frozenset({"el_paso", "las_cruces", "ciudad_juarez", "regional"})


def test_el_paso_positive() -> None:
    assert (
        classify_borderplex_subregion(
            city="El Paso",
            state_province="Texas",
            country="United States",
        )
        == "el_paso"
    )


def test_las_cruces_positive() -> None:
    assert (
        classify_borderplex_subregion(
            city="Las Cruces",
            state_province="New Mexico",
            country="United States",
        )
        == "las_cruces"
    )


def test_ciudad_juarez_positive() -> None:
    assert (
        classify_borderplex_subregion(
            city="Ciudad Juarez",
            state_province="Chihuahua",
            country="Mexico",
        )
        == "ciudad_juarez"
    )


def test_regional_missing_city_with_state_country() -> None:
    assert (
        classify_borderplex_subregion(
            city=None,
            state_province="Texas",
            country="United States",
        )
        == "regional"
    )


def test_regional_empty_city_with_state_country() -> None:
    assert (
        classify_borderplex_subregion(
            city="",
            state_province="Texas",
            country="United States",
        )
        == "regional"
    )


def test_regional_city_named_remote_not_a_metro() -> None:
    assert (
        classify_borderplex_subregion(
            city="Remote",
            state_province="Texas",
            country="United States",
        )
        == "regional"
    )


def test_regional_missing_city_mexico() -> None:
    assert (
        classify_borderplex_subregion(
            city=None,
            state_province="Chihuahua",
            country="Mexico",
        )
        == "regional"
    )


def test_regional_houston_texas() -> None:
    assert (
        classify_borderplex_subregion(
            city="Houston",
            state_province="Texas",
            country="United States",
        )
        == "regional"
    )


def test_regional_all_location_fields_none() -> None:
    assert (
        classify_borderplex_subregion(
            city=None,
            state_province=None,
            country=None,
        )
        == "regional"
    )


def test_normalization_casing_whitespace() -> None:
    assert (
        classify_borderplex_subregion(
            city="  EL PASO  ",
            state_province="tx",
            country="USA",
        )
        == "el_paso"
    )


def test_regional_cross_border_el_paso_texas_mexico_country() -> None:
    """US city/state with MX country is conflicting → conservative regional."""
    assert (
        classify_borderplex_subregion(
            city="El Paso",
            state_province="Texas",
            country="Mexico",
        )
        == "regional"
    )


@pytest.mark.parametrize(
    "city,state_province,country,is_remote,work_arrangement",
    [
        ("El Paso", "TX", None, None, None),
        ("Las Cruces", "NM", "us", False, None),
        ("Ciudad Juárez", None, "MX", None, None),
        (None, None, None, True, None),
        ("Austin", "TX", "United States", None, None),
        ("Juarez", "Chihuahua", None, None, None),
        ("El Paso", "NM", "United States", None, None),
        ("Las Cruces", "TX", "United States", None, None),
        (None, "TX", None, None, "Remote"),
    ],
)
def test_output_always_allowed_literal(
    city: str | None,
    state_province: str | None,
    country: str | None,
    is_remote: bool | None,
    work_arrangement: str | None,
) -> None:
    out = classify_borderplex_subregion(
        city=city,
        state_province=state_province,
        country=country,
        is_remote=is_remote,
        work_arrangement=work_arrangement,
    )
    assert out in _ALLOWED
