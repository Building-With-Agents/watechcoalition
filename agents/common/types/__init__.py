"""Shared Pydantic types for the Job Intelligence Engine pipeline."""

from agents.common.types.extraction_types import (
    ContextSignal,
    ExtractionMetadata,
    ResponsibilityRecord,
    SkillRecord,
    SpanRecord,
    TaskRecord,
    TaxonomyResult,
    ToolRecord,
)
from agents.common.types.job_record import JobRecord
from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig

__all__ = [
    "ContextSignal",
    "ExtractionMetadata",
    "JobRecord",
    "RawJobRecord",
    "RegionConfig",
    "ResponsibilityRecord",
    "SkillRecord",
    "SpanRecord",
    "TaskRecord",
    "TaxonomyResult",
    "ToolRecord",
]
