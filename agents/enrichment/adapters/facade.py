"""Facade over BLS / O*NET / Census adapters — single injection point for EnrichmentAgent.

Phase 1 calls async adapters from sync code via ``run_coroutine`` (new event loop per call
when needed). Phase 2 should optimize throughput; see integration-schema Cursor rule.
"""

from __future__ import annotations

from typing import Any

from agents.enrichment.adapters.base import AbstractBLSAdapter, AbstractCensusAdapter, AbstractONETAdapter
from agents.enrichment.adapters.bls_adapter import MockBLSAdapter
from agents.enrichment.adapters.census_adapter import MockCensusAdapter
from agents.enrichment.adapters.onet_adapter import MockONETAdapter


class ExternalEnrichmentFacade:
    """Fetches external reference data for one posting using stable adapter interfaces."""

    def __init__(
        self,
        bls: AbstractBLSAdapter | None = None,
        onet: AbstractONETAdapter | None = None,
        census: AbstractCensusAdapter | None = None,
    ) -> None:
        self._bls = bls or MockBLSAdapter()
        self._onet = onet or MockONETAdapter()
        self._census = census or MockCensusAdapter()

    async def fetch_for_posting(self, posting: dict[str, Any]) -> dict[str, Any]:
        """Return dict with optional keys ``wage_estimate``, ``occupation_profile``, ``regional_profile`` (JSON-ready)."""
        soc = str(posting.get("soc_code") or "").strip()
        title = str(posting.get("title") or "").strip()
        region_hint = posting.get("borderplex_subregion") or posting.get("location") or "borderplex"
        region_str = str(region_hint).strip() or "borderplex"

        wage = await self._bls.get_wage_data(soc, region_str)
        occupation = await self._onet.get_occupation_details(soc) if soc else None
        if occupation is None and title:
            cross = await self._onet.get_soc_crosswalk(title)
            if cross:
                top = max(cross, key=lambda m: m.confidence_score)
                occupation = await self._onet.get_occupation_details(top.soc_code)

        census_region = str(posting.get("borderplex_subregion") or "borderplex").strip() or "borderplex"
        regional = await self._census.get_regional_demographics(census_region)

        out: dict[str, Any] = {}
        if wage is not None:
            out["wage_estimate"] = wage.model_dump()
        if occupation is not None:
            out["occupation_profile"] = occupation.model_dump()
        if regional is not None:
            out["regional_profile"] = regional.model_dump()
        return out
