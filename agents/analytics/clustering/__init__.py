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
- ``CLUSTER_EMBEDDING_AUDIT_AGENT_NAME`` (default ``"analytics-clustering"``)
- ``EMERGENCE_MIN_QUALITY_SCORE`` (default ``0.70``)
- ``EMERGENCE_MIN_NOVEL_SKILLS`` (default ``3``)
- ``EMERGENCE_MIN_DISTINCT_EMPLOYERS`` (default ``2``)
"""

from agents.analytics.clustering.config import (
    DEFAULT_CLUSTER_DISTANCE_METRIC,
    DEFAULT_CLUSTER_EMBEDDING_AUDIT_AGENT_NAME,
    DEFAULT_CLUSTER_LABEL_DOMINANCE_THRESHOLD,
    DEFAULT_CLUSTER_MIN_CLUSTER_SIZE,
    DEFAULT_CLUSTER_MIN_SAMPLES,
    DEFAULT_CLUSTER_MIN_TOTAL_POSTINGS,
    DEFAULT_CLUSTER_SELECTION_EPSILON,
    DEFAULT_EMERGENCE_MIN_DISTINCT_EMPLOYERS,
    DEFAULT_EMERGENCE_MIN_NOVEL_SKILLS,
    DEFAULT_EMERGENCE_MIN_QUALITY_SCORE,
)
from agents.analytics.clustering.types import (
    ClusteredPosting,
    ClusteringResult,
    ClusterSummary,
    EmergenceCandidate,
    PostingClusterFeatures,
    RankedSkill,
    RankedTool,
)

__all__ = [
    "ClusterSummary",
    "ClusteredPosting",
    "ClusteringResult",
    "DEFAULT_CLUSTER_DISTANCE_METRIC",
    "DEFAULT_CLUSTER_EMBEDDING_AUDIT_AGENT_NAME",
    "DEFAULT_CLUSTER_LABEL_DOMINANCE_THRESHOLD",
    "DEFAULT_CLUSTER_MIN_CLUSTER_SIZE",
    "DEFAULT_CLUSTER_MIN_SAMPLES",
    "DEFAULT_CLUSTER_MIN_TOTAL_POSTINGS",
    "DEFAULT_CLUSTER_SELECTION_EPSILON",
    "DEFAULT_EMERGENCE_MIN_DISTINCT_EMPLOYERS",
    "DEFAULT_EMERGENCE_MIN_NOVEL_SKILLS",
    "DEFAULT_EMERGENCE_MIN_QUALITY_SCORE",
    "EmergenceCandidate",
    "PostingClusterFeatures",
    "RankedSkill",
    "RankedTool",
]
