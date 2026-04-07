"""Typed handoff models for canonical role clustering."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

ClusterLabelSource = Literal["dominant_title", "llm", "fallback", "unlabeled"]
ClusteringSkipReason = Literal[
    "insufficient_total_postings",
    "no_eligible_postings",
    "embedding_generation_failed",
    "all_points_marked_noise",
    "all_clusters_filtered",
]


def _normalize_required_string(value: object, *, field_name: str) -> str:
    text = _normalize_optional_string(value)
    if text is None:
        raise ValueError(f"{field_name} must be a non-empty string")
    return text


def _normalize_optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = value if isinstance(value, str) else str(value)
    normalized = text.strip()
    return normalized or None


def _normalize_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items: Iterable[object] = [value]
    elif isinstance(value, Iterable) and not isinstance(value, Mapping):
        raw_items = value
    else:
        raw_items = [value]

    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = _normalize_optional_string(item)
        if text is None or text in seen:
            continue
        normalized.append(text)
        seen.add(text)
    return normalized


class RankedSkill(BaseModel):
    """Frequency-ranked skill extracted from a cluster or emergence candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    skill_name: str = Field(description="Normalized skill label.")
    count: int = Field(ge=1, description="Number of postings containing the skill.")

    @field_validator("skill_name", mode="before")
    @classmethod
    def normalize_skill_name(cls, value: object) -> str:
        return _normalize_required_string(value, field_name="skill_name")


class RankedTool(BaseModel):
    """Frequency-ranked tool extracted from a cluster or emergence candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tool_name: str = Field(description="Normalized tool label.")
    count: int = Field(ge=1, description="Number of postings containing the tool.")

    @field_validator("tool_name", mode="before")
    @classmethod
    def normalize_tool_name(cls, value: object) -> str:
        return _normalize_required_string(value, field_name="tool_name")


class PostingClusterFeatures(BaseModel):
    """Pure clustering input for one posting after upstream normalization/enrichment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    posting_id: str = Field(description="Stable job posting id used for DB updates and traceability.")
    title: str = Field(description="Normalized job title used for clustering and label generation.")
    skills: list[str] = Field(default_factory=list, description="Normalized extracted skill labels.")
    tools: list[str] = Field(default_factory=list, description="Normalized extracted tool labels.")
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Normalized responsibility phrases used in embedding text.",
    )
    seniority: str | None = Field(default=None, description="Optional normalized seniority label.")
    employer_id: str | None = Field(default=None, description="Employer identifier for emergence filtering.")
    employer_name: str | None = Field(
        default=None,
        description="Fallback employer identity when a stable employer id is unavailable.",
    )
    quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional quality score used by emergence filtering.",
    )

    @field_validator("posting_id", "title", mode="before")
    @classmethod
    def normalize_required_fields(cls, value: object, info: ValidationInfo) -> str:
        field_name = info.field_name or "value"
        return _normalize_required_string(value, field_name=field_name)

    @field_validator("seniority", "employer_id", "employer_name", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: object) -> str | None:
        return _normalize_optional_string(value)

    @field_validator("skills", "tools", "responsibilities", mode="before")
    @classmethod
    def normalize_signal_lists(cls, value: object) -> list[str]:
        return _normalize_string_list(value)


