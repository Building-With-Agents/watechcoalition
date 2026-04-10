from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any

import numpy as np
import pytest

from agents.analytics.clustering.embeddings import embed_prepared_clustering_texts
from agents.analytics.clustering.emergence import detect_emergence_candidates
from agents.analytics.clustering.labeling import label_clusters
from agents.analytics.clustering.pipeline import run_clustering, run_clustering_pipeline
from agents.analytics.clustering.text import build_clustering_text, clustering_text_hash
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


def _make_feature(
    posting_id: str,
    *,
    title: str,
    skills: Sequence[str] = (),
    tools: Sequence[str] = (),
    responsibilities: Sequence[str] = (),
    seniority: str | None = None,
    employer_id: str | None = None,
    employer_name: str | None = None,
    quality_score: float | None = None,
) -> PostingClusterFeatures:
    return PostingClusterFeatures(
        posting_id=posting_id,
        title=title,
        skills=list(skills),
        tools=list(tools),
        responsibilities=list(responsibilities),
        seniority=seniority,
        employer_id=employer_id,
        employer_name=employer_name,
        quality_score=quality_score,
    )


def _make_prepared(posting_id: str, text: str) -> PreparedClusteringText:
    return PreparedClusteringText(
        posting_id=posting_id,
        text=text,
        text_hash=clustering_text_hash(text),
    )


def _make_embedded(posting_id: str, embedding: Sequence[float]) -> EmbeddedPostingText:
    text = f"title: {posting_id}"
    return EmbeddedPostingText(
        posting_id=posting_id,
        text=text,
        text_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        embedding=list(embedding),
    )


def _make_cluster_summary(
    cluster_id: str,
    *,
    raw_cluster_label: int,
    member_posting_ids: Sequence[str],
    representative_titles: Sequence[str],
    top_skills: Sequence[tuple[str, int]] = (),
    top_tools: Sequence[tuple[str, int]] = (),
    centroid_embedding: Sequence[float] | None = None,
) -> ClusterSummary:
    return ClusterSummary(
        cluster_id=cluster_id,
        raw_cluster_label=raw_cluster_label,
        member_posting_ids=list(member_posting_ids),
        member_count=len(member_posting_ids),
        representative_titles=list(representative_titles),
        top_skills=[RankedSkill(skill_name=name, count=count) for name, count in top_skills],
        top_tools=[RankedTool(tool_name=name, count=count) for name, count in top_tools],
        centroid_embedding=list(centroid_embedding) if centroid_embedding is not None else None,
    )


class _FakeClusterer:
    def __init__(
        self,
        labels: Sequence[int],
        *,
        probabilities: Sequence[float] | None = None,
    ) -> None:
        self._labels = np.asarray(labels)
        self.probabilities_ = (
            np.asarray(probabilities, dtype=float) if probabilities is not None else np.ones(len(labels), dtype=float)
        )

    def fit_predict(self, matrix: np.ndarray) -> np.ndarray:
        assert matrix.ndim == 2
        return self._labels


