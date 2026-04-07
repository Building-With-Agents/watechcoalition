"""Deterministic text composition for canonical role clustering embeddings."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable

from agents.analytics.clustering.types import PostingClusterFeatures, PreparedClusteringText

_SECTION_SEPARATOR = " || "
_LIST_SEPARATOR = " ; "
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def normalize_clustering_text_fragment(raw: str | None) -> str:
    """Normalize one text fragment without removing semantic casing."""
    text = unicodedata.normalize("NFKC", raw or "")
    text = _TAG_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def _stable_unique_strings(values: Iterable[str]) -> list[str]:
    normalized_by_key: dict[str, str] = {}
    for value in values:
        fragment = normalize_clustering_text_fragment(value)
        if not fragment:
            continue
        normalized_by_key.setdefault(fragment.casefold(), fragment)
    return sorted(normalized_by_key.values(), key=str.casefold)


def clustering_text_hash(normalized_clustering_text: str) -> str:
    """SHA-256 hex digest of the deterministic clustering text."""
    return hashlib.sha256(normalized_clustering_text.encode("utf-8")).hexdigest()


def build_clustering_text(features: PostingClusterFeatures) -> str:
    """Build deterministic embedding text from one posting's normalized feature row.

    Field order is fixed:
    1. title
    2. seniority
    3. skills
    4. tools
    5. responsibilities

    List-like sections are de-duplicated and sorted case-insensitively so
    upstream extraction ordering does not silently change clustering behavior.
    """
    sections: list[str] = [
        f"title: {normalize_clustering_text_fragment(features.title)}",
    ]

    seniority = normalize_clustering_text_fragment(features.seniority)
    if seniority:
        sections.append(f"seniority: {seniority}")

    skills = _stable_unique_strings(features.skills)
    if skills:
        sections.append(f"skills: {_LIST_SEPARATOR.join(skills)}")

    tools = _stable_unique_strings(features.tools)
    if tools:
        sections.append(f"tools: {_LIST_SEPARATOR.join(tools)}")

    responsibilities = _stable_unique_strings(features.responsibilities)
    if responsibilities:
        sections.append(f"responsibilities: {_LIST_SEPARATOR.join(responsibilities)}")

    return _SECTION_SEPARATOR.join(sections)


def build_clustering_texts(features_rows: Iterable[PostingClusterFeatures]) -> list[str]:
    """Build deterministic embedding texts for multiple postings."""
    return [build_clustering_text(features) for features in features_rows]


def prepare_clustering_text(features: PostingClusterFeatures) -> PreparedClusteringText:
    """Prepare one posting for embedding with a stable text hash."""
    text = build_clustering_text(features)
    return PreparedClusteringText(
        posting_id=features.posting_id,
        text=text,
        text_hash=clustering_text_hash(text),
    )


def prepare_clustering_texts(features_rows: Iterable[PostingClusterFeatures]) -> list[PreparedClusteringText]:
    """Prepare multiple postings for embedding with stable text hashes."""
    return [prepare_clustering_text(features) for features in features_rows]
