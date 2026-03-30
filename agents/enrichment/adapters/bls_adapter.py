"""Bureau of Labor Statistics adapter — OEWS-style wage data (Phase 1 stub).

Phase 2: use ``httpx`` against ``https://api.bls.gov`` with any API key from
``os.getenv("BLS_API_KEY")`` or documented BLS public endpoints — never hardcode credentials.
"""

from __future__ import annotations

import structlog

log = structlog.get_logger()


class BLSAdapter:
    """Fetches BLS occupational employment / wage statistics.

    Phase 1 returns deterministic mock payloads shaped like OEWS API results.
    """

    def get_wage_data(self, soc_code: str) -> dict | None:
        """Return wage / employment context for ``soc_code``.

        Phase 1: mock data shaped like a real BLS API response.
        Phase 2: replace stub with a live ``httpx`` call to ``api.bls.gov`` (see module docstring).

        Returns ``None`` on any failure; never raises.
        """
        try:
            code = (soc_code or "").strip()
            if not code:
                log.warning(
                    "bls_adapter_get_wage_data_invalid_input",
                    reason="empty_soc_code",
                )
                return None

            return {
                "series_id": f"OEWS{code}",
                "occupation": code,
                "annual_mean_wage": None,
                "employment": None,
                "source": "bls_stub",
            }
        except Exception as exc:  # noqa: BLE001 — contract: never raise to callers
            log.warning(
                "bls_adapter_get_wage_data_failed",
                soc_code=soc_code,
                error=str(exc),
            )
            return None
