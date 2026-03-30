"""External data adapters for the Enrichment Agent (BLS, O*NET, Census).

Phase 1 stubs return shaped mock payloads; Phase 2 swaps in ``httpx`` clients.
"""

from agents.enrichment.adapters.bls_adapter import BLSAdapter
from agents.enrichment.adapters.census_adapter import CensusAdapter
from agents.enrichment.adapters.onet_adapter import ONETAdapter

__all__ = [
    "BLSAdapter",
    "CensusAdapter",
    "ONETAdapter",
]
