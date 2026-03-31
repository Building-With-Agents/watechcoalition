"""JSON snapshot schema for extraction eval runs (Streamlit load + CLI output)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

SNAPSHOT_SCHEMA_VERSION = "1.2"


class AggregateMetrics(BaseModel):
    """Micro-averaged P/R/F1: matched/pred, matched/true (same micro definition as v1.0 skills/tools)."""

    total_gt_skills: int
    total_pred_skills: int
    matched_skills: int
    precision_skills: float
    recall_skills: float
    f1_skills: float = 0.0
    total_gt_tools: int
    total_pred_tools: int
    matched_tools: int
    precision_tools: float
    recall_tools: float
    f1_tools: float = 0.0
    total_gt_tasks: int = 0
    total_pred_tasks: int = 0
    matched_tasks: int = 0
    precision_tasks: float = 0.0
    recall_tasks: float = 0.0
    f1_tasks: float = 0.0
    total_gt_responsibilities: int = 0
    total_pred_responsibilities: int = 0
    matched_responsibilities: int = 0
    precision_responsibilities: float = 0.0
    recall_responsibilities: float = 0.0
    f1_responsibilities: float = 0.0
    total_gt_context: int = 0
    total_pred_context: int = 0
    matched_context: int = 0
    precision_context: float = 0.0
    recall_context: float = 0.0
    f1_context: float = 0.0
    total_tokens_used: int | None = None
    total_cost_usd: float | None = None
    total_latency_ms: int | None = None
    llm_applicable: bool = False
    # Skills-only taxonomy stats over predicted SkillRecords (pipeline); None if N/A (e.g. stub).
    skills_pred_record_count: int | None = None
    skills_esco_coverage: float | None = None
    skills_genai_extension_rate: float | None = None


class PerJobSnapshot(BaseModel):
    job_key: str
    title: str
    gt_skills: list[str] = Field(default_factory=list)
    gt_tools: list[str] = Field(default_factory=list)
    pred_skills: list[str] = Field(default_factory=list)
    pred_tools: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missed_skills: list[str] = Field(default_factory=list)
    false_positive_skills: list[str] = Field(default_factory=list)
    matched_tools: list[str] = Field(default_factory=list)
    missed_tools: list[str] = Field(default_factory=list)
    false_positive_tools: list[str] = Field(default_factory=list)
    precision_skills: float = 0.0
    recall_skills: float = 0.0
    f1_skills: float = 0.0
    precision_tools: float = 0.0
    recall_tools: float = 0.0
    f1_tools: float = 0.0
    gt_tasks: list[str] = Field(default_factory=list)
    pred_tasks: list[str] = Field(default_factory=list)
    matched_tasks: list[str] = Field(default_factory=list)
    missed_tasks: list[str] = Field(default_factory=list)
    false_positive_tasks: list[str] = Field(default_factory=list)
    precision_tasks: float = 0.0
    recall_tasks: float = 0.0
    f1_tasks: float = 0.0
    gt_responsibilities: list[str] = Field(default_factory=list)
    pred_responsibilities: list[str] = Field(default_factory=list)
    matched_responsibilities: list[str] = Field(default_factory=list)
    missed_responsibilities: list[str] = Field(default_factory=list)
    false_positive_responsibilities: list[str] = Field(default_factory=list)
    precision_responsibilities: float = 0.0
    recall_responsibilities: float = 0.0
    f1_responsibilities: float = 0.0
    gt_context: list[str] = Field(default_factory=list)
    pred_context: list[str] = Field(default_factory=list)
    matched_context: list[str] = Field(default_factory=list)
    missed_context: list[str] = Field(default_factory=list)
    false_positive_context: list[str] = Field(default_factory=list)
    precision_context: float = 0.0
    recall_context: float = 0.0
    f1_context: float = 0.0
    tokens_used: int | None = None
    cost_usd: float | None = None
    latency_ms: int | None = None
    extraction_failed: bool | None = None
    llm_error_reason: str | None = None


class PromptExemplar(BaseModel):
    """First-job skills prompt slice for backlog readability."""

    skills_prompt_version: str
    system_prompt: str
    user_prompt: str
    note: str = "User sections vary per job (Pass-1 tool list). This exemplar uses the first job only."


class ExtractionEvalSnapshot(BaseModel):
    schema_version: str = Field(default=SNAPSHOT_SCHEMA_VERSION)
    mt_timestamp_iso: str
    run_label: str = ""
    git_short_hash: str | None = None
    ground_truth_path: str
    record_count: int
    extractor_mode: str  # "stub" | "llm_skills_pattern_tools"
    aggregates: AggregateMetrics
    per_job: list[PerJobSnapshot]
    prompt_exemplar: PromptExemplar | None = None
    runtime_seconds: float | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def load_snapshot(path: str | Path) -> ExtractionEvalSnapshot:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return ExtractionEvalSnapshot.model_validate(data)