def test_build_clustering_text_normalizes_and_orders_sections() -> None:
    features = _make_feature(
        "posting-1",
        title="  Senior Data Engineer  ",
        seniority=" Mid  ",
        skills=["SQL", "python", "Python", " sql "],
        tools=[" dbt ", "Airflow", "airflow"],
        responsibilities=[" Build pipelines ", "<p>Mentor team</p>", "build pipelines"],
    )

    text = build_clustering_text(features)

    assert text == (
        "title: Senior Data Engineer || "
        "seniority: Mid || "
        "skills: python ; SQL || "
        "tools: Airflow ; dbt || "
        "responsibilities: Build pipelines ; Mentor team"
    )
    assert clustering_text_hash(text) == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_embed_prepared_clustering_texts_batches_and_preserves_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared_rows = [
        _make_prepared("posting-1", "title: data engineer"),
        _make_prepared("posting-2", "title: analytics engineer"),
        _make_prepared("posting-3", "title: ml engineer"),
    ]
    calls: list[tuple[list[str], str]] = []

    def fake_embed_texts(texts: list[str], *, audit_agent_name: str) -> list[list[float]]:
        calls.append((list(texts), audit_agent_name))
        return [[float(index + 1), float(index + 2)] for index in range(len(texts))]

    monkeypatch.setattr(
        "agents.analytics.clustering.embeddings._embed_texts_azure",
        fake_embed_texts,
    )

    embedded_rows = embed_prepared_clustering_texts(
        prepared_rows,
        audit_agent_name="analytics-clustering-test",
        batch_size=2,
    )

    assert embedded_rows is not None
    assert [row.posting_id for row in embedded_rows] == ["posting-1", "posting-2", "posting-3"]
    assert [row.text_hash for row in embedded_rows] == [row.text_hash for row in prepared_rows]
    assert calls == [
        (["title: data engineer", "title: analytics engineer"], "analytics-clustering-test"),
        (["title: ml engineer"], "analytics-clustering-test"),
    ]


def test_embed_prepared_clustering_texts_allow_partial_skips_failed_batches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared_rows = [
        _make_prepared("posting-1", "title: data engineer"),
        _make_prepared("posting-2", "title: analytics engineer"),
        _make_prepared("posting-3", "title: ml engineer"),
    ]
    call_count = {"count": 0}

    def fake_embed_texts(texts: list[str], *, audit_agent_name: str) -> list[list[float]] | None:
        del texts, audit_agent_name
        call_count["count"] += 1
        if call_count["count"] == 2:
            return None
        return [[1.0, 0.0], [0.0, 1.0]]

    monkeypatch.setattr(
        "agents.analytics.clustering.embeddings._embed_texts_azure",
        fake_embed_texts,
    )

    embedded_rows = embed_prepared_clustering_texts(
        prepared_rows,
        batch_size=2,
        allow_partial=True,
    )

    assert embedded_rows is not None
    assert [row.posting_id for row in embedded_rows] == ["posting-1", "posting-2"]


def test_run_clustering_skips_when_total_postings_below_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLUSTER_MIN_TOTAL_POSTINGS", "5")

    features_rows = [
        _make_feature("posting-1", title="Data Engineer"),
        _make_feature("posting-2", title="Analytics Engineer"),
        _make_feature("posting-3", title="ML Engineer"),
        _make_feature("posting-4", title="Platform Engineer"),
    ]
    embedded_rows = [
        _make_embedded("posting-1", [1.0, 0.0]),
        _make_embedded("posting-2", [0.0, 1.0]),
        _make_embedded("posting-3", [1.0, 1.0]),
        _make_embedded("posting-4", [0.5, 0.5]),
    ]

    result = run_clustering(features_rows, embedded_rows)

    assert result.skipped is True
    assert result.skip_reason == "insufficient_total_postings"
    assert result.clusters == []
    assert result.assignments == []


