"""Emergence candidate filtering for canonical role clustering."""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Sequence

import numpy as np
import structlog

from agents.analytics.clustering.config import (
    cluster_label_dominance_threshold,
    emergence_min_distinct_employers,
    emergence_min_novel_skills,
    emergence_min_quality_score,
)
from agents.analytics.clustering.text import normalize_clustering_text_fragment
from agents.analytics.clustering.types import (
    ClusteringResult,
    ClusterSummary,
    EmbeddedPostingText,
    EmergenceCandidate,
    PostingClusterFeatures,
    RankedSkill,
    RankedTool,
)

log = structlog.get_logger()

_TOP_SKILLS_LIMIT = 10
_TOP_TOOLS_LIMIT = 5


def _feature_map(features_rows: Sequence[PostingClusterFeatures]) -> dict[str, PostingClusterFeatures]:
    feature_map: dict[str, PostingClusterFeatures] = {}
    duplicate_count = 0
    for row in features_rows:
        if row.posting_id in feature_map:
            duplicate_count += 1
            continue
        feature_map[row.posting_id] = row
    if duplicate_count:
        log.warning("emergence_duplicate_feature_rows", duplicate_count=duplicate_count)
    return feature_map


def _embedding_map(embedded_rows: Sequence[EmbeddedPostingText]) -> dict[str, EmbeddedPostingText]:
    embedded_map: dict[str, EmbeddedPostingText] = {}
    duplicate_count = 0
    for row in embedded_rows:
        if row.posting_id in embedded_map:
            duplicate_count += 1
            continue
        embedded_map[row.posting_id] = row
    if duplicate_count:
        log.warning("emergence_duplicate_embedding_rows", duplicate_count=duplicate_count)
    return embedded_map


def _top_skills(feature_rows: Sequence[PostingClusterFeatures]) -> list[RankedSkill]:
    counts = Counter(skill for feature_row in feature_rows for skill in feature_row.skills)
    return [
        RankedSkill(skill_name=skill_name, count=count) for skill_name, count in counts.most_common(_TOP_SKILLS_LIMIT)
    ]


def _top_tools(feature_rows: Sequence[PostingClusterFeatures]) -> list[RankedTool]:
    counts = Counter(tool for feature_row in feature_rows for tool in feature_row.tools)
    return [RankedTool(tool_name=tool_name, count=count) for tool_name, count in counts.most_common(_TOP_TOOLS_LIMIT)]


def _distinct_employer_ids(feature_rows: Sequence[PostingClusterFeatures]) -> list[str]:
    employer_ids: dict[str, str] = {}
    for feature_row in feature_rows:
        employer_id = feature_row.employer_id or feature_row.employer_name
        if not employer_id:
            continue
        employer_ids.setdefault(employer_id.casefold(), employer_id)
    return sorted(employer_ids.values(), key=str.casefold)


def _candidate_label(feature_rows: Sequence[PostingClusterFeatures]) -> str | None:
    if not feature_rows:
        return None
    counts = Counter(feature_row.title for feature_row in feature_rows)
    return counts.most_common(1)[0][0]


def _candidate_id(group_key: str, posting_ids: Sequence[str]) -> str:
    seed = f"{group_key}|{'|'.join(sorted(posting_ids))}"
    return f"emergence-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _dominant_cluster_skill_keys(
    clusters: Sequence[ClusterSummary],
    *,
    minimum_share: float,
) -> set[str]:
    if minimum_share <= 0.0:
        return {ranked_skill.skill_name.casefold() for cluster in clusters for ranked_skill in cluster.top_skills}

    return {
        ranked_skill.skill_name.casefold()
        for cluster in clusters
        for ranked_skill in cluster.top_skills
        if cluster.member_count > 0 and (ranked_skill.count / cluster.member_count) >= minimum_share
    }


def _novel_skill_count(
    feature_rows: Sequence[PostingClusterFeatures],
    existing_cluster_skill_keys: set[str],
) -> int:
    novel_skills = {
        skill.casefold()
        for feature_row in feature_rows
        for skill in feature_row.skills
        if skill.casefold() not in existing_cluster_skill_keys
    }
    return len(novel_skills)


def _noise_group_key(feature_row: PostingClusterFeatures, raw_cluster_label: int | None) -> str:
    if raw_cluster_label is not None and raw_cluster_label >= 0:
        return f"raw:{raw_cluster_label}"
    normalized_title = normalize_clustering_text_fragment(feature_row.title).casefold()
    return f"title:{normalized_title}"


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float | None:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0.0:
        return None
    return float(np.dot(left, right) / denominator)