class ClusteredPosting(BaseModel):
    """Cluster assignment for one posting in a single clustering run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    posting_id: str = Field(description="Stable job posting id.")
    cluster_id: str | None = Field(
        default=None,
        description="Run-local cluster identifier; null when the posting is classified as noise.",
    )
    raw_cluster_label: int | None = Field(
        default=None,
        description="Raw HDBSCAN label; null when the posting is skipped or classified as noise.",
    )
    cluster_label: str | None = Field(
        default=None,
        description="Human-readable label attached after cluster summary generation.",
    )
    is_noise: bool = Field(default=False, description="True when HDBSCAN classifies the posting as noise.")
    assignment_confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional soft membership confidence when available from the clustering backend.",
    )

    @field_validator("posting_id", mode="before")
    @classmethod
    def normalize_posting_id(cls, value: object) -> str:
        return _normalize_required_string(value, field_name="posting_id")

    @field_validator("cluster_id", "cluster_label", mode="before")
    @classmethod
    def normalize_optional_cluster_fields(cls, value: object) -> str | None:
        return _normalize_optional_string(value)

    @model_validator(mode="after")
    def validate_assignment_shape(self) -> ClusteredPosting:
        if self.is_noise:
            if self.cluster_id is not None:
                raise ValueError("noise assignments may not include cluster_id")
            return self

        if self.cluster_id is None:
            raise ValueError("non-noise assignments must include cluster_id")
        return self


class ClusterSummary(BaseModel):
    """Summary Bryan hands to Emilio for one discovered role cluster."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    cluster_id: str = Field(description="Run-local cluster identifier.")
    raw_cluster_label: int = Field(description="Raw HDBSCAN label for this cluster.")
    label: str | None = Field(default=None, description="Human-readable cluster label.")
    label_source: ClusterLabelSource = Field(
        default="unlabeled",
        description="How the human-readable label was determined.",
    )
    member_posting_ids: list[str] = Field(
        default_factory=list,
        description="Stable posting ids assigned to this cluster.",
    )
    member_count: int = Field(ge=1, description="Number of postings in the cluster.")
    representative_titles: list[str] = Field(
        default_factory=list,
        description="Ordered sample titles used for QA and label generation.",
    )
    top_skills: list[RankedSkill] = Field(default_factory=list)
    top_tools: list[RankedTool] = Field(default_factory=list)
    centroid_embedding: list[float] | None = Field(
        default=None,
        description="Mean embedding vector for persistence into canonical_roles.",
    )
    description: str | None = Field(
        default=None,
        description="Optional longer cluster description used by downstream persistence or QA.",
    )
    is_llm_generated_label: bool = Field(
        default=False,
        description="True when the final label came from an LLM fallback instead of title dominance.",
    )

    @field_validator("cluster_id", mode="before")
    @classmethod
    def normalize_cluster_id(cls, value: object) -> str:
        return _normalize_required_string(value, field_name="cluster_id")

    @field_validator("label", "description", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> str | None:
        return _normalize_optional_string(value)

    @field_validator("member_posting_ids", "representative_titles", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: object) -> list[str]:
        return _normalize_string_list(value)

    @field_validator("centroid_embedding", mode="before")
    @classmethod
    def normalize_centroid_embedding(cls, value: object) -> list[float] | None:
        if value is None:
            return None
        if isinstance(value, str):
            raise ValueError("centroid_embedding must be a numeric sequence, not a string")
        if not isinstance(value, Iterable):
            raise ValueError("centroid_embedding must be a numeric sequence")
        return [float(item) for item in value]

    @model_validator(mode="after")
    def validate_member_counts(self) -> ClusterSummary:
        if len(self.member_posting_ids) != self.member_count:
            raise ValueError("member_count must match the number of member_posting_ids")
        return self


class EmergenceCandidate(BaseModel):
    """Filtered emergence candidate ready for Emilio to persist or emit as an alert."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(description="Run-local identifier for the emergence candidate group.")
    posting_ids: list[str] = Field(default_factory=list, description="Posting ids grouped into this candidate.")
    posting_count: int = Field(ge=1, description="Number of postings in the candidate group.")
    candidate_role_label: str | None = Field(
        default=None,
        description="Short proposed label for the candidate group.",
    )
    top_skills: list[RankedSkill] = Field(default_factory=list)
    top_tools: list[RankedTool] = Field(default_factory=list)
    employer_ids: list[str] = Field(
        default_factory=list,
        description="Distinct employer ids or names supporting the multi-employer rule.",
    )
    nearest_cluster_id: str | None = Field(
        default=None,
        description="Closest discovered cluster within the run, if any.",
    )
    filter_reason: str | None = Field(
        default=None,
        description="Why the candidate passed emergence filtering rather than remaining plain noise.",
    )

    @field_validator("candidate_id", mode="before")
    @classmethod
    def normalize_candidate_id(cls, value: object) -> str:
        return _normalize_required_string(value, field_name="candidate_id")

    @field_validator("candidate_role_label", "nearest_cluster_id", "filter_reason", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: object) -> str | None:
        return _normalize_optional_string(value)

    @field_validator("posting_ids", "employer_ids", mode="before")
    @classmethod
    def normalize_id_lists(cls, value: object) -> list[str]:
        return _normalize_string_list(value)

    @model_validator(mode="after")
    def validate_candidate_counts(self) -> EmergenceCandidate:
        if len(self.posting_ids) != self.posting_count:
            raise ValueError("posting_count must match the number of posting_ids")
        return self


class ClusteringResult(BaseModel):
    """Top-level handoff structure from Bryan's clustering pipeline to Emilio."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assignments: list[ClusteredPosting] = Field(default_factory=list)
    clusters: list[ClusterSummary] = Field(default_factory=list)
    emergence_candidates: list[EmergenceCandidate] = Field(default_factory=list)
    total_input_postings: int = Field(ge=0, description="Total postings received by the clustering pipeline.")
    eligible_posting_count: int = Field(
        ge=0,
        description="Postings that passed Bryan's eligibility checks before embedding/clustering.",
    )
    clustered_posting_count: int = Field(ge=0, description="Postings assigned to non-noise clusters.")
    noise_posting_count: int = Field(ge=0, description="Postings marked as noise after clustering.")
    skipped: bool = Field(default=False, description="True when the clustering run was deliberately skipped.")
    skip_reason: ClusteringSkipReason | None = Field(
        default=None,
        description="Machine-readable reason for skipping the run.",
    )

    @model_validator(mode="after")
    def validate_counts(self) -> ClusteringResult:
        if self.eligible_posting_count > self.total_input_postings:
            raise ValueError("eligible_posting_count may not exceed total_input_postings")
        if self.clustered_posting_count + self.noise_posting_count > self.eligible_posting_count:
            raise ValueError("clustered_posting_count + noise_posting_count may not exceed eligible_posting_count")
        if self.skipped and self.skip_reason is None:
            raise ValueError("skipped results must include skip_reason")
        if not self.skipped and self.skip_reason is not None:
            raise ValueError("skip_reason may only be set when skipped is true")
        return self