def test_run_clustering_builds_cluster_summaries_with_fake_clusterer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLUSTER_MIN_TOTAL_POSTINGS", "4")
    monkeypatch.setenv("CLUSTER_MIN_CLUSTER_SIZE", "2")
    monkeypatch.setenv("CLUSTER_MIN_SAMPLES", "1")
    monkeypatch.setenv("CLUSTER_SELECTION_EPSILON", "0.15")
    monkeypatch.setenv("CLUSTER_DISTANCE_METRIC", "cosine")

    features_rows = [
        _make_feature("posting-1", title="Data Engineer", skills=["Python", "SQL"], tools=["dbt"]),
        _make_feature("posting-2", title="Data Engineer", skills=["Python"], tools=["dbt", "Airflow"]),
        _make_feature("posting-3", title="ML Engineer", skills=["PyTorch"], tools=["Docker"]),
        _make_feature("posting-4", title="ML Engineer", skills=["PyTorch", "Python"], tools=["Docker"]),
    ]
    embedded_rows = [
        _make_embedded("posting-1", [1.0, 0.0]),
        _make_embedded("posting-2", [1.0, 0.1]),
        _make_embedded("posting-3", [0.0, 1.0]),
        _make_embedded("posting-4", [0.1, 1.0]),
    ]
    captured_kwargs: dict[str, Any] = {}

    def clusterer_factory(**kwargs: Any) -> _FakeClusterer:
        captured_kwargs.update(kwargs)
        return _FakeClusterer(
            [0, 0, 1, 1],
            probabilities=[0.91, 0.87, 0.79, 0.74],
        )

    result = run_clustering(
        features_rows,
        embedded_rows,
        clusterer_factory=clusterer_factory,
    )

    assert result.skipped is False
    assert result.clustered_posting_count == 4
    assert result.noise_posting_count == 0
    assert [cluster.cluster_id for cluster in result.clusters] == ["cluster-0001", "cluster-0002"]
    assert result.clusters[0].representative_titles == ["Data Engineer"]
    assert result.clusters[0].top_skills[0].skill_name == "Python"
    assert result.clusters[0].top_skills[0].count == 2
    assert result.clusters[0].centroid_embedding == pytest.approx([1.0, 0.05])
    assert [assignment.cluster_id for assignment in result.assignments] == [
        "cluster-0001",
        "cluster-0001",
        "cluster-0002",
        "cluster-0002",
    ]
    assert captured_kwargs == {
        "min_cluster_size": 2,
        "min_samples": 1,
        "cluster_selection_epsilon": 0.15,
        "metric": "cosine",
    }


def test_label_clusters_uses_dominant_title_llm_and_fallback() -> None:
    result = ClusteringResult(
        assignments=[
            ClusteredPosting(posting_id="posting-1", cluster_id="cluster-0001", raw_cluster_label=0),
            ClusteredPosting(posting_id="posting-2", cluster_id="cluster-0001", raw_cluster_label=0),
            ClusteredPosting(posting_id="posting-3", cluster_id="cluster-0001", raw_cluster_label=0),
            ClusteredPosting(posting_id="posting-4", cluster_id="cluster-0002", raw_cluster_label=1),
            ClusteredPosting(posting_id="posting-5", cluster_id="cluster-0002", raw_cluster_label=1),
            ClusteredPosting(posting_id="posting-6", cluster_id="cluster-0003", raw_cluster_label=2),
        ],
        clusters=[
            _make_cluster_summary(
                "cluster-0001",
                raw_cluster_label=0,
                member_posting_ids=["posting-1", "posting-2", "posting-3"],
                representative_titles=["Data Engineer", "Analytics Engineer"],
                top_skills=[("Python", 3), ("SQL", 2)],
                top_tools=[("dbt", 2)],
            ),
            _make_cluster_summary(
                "cluster-0002",
                raw_cluster_label=1,
                member_posting_ids=["posting-4", "posting-5"],
                representative_titles=["AI Platform Engineer", "ML Infrastructure Engineer"],
                top_skills=[("PyTorch", 2), ("Kubernetes", 2)],
                top_tools=[("Docker", 2)],
            ),
            _make_cluster_summary(
                "cluster-0003",
                raw_cluster_label=2,
                member_posting_ids=["posting-6"],
                representative_titles=["Emerging Role Analyst"],
                top_skills=[],
                top_tools=[],
            ),
        ],
        total_input_postings=6,
        eligible_posting_count=6,
        clustered_posting_count=6,
        noise_posting_count=0,
    )
    features_rows = [
        _make_feature("posting-1", title="Data Engineer", skills=["Python", "SQL"], tools=["dbt"]),
        _make_feature("posting-2", title="Data Engineer", skills=["Python"], tools=["dbt"]),
        _make_feature("posting-3", title="Analytics Engineer", skills=["SQL"], tools=["Airflow"]),
        _make_feature("posting-4", title="AI Platform Engineer", skills=["PyTorch"], tools=["Docker"]),
        _make_feature("posting-5", title="ML Infrastructure Engineer", skills=["Kubernetes"], tools=["Docker"]),
    ]

    def llm_labeler(cluster: ClusterSummary, feature_rows: Sequence[PostingClusterFeatures]) -> str | None:
        del feature_rows
        if cluster.cluster_id == "cluster-0002":
            return "ML Platform Engineer"
        return None

    labeled_result = label_clusters(
        result,
        features_rows,
        llm_labeler=llm_labeler,
        dominance_threshold=0.6,
    )

    cluster_by_id = {cluster.cluster_id: cluster for cluster in labeled_result.clusters}
    assert cluster_by_id["cluster-0001"].label == "Data Engineer"
    assert cluster_by_id["cluster-0001"].label_source == "dominant_title"
    assert "Common skills include Python, SQL" in (cluster_by_id["cluster-0001"].description or "")

    assert cluster_by_id["cluster-0002"].label == "ML Platform Engineer"
    assert cluster_by_id["cluster-0002"].label_source == "llm"
    assert cluster_by_id["cluster-0002"].is_llm_generated_label is True

    assert cluster_by_id["cluster-0003"].label == "Emerging Role Analyst"
    assert cluster_by_id["cluster-0003"].label_source == "fallback"

    assert [assignment.cluster_label for assignment in labeled_result.assignments] == [
        "Data Engineer",
        "Data Engineer",
        "Data Engineer",
        "ML Platform Engineer",
        "ML Platform Engineer",
        "Emerging Role Analyst",
    ]


