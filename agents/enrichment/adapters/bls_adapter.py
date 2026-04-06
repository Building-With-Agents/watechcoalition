"""Bureau of Labor Statistics adapter — OEWS-style wage data (Phase 1 mock).

Phase 2: use ``httpx`` against ``https://api.bls.gov`` with any API key from
``os.getenv("BLS_API_KEY")`` or documented BLS public endpoints — never hardcode credentials.

Unknown SOC codes return ``None`` (documented contract). El Paso MSA–style medians from OEWS
for selected SOCs (runbook table).
"""

from __future__ import annotations

import asyncio

import structlog

from agents.enrichment.adapters.base import AbstractBLSAdapter
from agents.enrichment.adapters.models import WageEstimate

log = structlog.get_logger()

# El Paso–style annual wages (USD), runbook Week 6 — plausible p25/p75 spreads.
_OEWS_KNOWN: dict[str, tuple[float, float, float]] = {
    "15-1252": (75300.0, 95340.0, 118000.0),  # Software Developers
    "15-1211": (68200.0, 85620.0, 104000.0),  # Computer Systems Analysts
    "15-1299": (61200.0, 78900.0, 96000.0),  # Computer Occupations, All Other
}


def _normalize_soc(soc_code: str) -> str:
    """Strip O*NET-style decimals (e.g. 15-1252.00 -> 15-1252).

    Canonical convention: `.cursor/rules/integration-schema.mdc` § SOC / O*NET normalization.
    """
    s = (soc_code or "").strip()
    if not s:
        return ""
    base = s.split(".")[0].strip()
    return base


class MockBLSAdapter(AbstractBLSAdapter):
    """Phase 1 mock BLS wage data; implements :class:`AbstractBLSAdapter`."""

    async def get_wage_data(self, soc_code: str, region: str) -> WageEstimate | None:
        """Return wage statistics for known SOCs; ``None`` for unknown or invalid input."""
        await asyncio.sleep(0)
        try:
            code = _normalize_soc(soc_code)
            reg = (region or "").strip() or "unknown"
            if not code:
                log.warning(
                    "bls_adapter_get_wage_data_invalid_input",
                    reason="empty_soc_code",
                )
                return None
            row = _OEWS_KNOWN.get(code)
            if row is None:
                log.info(
                    "bls_adapter_unknown_soc",
                    soc_code=code,
                    region=reg,
                )
                return None
            p25, median, p75 = row
            return WageEstimate(
                soc_code=code,
                region=reg,
                median_wage=median,
                percentile_25=p25,
                percentile_75=p75,
                source="mock",
            )
        except Exception as exc:  # noqa: BLE001 — contract: never raise to callers
            log.warning(
                "bls_adapter_get_wage_data_failed",
                soc_code=soc_code,
                error=str(exc),
            )
            return None


# Backward-compatible name for imports expecting ``BLSAdapter``.
BLSAdapter = MockBLSAdapter
