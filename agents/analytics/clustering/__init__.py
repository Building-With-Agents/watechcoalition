"""Canonical role clustering package for Analytics step 4.

Bryan owns the pure clustering logic in this package. Emilio wires its outputs
into the Analytics Agent, database models, and event flow.

Production guidelines:
- Keep functions pure where possible.
- Log counts, ids, and cluster metadata only; never log raw descriptions.
- Reuse the shared Azure embedding path with a dedicated audit agent name.

Environment variables consumed by later modules in this package:
- ``CLUSTER_MIN_TOTAL_POSTINGS`` (default ``500``)
- ``CLUSTER_MIN_CLUSTER_SIZE`` (default ``10``)
- ``CLUSTER_MIN_SAMPLES`` (default ``5``)
- ``CLUSTER_SELECTION_EPSILON`` (default ``0.0``)
- ``CLUSTER_DISTANCE_METRIC`` (default ``"euclidean"``)
- ``CLUSTER_LABEL_DOMINANCE_THRESHOLD`` (default ``0.30``)
- ``CLUSTER_EMBEDDING_BATCH_SIZE`` (default ``50``)
- ``CLUSTER_EMBEDDING_AUDIT_AGENT_NAME`` (default ``"analytics-clustering"``)
- ``EMERGENCE_MIN_QUALITY_SCORE`` (default ``0.70``)
- ``EMERGENCE_MIN_NOVEL_SKILLS`` (default ``3``)
- ``EMERGENCE_MIN_DISTINCT_EMPLOYERS`` (default ``2``)
"""

from agents.analytics.clustering.config import (
    DEFAULT_CLUSTER_DISTANCE_METRIC,
    DEFAULT_CLUSTER_EMBEDDING_AUDIT_AGENT_NAME,
    DEFAULT_CLUSTER_EMBEDDING_BATCH_SIZE,
    DEFAULT_CLUSTER_LABEL_DOMINANCE_THRESHOLD,
    DEFAULT_CLUSTER_MIN_CLUSTER_SIZE,
    DEFAULT_CLUSTER_MIN_SAMPLES,
    DEFAULT_CLUSTER_MIN_TOTAL_POSTINGS,
    DEFAULT_CLUSTER_SELECTION_EPSILON,
    DEFAULT_EMERGENCE_MIN_DISTINCT_EMPLOYERS,
    DEFAULT_EMERGENCE_MIN_NOVEL_SKILLS,
    DEFAULT_EMERGENCE_MIN_QUALITY_SCORE,
    cluster_distance_metric,
    cluster_min_cluster_size,
    cluster_min_samples,
    cluster_min_total_postings,
    cluster_selection_epsilon,
)
from agents.analytics.clustering.embeddings import (
    embed_posting_features,
    embed_prepared_clustering_texts,
)
from agents.analytics.clustering.pipeline import run_clustering
from agents.analytics.clustering.text import (
    build_clustering_text,
    build_clustering_texts,
    clustering_text_hash,
    prepare_clustering_text,
    prepare_clustering_texts,
)
from agents.analytics.clustering.types import (
    ClusteredPosting,
    ClusteringResult,
    ClusterSummary,
    EmbeddedPostingText,
    EmergenceCandidate,
    PostingClusterFeatures,
    PreparedClusteringText,
    RankedSkill,
    RankedTool,
)

__all__ = [
    "build_clustering_text",
    "build_clustering_texts",
    "cluster_distance_metric",
    "cluster_min_cluster_size",
    "cluster_min_samples",
    "cluster_min_total_postings",
    "cluster_selection_epsilon",
    "ClusterSummary",
    "ClusteredPosting",
    "ClusteringResult",
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
    "embed_posting_features",
    "embed_prepared_clustering_texts",
    "EmbeddedPostingText",
    "EmergenceCandidate",
    "PostingClusterFeatures",
    "PreparedClusteringText",
    "prepare_clustering_text",
    "prepare_clustering_texts",
    "RankedSkill",
    "RankedTool",
    "run_clustering",
    "clustering_text_hash",
]
