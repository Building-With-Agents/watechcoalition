"""Shared Pydantic types for the Job Intelligence Engine pipeline."""

from agents.common.types.extraction_metadata import ExtractionMetadata
from agents.common.types.job_record import JobRecord
from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.common.types.skill_record import SkillRecord, ToolRecord

__all__ = [
    "ExtractionMetadata",
    "JobRecord",
    "RawJobRecord",
    "RegionConfig",
    "SkillRecord",
    "ToolRecord",
]
