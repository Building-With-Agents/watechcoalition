"""Pure clustering pipeline for canonical role discovery."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
import structlog

from agents.analytics.clustering.config import (
    cluster_distance_metric,
    cluster_min_cluster_size,
    cluster_min_samples,
    cluster_min_total_postings,
    cluster_selection_epsilon,
)
from agents.analytics.clustering.emergence import detect_emergence_candidates
from agents.analytics.clustering.labeling import ClusterLabeler, label_clusters
from agents.analytics.clustering.types import (
    ClusteredPosting,
    ClusteringResult,
    ClusterSummary,
    EmbeddedPostingText,
    PostingClusterFeatures,
    RankedSkill,
    RankedTool,
)

log = structlog.get_logger()

_TOP_SKILLS_LIMIT = 10
_TOP_TOOLS_LIMIT = 5
_REPRESENTATIVE_TITLES_LIMIT = 5


def _default_clusterer_factory(**kwargs: Any) -> Any:
    try:
        import hdbscan
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "hdbscan is not installed; install agents/requirements.txt before running clustering"
        ) from exc
    return hdbscan.HDBSCAN(**kwargs)


def _dedupe_feature_rows(features_rows: Sequence[PostingClusterFeatures]) -> dict[str, PostingClusterFeatures]:
    feature_map: dict[str, PostingClusterFeatures] = {}
    duplicate_count = 0
    for row in features_rows:
        if row.posting_id in feature_map:
            duplicate_count += 1
            continue
        feature_map[row.posting_id] = row
    if duplicate_count:
        log.warning("clustering_duplicate_feature_rows", duplicate_count=duplicate_count)
    return feature_map


def _dedupe_embedded_rows(embedded_rows: Sequence[EmbeddedPostingText]) -> dict[str, EmbeddedPostingText]:
    embedded_map: dict[str, EmbeddedPostingText] = {}
    duplicate_count = 0
    for row in embedded_rows:
        if row.posting_id in embedded_map:
            duplicate_count += 1
            continue
        embedded_map[row.posting_id] = row
    if duplicate_count:
        log.warning("clustering_duplicate_embedding_rows", duplicate_count=duplicate_count)
    return embedded_map


def _aligned_rows(
    features_rows: Sequence[PostingClusterFeatures],
    embedded_rows: Sequence[EmbeddedPostingText],
) -> list[tuple[PostingClusterFeatures, EmbeddedPostingText]]:
    feature_map = _dedupe_feature_rows(features_rows)
    embedded_map = _dedupe_embedded_rows(embedded_rows)

    missing_embedding_count = 0
    aligned: list[tuple[PostingClusterFeatures, EmbeddedPostingText]] = []
    for posting_id, feature_row in feature_map.items():
        embedded_row = embedded_map.get(posting_id)
        if embedded_row is None:
            missing_embedding_count += 1
            continue
        aligned.append((feature_row, embedded_row))

    orphan_embedding_count = sum(1 for posting_id in embedded_map if posting_id not in feature_map)

    if missing_embedding_count:
        log.warning("clustering_missing_embeddings", missing_embedding_count=missing_embedding_count)
    if orphan_embedding_count:
        log.warning("clustering_orphan_embeddings", orphan_embedding_count=orphan_embedding_count)

    return aligned


def _embedding_matrix(aligned_rows: Sequence[tuple[PostingClusterFeatures, EmbeddedPostingText]]) -> np.ndarray | None:
    if not aligned_rows:
        return None
    try:
        matrix = np.asarray([embedded_row.embedding for _, embedded_row in aligned_rows], dtype=float)
    except ValueError:
        log.warning("clustering_embedding_matrix_invalid", reason="ragged_embeddings")
        return None
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        log.warning(
            "clustering_embedding_matrix_invalid",
            matrix_shape=list(matrix.shape),
        )
        return None
    return matrix


def _cluster_id_map(raw_labels: Sequence[int], *, minimum_cluster_size: int) -> dict[int, str]:
    surviving_labels = [
        raw_label
        for raw_label, count in sorted(Counter(raw_labels).items())
        if raw_label != -1 and count >= minimum_cluster_size
    ]
    return {raw_label: f"cluster-{index:04d}" for index, raw_label in enumerate(surviving_labels, start=1)}


def _top_titles(feature_rows: Sequence[PostingClusterFeatures]) -> list[str]:
    counts = Counter(feature_row.title for feature_row in feature_rows)
    return [title for title, _count in counts.most_common(_REPRESENTATIVE_TITLES_LIMIT)]


def _top_skills(feature_rows: Sequence[PostingClusterFeatures]) -> list[RankedSkill]:
    counts = Counter(skill for feature_row in feature_rows for skill in feature_row.skills)
    return [
        RankedSkill(skill_name=skill_name, count=count) for skill_name, count in counts.most_common(_TOP_SKILLS_LIMIT)
    ]


def _top_tools(feature_rows: Sequence[PostingClusterFeatures]) -> list[RankedTool]:
    counts = Counter(tool for feature_row in feature_rows for tool in feature_row.tools)
    return [RankedTool(tool_name=tool_name, count=count) for tool_name, count in counts.most_common(_TOP_TOOLS_LIMIT)]


def _cluster_centroid(embedded_rows: Sequence[EmbeddedPostingText]) -> list[float]:
    matrix = np.asarray([embedded_row.embedding for embedded_row in embedded_rows], dtype=float)
    centroid = np.mean(matrix, axis=0)
    return [float(value) for value in centroid.tolist()]


def run_clustering(
    features_rows: Sequence[PostingClusterFeatures],
    embedded_rows: Sequence[EmbeddedPostingText],
    *,
    clusterer_factory: Callable[..., Any] | None = None,
) -> ClusteringResult:
    """Run HDBSCAN on prepared posting embeddings and return cluster assignments."""
    total_input_postings = len(features_rows)
    aligned_rows = _aligned_rows(features_rows, embedded_rows)
    eligible_posting_count = len(aligned_rows)

    if not embedded_rows and total_input_postings > 0:
        log.warning(
            "clustering_skipped_embedding_generation_failed",
            total_input_postings=total_input_postings,
        )
        return ClusteringResult(
            total_input_postings=total_input_postings,
            eligible_posting_count=0,
            clustered_posting_count=0,
            noise_posting_count=0,
            skipped=True,
            skip_reason="embedding_generation_failed",
        )

    if eligible_posting_count == 0:
        log.info("clustering_skipped_no_eligible_postings", total_input_postings=total_input_postings)
        return ClusteringResult(
            total_input_postings=total_input_postings,
            eligible_posting_count=0,
            clustered_posting_count=0,
            noise_posting_count=0,
            skipped=True,
            skip_reason="no_eligible_postings",
        )

    minimum_total_postings = cluster_min_total_postings()
    if eligible_posting_count < minimum_total_postings:
        log.info(
            "clustering_skipped_insufficient_total_postings",
            total_input_postings=total_input_postings,
            eligible_posting_count=eligible_posting_count,
            minimum_total_postings=minimum_total_postings,
        )
        return ClusteringResult(
            total_input_postings=total_input_postings,
            eligible_posting_count=eligible_posting_count,
            clustered_posting_count=0,
            noise_posting_count=0,
            skipped=True,
            skip_reason="insufficient_total_postings",
        )

    matrix = _embedding_matrix(aligned_rows)
    if matrix is None:
        return ClusteringResult(
            total_input_postings=total_input_postings,
            eligible_posting_count=eligible_posting_count,
            clustered_posting_count=0,
            noise_posting_count=0,
            skipped=True,
            skip_reason="embedding_generation_failed",
        )

    minimum_cluster_size = cluster_min_cluster_size()
    minimum_samples = cluster_min_samples()
    selection_epsilon = cluster_selection_epsilon()
    distance_metric = cluster_distance_metric()

    effective_clusterer_factory = clusterer_factory or _default_clusterer_factory
    clusterer = effective_clusterer_factory(
        min_cluster_size=minimum_cluster_size,
        min_samples=minimum_samples,
        cluster_selection_epsilon=selection_epsilon,
        metric=distance_metric,
    )

    raw_labels = clusterer.fit_predict(matrix)
    if len(raw_labels) != eligible_posting_count:
        log.warning(
            "clustering_label_count_mismatch",
            eligible_posting_count=eligible_posting_count,
            label_count=len(raw_labels),
        )
        return ClusteringResult(
            total_input_postings=total_input_postings,
            eligible_posting_count=eligible_posting_count,
            clustered_posting_count=0,
            noise_posting_count=0,
            skipped=True,
            skip_reason="embedding_generation_failed",
        )

    probabilities = getattr(clusterer, "probabilities_", None)
    probability_values: list[float | None]
    if isinstance(probabilities, np.ndarray) and len(probabilities) == eligible_posting_count:
        probability_values = [float(value) for value in probabilities.tolist()]
    else:
        probability_values = [None] * eligible_posting_count

    raw_label_values = [int(label) for label in raw_labels]
    cluster_ids_by_raw_label = _cluster_id_map(raw_label_values, minimum_cluster_size=minimum_cluster_size)

    assignments: list[ClusteredPosting] = []
    cluster_slices: dict[int, list[tuple[PostingClusterFeatures, EmbeddedPostingText]]] = {}

    for (feature_row, embedded_row), raw_label, probability in zip(
        aligned_rows,
        raw_label_values,
        probability_values,
        strict=True,
    ):
        cluster_id = cluster_ids_by_raw_label.get(raw_label)
        is_noise = cluster_id is None
        assignments.append(
            ClusteredPosting(
                posting_id=feature_row.posting_id,
                cluster_id=cluster_id,
                raw_cluster_label=raw_label,
                cluster_label=None,
                is_noise=is_noise,
                assignment_confidence=probability,
            )
        )
        if is_noise:
            continue
        cluster_slices.setdefault(raw_label, []).append((feature_row, embedded_row))

    cluster_summaries: list[ClusterSummary] = []
    for raw_label in sorted(cluster_slices):
        rows = cluster_slices[raw_label]
        feature_slice = [feature_row for feature_row, _embedded_row in rows]
        embedded_slice = [embedded_row for _feature_row, embedded_row in rows]
        cluster_summaries.append(
            ClusterSummary(
                cluster_id=cluster_ids_by_raw_label[raw_label],
                raw_cluster_label=raw_label,
                label=None,
                label_source="unlabeled",
                member_posting_ids=[feature_row.posting_id for feature_row in feature_slice],
                member_count=len(feature_slice),
                representative_titles=_top_titles(feature_slice),
                top_skills=_top_skills(feature_slice),
                top_tools=_top_tools(feature_slice),
                centroid_embedding=_cluster_centroid(embedded_slice),
                description=None,
                is_llm_generated_label=False,
            )
        )

    clustered_posting_count = sum(1 for assignment in assignments if not assignment.is_noise)
    noise_posting_count = sum(1 for assignment in assignments if assignment.is_noise)

    log.info(
        "clustering_completed",
        total_input_postings=total_input_postings,
        eligible_posting_count=eligible_posting_count,
        cluster_count=len(cluster_summaries),
        clustered_posting_count=clustered_posting_count,
        noise_posting_count=noise_posting_count,
        minimum_cluster_size=minimum_cluster_size,
        minimum_samples=minimum_samples,
        selection_epsilon=selection_epsilon,
        distance_metric=distance_metric,
    )

    return ClusteringResult(
        assignments=assignments,
        clusters=cluster_summaries,
        emergence_candidates=[],
        total_input_postings=total_input_postings,
        eligible_posting_count=eligible_posting_count,
        clustered_posting_count=clustered_posting_count,
        noise_posting_count=noise_posting_count,
        skipped=False,
        skip_reason=None,
    )


def run_clustering_pipeline(
    features_rows: Sequence[PostingClusterFeatures],
    embedded_rows: Sequence[EmbeddedPostingText],
    *,
    clusterer_factory: Callable[..., Any] | None = None,
    llm_labeler: ClusterLabeler | None = None,
    allow_llm_fallback: bool = True,
) -> ClusteringResult:
    """Run discovery, label clusters, and filter emergence candidates."""
    base_result = run_clustering(
        features_rows,
        embedded_rows,
        clusterer_factory=clusterer_factory,
    )
    labeled_result = label_clusters(
        base_result,
        features_rows,
        llm_labeler=llm_labeler,
        allow_llm_fallback=allow_llm_fallback,
    )
    emergence_candidates = detect_emergence_candidates(
        labeled_result,
        features_rows,
        embedded_rows,
    )
    return labeled_result.model_copy(
        update={
            "emergence_candidates": emergence_candidates,
        }
    )
