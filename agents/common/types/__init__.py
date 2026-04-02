"""Shared Pydantic types for the Job Intelligence Engine pipeline."""

from agents.common.types.extraction_schemas import (
    ContextSignal,
    ResponsibilityRecord,
    TaskRecord,
)
from agents.common.types.extraction_types import (
    ExtractionMetadata,
    SkillRecord,
    SpanRecord,
    TaxonomyResult,
    ToolRecord,
)
from agents.common.types.job_record import JobRecord
from agents.common.types.query_request import QueryPersona, QueryRequest
from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig

__all__ = [
    "ContextSignal",
    "ExtractionMetadata",
    "JobRecord",
    "QueryPersona",
    "QueryRequest",
    "RawJobRecord",
    "RegionConfig",
    "ResponsibilityRecord",
    "SkillRecord",
    "SpanRecord",
    "TaskRecord",
    "TaxonomyResult",
    "ToolRecord",
]
