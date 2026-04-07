"""Cluster labeling helpers for canonical role clustering."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence

import structlog

from agents.analytics.clustering.config import cluster_label_dominance_threshold
from agents.analytics.clustering.text import normalize_clustering_text_fragment
from agents.analytics.clustering.types import (
    ClusteredPosting,
    ClusteringResult,
    ClusterSummary,
    PostingClusterFeatures,
)
from agents.common.llm_adapter import complete

log = structlog.get_logger()

_LABEL_AGENT_NAME = "analytics-clustering-labeler"
_LABEL_MAX_TOKENS = 48
_RESPONSIBILITY_SAMPLE_LIMIT = 6
_REPRESENTATIVE_TITLE_LIMIT = 6
_DESCRIPTION_SKILL_LIMIT = 3
_DESCRIPTION_TOOL_LIMIT = 2

ClusterLabeler = Callable[[ClusterSummary, Sequence[PostingClusterFeatures]], str | None]


def _feature_map(features_rows: Sequence[PostingClusterFeatures]) -> dict[str, PostingClusterFeatures]:
    feature_map: dict[str, PostingClusterFeatures] = {}
    duplicate_count = 0
    for row in features_rows:
        if row.posting_id in feature_map:
            duplicate_count += 1
            continue
        feature_map[row.posting_id] = row
    if duplicate_count:
        log.warning("clustering_label_duplicate_feature_rows", duplicate_count=duplicate_count)
    return feature_map


def _cluster_feature_rows(
    cluster: ClusterSummary,
    feature_map: dict[str, PostingClusterFeatures],
) -> list[PostingClusterFeatures]:
    return [
        feature_map[posting_id]
        for posting_id in cluster.member_posting_ids
        if posting_id in feature_map
    ]


def _most_common_title(feature_rows: Sequence[PostingClusterFeatures]) -> tuple[str | None, float]:
    if not feature_rows:
        return None, 0.0
    counts = Counter(feature_row.title for feature_row in feature_rows)
    title, count = counts.most_common(1)[0]
    return title, count / len(feature_rows)


def _fallback_label(cluster: ClusterSummary, feature_rows: Sequence[PostingClusterFeatures]) -> str:
    title, _dominance = _most_common_title(feature_rows)
    if title:
        return title
    if cluster.representative_titles:
        return cluster.representative_titles[0]
    return cluster.cluster_id


def _responsibility_samples(feature_rows: Sequence[PostingClusterFeatures]) -> list[str]:
    seen: set[str] = set()
    samples: list[str] = []
    for feature_row in feature_rows:
        for responsibility in feature_row.responsibilities:
            normalized = normalize_clustering_text_fragment(responsibility)
            if not normalized:
                continue
            folded = normalized.casefold()
            if folded in seen:
                continue
            seen.add(folded)
            samples.append(normalized)
            if len(samples) >= _RESPONSIBILITY_SAMPLE_LIMIT:
                return samples
    return samples


def _representative_title_samples(
    cluster: ClusterSummary,
    feature_rows: Sequence[PostingClusterFeatures],
) -> list[str]:
    samples: list[str] = []
    seen: set[str] = set()

    for title in cluster.representative_titles:
        normalized = normalize_clustering_text_fragment(title)
        if not normalized:
            continue
        folded = normalized.casefold()
        if folded in seen:
            continue
        seen.add(folded)
        samples.append(normalized)
        if len(samples) >= _REPRESENTATIVE_TITLE_LIMIT:
            return samples

    ordered_feature_rows = sorted(
        feature_rows,
        key=lambda feature_row: (feature_row.title.casefold(), feature_row.posting_id),
    )
    for feature_row in ordered_feature_rows:
        normalized = normalize_clustering_text_fragment(feature_row.title)
        if not normalized:
            continue
        folded = normalized.casefold()
        if folded in seen:
            continue
        seen.add(folded)
        samples.append(normalized)
        if len(samples) >= _REPRESENTATIVE_TITLE_LIMIT:
            return samples

    return samples


def _cluster_label_prompt(cluster: ClusterSummary, feature_rows: Sequence[PostingClusterFeatures]) -> str:
    top_titles = _representative_title_samples(cluster, feature_rows)
    top_skills = [skill.skill_name for skill in cluster.top_skills[:5]]
    top_tools = [tool.tool_name for tool in cluster.top_tools[:5]]
    responsibilities = _responsibility_samples(feature_rows)

    prompt_lines = [
        "Generate a concise canonical job role label.",
        "Return only the role label with no explanation.",
        f"Representative titles: {', '.join(top_titles) or 'n/a'}",
        f"Top skills: {', '.join(top_skills) or 'n/a'}",
        f"Top tools: {', '.join(top_tools) or 'n/a'}",
        f"Responsibilities: {', '.join(responsibilities) or 'n/a'}",
    ]
    return "\n".join(prompt_lines)


def _normalize_label_output(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    first_line = value.strip().splitlines()[0].strip() if value.strip() else ""
    normalized = first_line.strip("\"' ")
    return normalized or None


def _cluster_description(cluster: ClusterSummary, label: str) -> str:
    skills = [skill.skill_name for skill in cluster.top_skills[:_DESCRIPTION_SKILL_LIMIT]]
    tools = [tool.tool_name for tool in cluster.top_tools[:_DESCRIPTION_TOOL_LIMIT]]
    titles = [
        title
        for title in cluster.representative_titles[:_REPRESENTATIVE_TITLE_LIMIT]
        if title.casefold() != label.casefold()
    ]

    fragments: list[str] = []
    if skills:
        fragments.append(f"Common skills include {', '.join(skills)}")
    if tools:
        fragments.append(f"Common tools include {', '.join(tools)}")
    if not fragments and titles:
        fragments.append(f"Representative titles include {', '.join(titles[:3])}")

    if not fragments:
        return label
    return f"{label}. {' '.join(fragments)}"


def _default_llm_labeler(cluster: ClusterSummary, feature_rows: Sequence[PostingClusterFeatures]) -> str | None:
    prompt = _cluster_label_prompt(cluster, feature_rows)
    try:
        result = complete(
            prompt,
            agent_name=_LABEL_AGENT_NAME,
            max_tokens=_LABEL_MAX_TOKENS,
        )
    except Exception as exc:
        log.warning(
            "clustering_label_llm_exception",
            cluster_id=cluster.cluster_id,
            error_type=type(exc).__name__,
        )
        return None

    if not result.get("success") or result.get("extraction_failed"):
        log.warning("clustering_label_llm_failed", cluster_id=cluster.cluster_id)
        return None

    return _normalize_label_output(result.get("content"))


def label_clusters(
    result: ClusteringResult,
    features_rows: Sequence[PostingClusterFeatures],
    *,
    llm_labeler: ClusterLabeler | None = None,
    allow_llm_fallback: bool = True,
    dominance_threshold: float | None = None,
) -> ClusteringResult:
    """Apply dominant-title or LLM-generated labels to cluster summaries."""
    if result.skipped or not result.clusters:
        return result

    effective_dominance_threshold = (
        cluster_label_dominance_threshold()
        if dominance_threshold is None
        else dominance_threshold
    )
    if not 0.0 <= effective_dominance_threshold <= 1.0:
        raise ValueError("dominance_threshold must be between 0.0 and 1.0")

    feature_map = _feature_map(features_rows)
    effective_llm_labeler = llm_labeler or _default_llm_labeler

    updated_clusters: list[ClusterSummary] = []
    label_by_cluster_id: dict[str, str] = {}
    dominant_title_count = 0
    llm_generated_count = 0
    fallback_count = 0

    for cluster in result.clusters:
        cluster_features = _cluster_feature_rows(cluster, feature_map)
        dominant_title, dominant_share = _most_common_title(cluster_features)

        label = None
        label_source = cluster.label_source
        is_llm_generated_label = False

        if dominant_title and dominant_share >= effective_dominance_threshold:
            label = dominant_title
            label_source = "dominant_title"
            dominant_title_count += 1
        elif allow_llm_fallback:
            llm_label = effective_llm_labeler(cluster, cluster_features)
            if llm_label:
                label = llm_label
                label_source = "llm"
                is_llm_generated_label = True
                llm_generated_count += 1

        if label is None:
            label = _fallback_label(cluster, cluster_features)
            label_source = "fallback"
            fallback_count += 1

        updated_cluster = cluster.model_copy(
            update={
                "label": label,
                "label_source": label_source,
                "description": _cluster_description(cluster, label),
                "is_llm_generated_label": is_llm_generated_label,
            }
        )
        updated_clusters.append(updated_cluster)
        label_by_cluster_id[cluster.cluster_id] = label

    updated_assignments: list[ClusteredPosting] = []
    for assignment in result.assignments:
        cluster_label = None
        if assignment.cluster_id is not None:
            cluster_label = label_by_cluster_id.get(assignment.cluster_id)
        updated_assignments.append(
            assignment.model_copy(
                update={
                    "cluster_label": cluster_label,
                }
            )
        )

    log.info(
        "clustering_labels_applied",
        cluster_count=len(updated_clusters),
        dominant_title_count=dominant_title_count,
        llm_generated_count=llm_generated_count,
        fallback_count=fallback_count,
        dominance_threshold=effective_dominance_threshold,
    )

    return result.model_copy(
        update={
            "clusters": updated_clusters,
            "assignments": updated_assignments,
        }
    )
