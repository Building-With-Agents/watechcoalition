"""External data adapters for the Enrichment Agent (BLS, O*NET, Census).

Phase 1 mocks implement abstract bases; Phase 2 swaps in ``httpx`` clients.
"""

from agents.enrichment.adapters.base import (
    AbstractBLSAdapter,
    AbstractCensusAdapter,
    AbstractONETAdapter,
)
from agents.enrichment.adapters.bls_adapter import BLSAdapter, MockBLSAdapter
from agents.enrichment.adapters.census_adapter import CensusAdapter, MockCensusAdapter
from agents.enrichment.adapters.facade import ExternalEnrichmentFacade
from agents.enrichment.adapters.models import (
    OccupationProfile,
    RegionalProfile,
    SOCMatch,
    WageEstimate,
)
from agents.enrichment.adapters.onet_adapter import MockONETAdapter, ONETAdapter

__all__ = [
    "AbstractBLSAdapter",
    "AbstractCensusAdapter",
    "AbstractONETAdapter",
    "BLSAdapter",
    "CensusAdapter",
    "ExternalEnrichmentFacade",
    "MockBLSAdapter",
    "MockCensusAdapter",
    "MockONETAdapter",
    "ONETAdapter",
    "OccupationProfile",
    "RegionalProfile",
    "SOCMatch",
    "WageEstimate",
]
