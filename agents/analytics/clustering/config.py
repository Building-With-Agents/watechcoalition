"""Configuration defaults for canonical role clustering."""

from __future__ import annotations

import os

DEFAULT_CLUSTER_EMBEDDING_BATCH_SIZE = 50
DEFAULT_CLUSTER_MIN_TOTAL_POSTINGS = 500
DEFAULT_CLUSTER_MIN_CLUSTER_SIZE = 10
DEFAULT_CLUSTER_MIN_SAMPLES = 5
DEFAULT_CLUSTER_SELECTION_EPSILON = 0.0
DEFAULT_CLUSTER_DISTANCE_METRIC = "euclidean"
DEFAULT_CLUSTER_LABEL_DOMINANCE_THRESHOLD = 0.30
DEFAULT_CLUSTER_EMBEDDING_AUDIT_AGENT_NAME = "analytics-clustering"

DEFAULT_EMERGENCE_MIN_QUALITY_SCORE = 0.70
DEFAULT_EMERGENCE_MIN_NOVEL_SKILLS = 3
DEFAULT_EMERGENCE_MIN_DISTINCT_EMPLOYERS = 2


def _int_from_env(name: str, default: int, *, minimum: int = 1) -> int:
    raw = os.getenv(name, str(default))
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= minimum else default


def _float_from_env(
    name: str,
    default: float,
    *,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> float:
    raw = os.getenv(name, str(default))
    try:
        parsed = float(raw)
    except (TypeError, ValueError):
        return default
    if parsed < minimum:
        return default
    if maximum is not None and parsed > maximum:
        return default
    return parsed


def cluster_min_total_postings() -> int:
    return _int_from_env("CLUSTER_MIN_TOTAL_POSTINGS", DEFAULT_CLUSTER_MIN_TOTAL_POSTINGS)


def cluster_min_cluster_size() -> int:
    return _int_from_env("CLUSTER_MIN_CLUSTER_SIZE", DEFAULT_CLUSTER_MIN_CLUSTER_SIZE)


def cluster_min_samples() -> int:
    return _int_from_env("CLUSTER_MIN_SAMPLES", DEFAULT_CLUSTER_MIN_SAMPLES)


def cluster_selection_epsilon() -> float:
    return _float_from_env("CLUSTER_SELECTION_EPSILON", DEFAULT_CLUSTER_SELECTION_EPSILON, minimum=0.0)


def cluster_distance_metric() -> str:
    raw = os.getenv("CLUSTER_DISTANCE_METRIC", DEFAULT_CLUSTER_DISTANCE_METRIC)
    normalized = raw.strip().lower()
    return normalized or DEFAULT_CLUSTER_DISTANCE_METRIC


def cluster_label_dominance_threshold() -> float:
    return _float_from_env(
        "CLUSTER_LABEL_DOMINANCE_THRESHOLD",
        DEFAULT_CLUSTER_LABEL_DOMINANCE_THRESHOLD,
        minimum=0.0,
        maximum=1.0,
    )


def emergence_min_quality_score() -> float:
    return _float_from_env(
        "EMERGENCE_MIN_QUALITY_SCORE",
        DEFAULT_EMERGENCE_MIN_QUALITY_SCORE,
        minimum=0.0,
        maximum=1.0,
    )


def emergence_min_novel_skills() -> int:
    return _int_from_env("EMERGENCE_MIN_NOVEL_SKILLS", DEFAULT_EMERGENCE_MIN_NOVEL_SKILLS)


def emergence_min_distinct_employers() -> int:
    return _int_from_env(
        "EMERGENCE_MIN_DISTINCT_EMPLOYERS",
        DEFAULT_EMERGENCE_MIN_DISTINCT_EMPLOYERS,
    )


__all__ = [
    "cluster_distance_metric",
    "cluster_label_dominance_threshold",
    "cluster_min_cluster_size",
    "cluster_min_samples",
    "cluster_min_total_postings",
    "cluster_selection_epsilon",
    "DEFAULT_CLUSTER_DISTANCE_METRIC",
    "DEFAULT_CLUSTER_EMBEDDING_BATCH_SIZE",
    "DEFAULT_CLUSTER_EMBEDDING_AUDIT_AGENT_NAME",
    "DEFAULT_CLUSTER_LABEL_DOMINANCE_THRESHOLD",
    "DEFAULT_CLUSTER_MIN_CLUSTER_SIZE",
    "DEFAULT_CLUSTER_MIN_SAMPLES",
    "DEFAULT_CLUSTER_MIN_TOTAL_POSTINGS",
    "DEFAULT_CLUSTER_SELECTION_EPSILON",
    "DEFAULT_EMERGENCE_MIN_DISTINCT_EMPLOYERS",
    "DEFAULT_EMERGENCE_MIN_NOVEL_SKILLS",
    "DEFAULT_EMERGENCE_MIN_QUALITY_SCORE",
    "emergence_min_distinct_employers",
    "emergence_min_novel_skills",
    "emergence_min_quality_score",
]
