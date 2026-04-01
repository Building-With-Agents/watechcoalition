"""Embedding vectors: L2-normalize and parse pgvector text for fuzzy dedup."""

from __future__ import annotations

import json
from typing import Any

import numpy as np


def l2_normalize(vec: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(vec))
    if n == 0.0:
        return vec
    return vec / n


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity after L2 normalization (dot product)."""
    aa = l2_normalize(a.astype(np.float64, copy=False))
    bb = l2_normalize(b.astype(np.float64, copy=False))
    return float(np.dot(aa, bb))


def vector_to_pg_cast_param(vec: list[float]) -> str:
    """JSON array string for PostgreSQL ``CAST(:x AS vector)`` (matches seed_esco_embeddings)."""
    return json.dumps(vec)


def parse_stored_embedding(value: Any) -> np.ndarray | None:
    """
    Parse value from ``dedup_embedding`` (pgvector text, list, or None).

    PostgreSQL often returns ``str`` like ``[0.1,0.2,...]`` for vector::text.
    """
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        return value.astype(np.float64, copy=False)
    if isinstance(value, (list, tuple)):
        try:
            return np.asarray([float(x) for x in value], dtype=np.float64)
        except (TypeError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            arr = json.loads(s)
            if isinstance(arr, list):
                return np.asarray([float(x) for x in arr], dtype=np.float64)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        if s.startswith("[") and s.endswith("]"):
            try:
                inner = s[1:-1]
                if not inner.strip():
                    return None
                parts = [p.strip() for p in inner.split(",")]
                return np.asarray([float(p) for p in parts], dtype=np.float64)
            except (TypeError, ValueError):
                return None
    return None
