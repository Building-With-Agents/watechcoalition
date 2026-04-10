"""Embedding helpers for canonical role clustering."""

from __future__ import annotations

import os
from collections.abc import Sequence

import structlog

from agents.analytics.clustering.config import (
    DEFAULT_CLUSTER_EMBEDDING_AUDIT_AGENT_NAME,
    DEFAULT_CLUSTER_EMBEDDING_BATCH_SIZE,
)
from agents.analytics.clustering.text import prepare_clustering_texts
from agents.analytics.clustering.types import EmbeddedPostingText, PostingClusterFeatures, PreparedClusteringText
from agents.skills_extraction.extractors.taxonomy import _embed_texts_azure

log = structlog.get_logger()


def _embedding_batch_size() -> int:
    raw = os.getenv("CLUSTER_EMBEDDING_BATCH_SIZE", str(DEFAULT_CLUSTER_EMBEDDING_BATCH_SIZE))
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_CLUSTER_EMBEDDING_BATCH_SIZE
    return parsed if parsed > 0 else DEFAULT_CLUSTER_EMBEDDING_BATCH_SIZE


def _embedding_audit_agent_name() -> str:
    raw = os.getenv("CLUSTER_EMBEDDING_AUDIT_AGENT_NAME", DEFAULT_CLUSTER_EMBEDDING_AUDIT_AGENT_NAME)
    normalized = raw.strip()
    return normalized or DEFAULT_CLUSTER_EMBEDDING_AUDIT_AGENT_NAME


def embed_prepared_clustering_texts(
    prepared_rows: Sequence[PreparedClusteringText],
    *,
    audit_agent_name: str | None = None,
    batch_size: int | None = None,
    allow_partial: bool = False,
) -> list[EmbeddedPostingText] | None:
    """Embed prepared clustering texts using the shared Azure embedding helper.

    Returns ``None`` when a batch fails and ``allow_partial`` is false.
    When ``allow_partial`` is true, failed batches are skipped and successful
    batches are returned.
    """
    if not prepared_rows:
        return []

    effective_batch_size = batch_size if batch_size is not None else _embedding_batch_size()
    if effective_batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    effective_audit_agent_name = audit_agent_name or _embedding_audit_agent_name()
    embedded_rows: list[EmbeddedPostingText] = []

    for start in range(0, len(prepared_rows), effective_batch_size):
        chunk = list(prepared_rows[start : start + effective_batch_size])
        vectors = _embed_texts_azure(
            [item.text for item in chunk],
            audit_agent_name=effective_audit_agent_name,
        )
        if vectors is None or len(vectors) != len(chunk):
            log.warning(
                "clustering_embedding_chunk_failed",
                chunk_start=start,
                chunk_size=len(chunk),
                requested_posting_count=len(prepared_rows),
                allow_partial=allow_partial,
            )
            if allow_partial:
                continue
            return None

        for item, vector in zip(chunk, vectors, strict=True):
            if not vector:
                log.warning(
                    "clustering_embedding_vector_missing",
                    posting_id=item.posting_id,
                    text_hash=item.text_hash,
                )
                if allow_partial:
                    continue
                return None
            embedded_rows.append(
                EmbeddedPostingText(
                    posting_id=item.posting_id,
                    text=item.text,
                    text_hash=item.text_hash,
                    embedding=[float(value) for value in vector],
                )
            )

    log.info(
        "clustering_embeddings_ready",
        requested_posting_count=len(prepared_rows),
        embedded_posting_count=len(embedded_rows),
        batch_size=effective_batch_size,
        allow_partial=allow_partial,
    )
    return embedded_rows


def embed_posting_features(
    features_rows: Sequence[PostingClusterFeatures],
    *,
    audit_agent_name: str | None = None,
    batch_size: int | None = None,
    allow_partial: bool = False,
) -> list[EmbeddedPostingText] | None:
    """Prepare and embed posting feature rows in one call."""
    prepared_rows = prepare_clustering_texts(features_rows)
    return embed_prepared_clustering_texts(
        prepared_rows,
        audit_agent_name=audit_agent_name,
        batch_size=batch_size,
        allow_partial=allow_partial,
    )