def test_detect_emergence_candidates_uses_dominant_cluster_skills(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLUSTER_LABEL_DOMINANCE_THRESHOLD", "0.3")
    monkeypatch.setenv("EMERGENCE_MIN_QUALITY_SCORE", "0.7")
    monkeypatch.setenv("EMERGENCE_MIN_NOVEL_SKILLS", "3")
    monkeypatch.setenv("EMERGENCE_MIN_DISTINCT_EMPLOYERS", "2")

    result = ClusteringResult(
        assignments=[
            *[
                ClusteredPosting(
                    posting_id=f"existing-{index}",
                    cluster_id="cluster-0001",
                    raw_cluster_label=0,
                )
                for index in range(10)
            ],
            ClusteredPosting(posting_id="candidate-1", cluster_id=None, raw_cluster_label=-1, is_noise=True),
            ClusteredPosting(posting_id="candidate-2", cluster_id=None, raw_cluster_label=-1, is_noise=True),
        ],
        clusters=[
            _make_cluster_summary(
                "cluster-0001",
                raw_cluster_label=0,
                member_posting_ids=[f"existing-{index}" for index in range(10)],
                representative_titles=["Software Engineer"],
                top_skills=[("Python", 9), ("SQL", 2)],
                top_tools=[("Docker", 6)],
                centroid_embedding=[1.0, 0.0, 0.0],
            )
        ],
        total_input_postings=12,
        eligible_posting_count=12,
        clustered_posting_count=10,
        noise_posting_count=2,
    )
    features_rows = [
        _make_feature(
            "candidate-1",
            title="AI Workflow Engineer",
            skills=["SQL", "Graph RAG", "LLMOps", "Vector DB"],
            tools=["LangChain", "Docker"],
            employer_id="employer-a",
            quality_score=0.92,
        ),
        _make_feature(
            "candidate-2",
            title="AI Workflow Engineer",
            skills=["SQL", "LLMOps", "Vector DB", "Agentic Systems"],
            tools=["LangChain", "Docker"],
            employer_id="employer-b",
            quality_score=0.9,
        ),
    ]
    embedded_rows = [
        _make_embedded("candidate-1", [0.95, 0.05, 0.0]),
        _make_embedded("candidate-2", [0.9, 0.1, 0.0]),
    ]

    candidates = detect_emergence_candidates(result, features_rows, embedded_rows)

    assert candidates == [
        EmergenceCandidate(
            candidate_id=candidates[0].candidate_id,
            posting_ids=["candidate-1", "candidate-2"],
            posting_count=2,
            candidate_role_label="AI Workflow Engineer",
            top_skills=[
                RankedSkill(skill_name="SQL", count=2),
                RankedSkill(skill_name="LLMOps", count=2),
                RankedSkill(skill_name="Vector DB", count=2),
                RankedSkill(skill_name="Graph RAG", count=1),
                RankedSkill(skill_name="Agentic Systems", count=1),
            ],
            top_tools=[
                RankedTool(tool_name="LangChain", count=2),
                RankedTool(tool_name="Docker", count=2),
            ],
            employer_ids=["employer-a", "employer-b"],
            nearest_cluster_id="cluster-0001",
            filter_reason="quality>=0.70; novel_skills>=3; distinct_employers>=2",
        )
    ]
    assert candidates[0].candidate_id.startswith("emergence-")


def test_run_clustering_pipeline_applies_labels_and_emergence_filters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLUSTER_MIN_TOTAL_POSTINGS", "5")
    monkeypatch.setenv("CLUSTER_MIN_CLUSTER_SIZE", "2")
    monkeypatch.setenv("CLUSTER_MIN_SAMPLES", "1")
    monkeypatch.setenv("EMERGENCE_MIN_QUALITY_SCORE", "0.7")
    monkeypatch.setenv("EMERGENCE_MIN_NOVEL_SKILLS", "3")
    monkeypatch.setenv("EMERGENCE_MIN_DISTINCT_EMPLOYERS", "2")

    features_rows = [
        _make_feature(
            "posting-1",
            title="Data Engineer",
            skills=["Python", "SQL"],
            tools=["dbt"],
            employer_id="employer-a",
            quality_score=0.88,
        ),
        _make_feature(
            "posting-2",
            title="Data Engineer",
            skills=["Python", "SQL"],
            tools=["Airflow"],
            employer_id="employer-b",
            quality_score=0.86,
        ),
        _make_feature(
            "posting-3",
            title="Analytics Engineer",
            skills=["Python", "SQL"],
            tools=["dbt"],
            employer_id="employer-c",
            quality_score=0.87,
        ),
        _make_feature(
            "posting-4",
            title="AI Workflow Engineer",
            skills=["Graph RAG", "LLMOps", "Vector DB"],
            tools=["LangChain"],
            employer_id="employer-d",
            quality_score=0.95,
        ),
        _make_feature(
            "posting-5",
            title="AI Workflow Engineer",
            skills=["Graph RAG", "LLMOps", "Agentic Systems"],
            tools=["LangChain"],
            employer_id="employer-e",
            quality_score=0.96,
        ),
    ]
    embedded_rows = [
        _make_embedded("posting-1", [1.0, 0.0]),
        _make_embedded("posting-2", [0.95, 0.05]),
        _make_embedded("posting-3", [0.9, 0.1]),
        _make_embedded("posting-4", [0.1, 0.9]),
        _make_embedded("posting-5", [0.05, 0.95]),
    ]

    def clusterer_factory(**kwargs: Any) -> _FakeClusterer:
        del kwargs
        return _FakeClusterer([0, 0, 0, -1, -1], probabilities=[0.9, 0.86, 0.83, 0.2, 0.18])

    result = run_clustering_pipeline(
        features_rows,
        embedded_rows,
        clusterer_factory=clusterer_factory,
        allow_llm_fallback=False,
    )

    assert result.skipped is False
    assert [cluster.label for cluster in result.clusters] == ["Data Engineer"]
    assert result.emergence_candidates[0].candidate_role_label == "AI Workflow Engineer"
    assert result.emergence_candidates[0].posting_ids == ["posting-4", "posting-5"]
