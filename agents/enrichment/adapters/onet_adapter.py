"""O*NET Web Services adapter — occupation details (Phase 1 stub).

Phase 2: use ``httpx`` against ``https://services.onetcenter.org`` with credentials from
``os.getenv("ONET_CLIENT_ID")`` / ``os.getenv("ONET_API_KEY")`` (or as documented by O*NET) —
never hardcode secrets.
"""

from __future__ import annotations

import structlog

log = structlog.get_logger()


class ONETAdapter:
    """Fetches O*NET occupation summaries and related skills."""

    def get_occupation(self, soc_code: str) -> dict | None:
        """Return occupation metadata for ``soc_code``.

        Phase 1: mock data shaped like a real O*NET response.
        Phase 2: replace stub with a live ``httpx`` call to ``services.onetcenter.org`` (see module docstring).

        Returns ``None`` on any failure; never raises.
        """
        try:
            code = (soc_code or "").strip()
            if not code:
                log.warning(
                    "onet_adapter_get_occupation_invalid_input",
                    reason="empty_soc_code",
                )
                return None

            return {
                "soc_code": code,
                "title": None,
                "description": None,
                "skills": [],
                "source": "onet_stub",
            }
        except Exception as exc:  # noqa: BLE001 — contract: never raise to callers
            log.warning(
                "onet_adapter_get_occupation_failed",
                soc_code=soc_code,
                error=str(exc),
            )
            return None