def _nearest_cluster_id(
    clusters: Sequence[ClusterSummary],
    embedded_rows: Sequence[EmbeddedPostingText],
) -> str | None:
    if not clusters or not embedded_rows:
        return None

    candidate_matrix = np.asarray([row.embedding for row in embedded_rows], dtype=float)
    candidate_centroid = np.mean(candidate_matrix, axis=0)

    best_cluster_id: str | None = None
    best_similarity = float("-inf")

    for cluster in clusters:
        if not cluster.centroid_embedding:
            continue
        cluster_centroid = np.asarray(cluster.centroid_embedding, dtype=float)
        if cluster_centroid.shape != candidate_centroid.shape:
            continue
        similarity = _cosine_similarity(candidate_centroid, cluster_centroid)
        if similarity is None or similarity <= best_similarity:
            continue
        best_similarity = similarity
        best_cluster_id = cluster.cluster_id

    return best_cluster_id


def detect_emergence_candidates(
    result: ClusteringResult,
    features_rows: Sequence[PostingClusterFeatures],
    embedded_rows: Sequence[EmbeddedPostingText],
) -> list[EmergenceCandidate]:
    """Filter noise assignments into structured emergence candidates."""
    if result.skipped or not result.assignments:
        return []

    minimum_quality_score = emergence_min_quality_score()
    minimum_novel_skills = emergence_min_novel_skills()
    minimum_distinct_employers = emergence_min_distinct_employers()
    dominant_skill_share_threshold = cluster_label_dominance_threshold()

    feature_map = _feature_map(features_rows)
    embedded_map = _embedding_map(embedded_rows)
    existing_cluster_skill_keys = _dominant_cluster_skill_keys(
        result.clusters,
        minimum_share=dominant_skill_share_threshold,
    )

    grouped_rows: dict[str, list[tuple[PostingClusterFeatures, EmbeddedPostingText]]] = {}

    for assignment in result.assignments:
        if not assignment.is_noise:
            continue
        feature_row = feature_map.get(assignment.posting_id)
        embedded_row = embedded_map.get(assignment.posting_id)
        if feature_row is None or embedded_row is None:
            continue
        if feature_row.quality_score is None or feature_row.quality_score < minimum_quality_score:
            continue

        group_key = _noise_group_key(feature_row, assignment.raw_cluster_label)
        grouped_rows.setdefault(group_key, []).append((feature_row, embedded_row))

    candidates: list[EmergenceCandidate] = []

    for group_key in sorted(grouped_rows):
        rows = grouped_rows[group_key]
        feature_slice = [feature_row for feature_row, _embedded_row in rows]
        embedded_slice = [embedded_row for _feature_row, embedded_row in rows]
        employer_ids = _distinct_employer_ids(feature_slice)
        if len(employer_ids) < minimum_distinct_employers:
            continue

        novel_skill_count = _novel_skill_count(feature_slice, existing_cluster_skill_keys)
        if novel_skill_count < minimum_novel_skills:
            continue

        posting_ids = sorted(feature_row.posting_id for feature_row in feature_slice)
        candidates.append(
            EmergenceCandidate(
                candidate_id=_candidate_id(group_key, posting_ids),
                posting_ids=posting_ids,
                posting_count=len(posting_ids),
                candidate_role_label=_candidate_label(feature_slice),
                top_skills=_top_skills(feature_slice),
                top_tools=_top_tools(feature_slice),
                employer_ids=employer_ids,
                nearest_cluster_id=_nearest_cluster_id(result.clusters, embedded_slice),
                filter_reason=(
                    f"quality>={minimum_quality_score:.2f}; "
                    f"novel_skills>={minimum_novel_skills}; "
                    f"distinct_employers>={minimum_distinct_employers}"
                ),
            )
        )

    candidates.sort(key=lambda candidate: (-candidate.posting_count, candidate.candidate_id))
    log.info(
        "clustering_emergence_candidates_ready",
        candidate_count=len(candidates),
        minimum_quality_score=minimum_quality_score,
        minimum_novel_skills=minimum_novel_skills,
        minimum_distinct_employers=minimum_distinct_employers,
        dominant_skill_share_threshold=dominant_skill_share_threshold,
    )
    return candidates
