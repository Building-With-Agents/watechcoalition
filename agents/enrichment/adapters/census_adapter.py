"""U.S. Census Bureau API adapter — regional demographics (Phase 1 stub).

Phase 2: use ``httpx`` against ``https://api.census.gov``; API key from
``os.getenv("CENSUS_API_KEY")`` when required by the endpoint — never hardcode credentials.
"""

from __future__ import annotations

import structlog

log = structlog.get_logger()


class CensusAdapter:
    """Fetches Census demographic and labor-force statistics by region identifier."""

    def get_regional_demographics(self, region: str) -> dict | None:
        """Return population / labor metrics for ``region`` (e.g. GEOID or label).

        Phase 1: mock data shaped like a real Census API response.
        Phase 2: replace stub with a live ``httpx`` call to ``api.census.gov`` (see module docstring).

        Returns ``None`` on any failure; never raises.
        """
        try:
            key = (region or "").strip()
            if not key:
                log.warning(
                    "census_adapter_get_regional_demographics_invalid_input",
                    reason="empty_region",
                )
                return None

            return {
                "region": key,
                "population": None,
                "labor_force": None,
                "unemployment_rate": None,
                "source": "census_stub",
            }
        except Exception as exc:  # noqa: BLE001 — contract: never raise to callers
            log.warning(
                "census_adapter_get_regional_demographics_failed",
                region=region,
                error=str(exc),
            )
            return None
