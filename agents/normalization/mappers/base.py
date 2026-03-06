"""MapperBase — abstract base for per-source field mappers.

Contract type: Architectural (Fixed) — students implement concrete mappers
but do NOT modify this interface.

Each mapper transforms a ``RawJobRecord`` (from ingestion) into a
``JobRecord`` (for the normalized_jobs table).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agents.common.types.job_record import JobRecord
from agents.common.types.raw_job_record import RawJobRecord


class MapperBase(ABC):
    """Maps raw source-specific fields to canonical normalized fields."""

    @property
    @abstractmethod
    def mapper_name(self) -> str:
        """Canonical mapper identifier (e.g. 'jsearch_mapper')."""
        ...

    @abstractmethod
    def map(self, raw: RawJobRecord) -> JobRecord:
        """Transform a RawJobRecord into a canonical JobRecord.

        Implementations should apply cleaners (clean_text, normalize_date,
        parse_salary, etc.) as appropriate for their source format.
        """


# Backward-compatibility alias
FieldMapper = MapperBase
