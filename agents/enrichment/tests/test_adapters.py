"""Tests for Week 6 external data adapter mocks."""

from __future__ import annotations

import asyncio

from agents.enrichment.adapters import (
    MockBLSAdapter,
    MockCensusAdapter,
    MockONETAdapter,
)


def test_mock_bls_known_soc_el_paso_median() -> None:
    async def _run() -> None:
        a = MockBLSAdapter()
        w = await a.get_wage_data("15-1252.00", "el_paso")
        assert w is not None
        assert w.soc_code == "15-1252"
        assert w.median_wage == 95340.0
        assert w.percentile_25 < w.median_wage < w.percentile_75
        assert w.source == "mock"

    asyncio.run(_run())


def test_mock_bls_unknown_soc_returns_none() -> None:
    async def _run() -> None:
        a = MockBLSAdapter()
        assert await a.get_wage_data("99-9999", "el_paso") is None

    asyncio.run(_run())


def test_mock_bls_empty_soc_returns_none() -> None:
    async def _run() -> None:
        a = MockBLSAdapter()
        assert await a.get_wage_data("", "tx") is None

    asyncio.run(_run())


def test_mock_onet_occupation_details() -> None:
    async def _run() -> None:
        a = MockONETAdapter()
        p = await a.get_occupation_details("15-1252")
        assert p is not None
        assert "Software" in p.title
        assert len(p.tasks) >= 1
        assert p.source == "mock"

    asyncio.run(_run())


def test_mock_onet_crosswalk_software_developer() -> None:
    async def _run() -> None:
        a = MockONETAdapter()
        matches = await a.get_soc_crosswalk("Senior Software Developer")
        assert len(matches) >= 1
        assert matches[0].soc_code == "15-1252"
        assert matches[0].confidence_score > 0.5

    asyncio.run(_run())


def test_mock_census_borderplex() -> None:
    async def _run() -> None:
        a = MockCensusAdapter()
        r = await a.get_regional_demographics("el_paso")
        assert r is not None
        assert r.population > 0
        assert r.median_household_income > 0
        assert 0 <= r.education_bachelors_or_higher_pct <= 100

    asyncio.run(_run())


def test_mock_census_empty_region_none() -> None:
    async def _run() -> None:
        a = MockCensusAdapter()
        assert await a.get_regional_demographics("") is None

    asyncio.run(_run())
