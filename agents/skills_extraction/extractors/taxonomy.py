"""Taxonomy resolution — 6-step linking pipeline.

Links extracted skill labels to the ESCO digital skills taxonomy using a
strict 6-step resolution order:
  1. Exact match → GenAI Extension Layer (10 predefined AI-era skills)
  2. Exact match → ESCO digital skills cluster
  3. Normalized match → ESCO digital skills cluster
  4. Embedding cosine similarity >= 0.92 → ESCO
  5. O*NET occupation code match
  6. Emit as raw_skill with esco_uri = null (Enrichment resolves in Phase 2)

Week 4 implementation (Angel + Fabian):
- Set up ESCO digital skills store (Decision #36)
- Build GenAI Extension Layer lookup table (10 skills → ESCO parent clusters)
- Implement resolve_taxonomy() with 6-step order
- Implement resolve_taxonomy_batch() with shared embedding computations
- Track per-step resolution statistics

Reference: ARCHITECTURE_DEEP.md § 6-Step Taxonomy Resolution.
"""

from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import structlog

from agents.common.types import TaxonomyResult

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Paths and config
# ---------------------------------------------------------------------------

_TAXONOMY_DIR = Path(__file__).parent.parent / "taxonomy"
_DEFAULT_ESCO_JSON = _TAXONOMY_DIR / "esco_digital_skills.json"
_DEFAULT_GENAI_EXTENSION_JSON = _TAXONOMY_DIR / "genai_extension.json"
_DEFAULT_ONET_SKILLS_PATH = _TAXONOMY_DIR / "onet_skills.txt"

# Alias map: ARCHITECTURE_DEEP parent cluster name (normalized) → ESCO broader_concept label as it appears in data
_PARENT_LABEL_ALIASES: dict[str, str] = {
    "digital content creation": "create digital content",
    "software architecture": "designing ict systems or applications",  # define software architecture has this parent
    "database management": "manage database",
}

# ---------------------------------------------------------------------------
# Normalization (matches seed_esco.normalize_text)
# ---------------------------------------------------------------------------


def _normalize_label(value: str | None) -> str:
    """NFKC, lowercase, strip, collapse internal whitespace."""
    text = unicodedata.normalize("NFKC", value or "")
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------------------------------
# ESCO store and GenAI extension loading
# ---------------------------------------------------------------------------


def _load_esco_store(json_path: Path | None = None) -> list[dict[str, Any]]:
    """Load ESCO digital skills from JSON. Returns list of skill records."""
    path = json_path or _DEFAULT_ESCO_JSON
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _build_parent_label_to_uri(records: list[dict[str, Any]]) -> dict[str, str]:
    """Build map: normalized parent cluster label → one ESCO broader concept URI."""
    out: dict[str, str] = {}
    for rec in records:
        labels = rec.get("broader_concept_labels") or []
        uris = rec.get("broader_concept_uris") or []
        for label, uri in zip(labels, uris, strict=True):
            if label and uri:
                key = _normalize_label(label)
                if key not in out:
                    out[key] = uri.strip()
    # Apply aliases so GenAI parent names resolve
    for arch_name, esco_name in _PARENT_LABEL_ALIASES.items():
        key = _normalize_label(arch_name)
        alias_key = _normalize_label(esco_name)
        if key not in out and alias_key in out:
            out[key] = out[alias_key]
    return out


def _load_genai_extension(json_path: Path | None = None) -> dict[str, str]:
    """Load GenAI skill name → ESCO parent cluster label. Keys are as in ARCHITECTURE_DEEP."""
    path = json_path or _DEFAULT_GENAI_EXTENSION_JSON
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# O*NET store loading (Step 5)
# ---------------------------------------------------------------------------

_onet_normalized_to_pair: dict[str, tuple[str, str]] | None = None


def _load_onet_store(path: Path | None = None) -> dict[str, tuple[str, str]]:
    """Load O*NET Skills tab-delimited file; return normalized_name -> (element_id, element_name).

    File format: O*NET 25.0 Text Skills (13 columns). Uses Element ID and Element Name.
    First occurrence wins for duplicates. If file is missing or empty, returns {}.
    """
    p = path or _DEFAULT_ONET_SKILLS_PATH
    if not p.exists():
        return {}
    out: dict[str, tuple[str, str]] = {}
    try:
        with p.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter="\t")
            header = next(reader, None)
            if not header:
                return {}
            col_names = [h.strip() for h in header]
            try:
                idx_id = col_names.index("Element ID")
                idx_name = col_names.index("Element Name")
            except ValueError:
                return {}
            for row in reader:
                if len(row) <= max(idx_id, idx_name):
                    continue
                element_id = (row[idx_id] or "").strip()
                element_name = (row[idx_name] or "").strip()
                if not element_id or not element_name:
                    continue
                key = _normalize_label(element_name)
                if key not in out:
                    out[key] = (element_id, element_name)
    except Exception as exc:
        log.warning("onet_load_failed", path=str(p), error=str(exc))
        return {}
    return out


def _get_onet_store() -> dict[str, tuple[str, str]]:
    """Return lazy-loaded O*NET normalized_name -> (element_id, element_name)."""
    global _onet_normalized_to_pair
    if _onet_normalized_to_pair is None:
        _onet_normalized_to_pair = _load_onet_store()
    return _onet_normalized_to_pair


# Lazy-loaded singleton store state
_esco_records: list[dict[str, Any]] | None = None
_parent_label_to_uri: dict[str, str] | None = None
_genai_skill_to_parent: dict[str, str] | None = None
_genai_normalized_to_canonical: dict[str, str] | None = None


def _get_store():
    """Load ESCO + GenAI config once; return (records, parent_label_to_uri, genai_normalized_to_canonical, genai_skill_to_parent)."""
    global _esco_records, _parent_label_to_uri, _genai_skill_to_parent, _genai_normalized_to_canonical
    if _esco_records is None:
        _esco_records = _load_esco_store()
        _parent_label_to_uri = _build_parent_label_to_uri(_esco_records) if _esco_records else {}
        _genai_skill_to_parent = _load_genai_extension()
        _genai_normalized_to_canonical = {_normalize_label(k): k for k in _genai_skill_to_parent}
    return _esco_records, _parent_label_to_uri, _genai_normalized_to_canonical, _genai_skill_to_parent


# ---------------------------------------------------------------------------
# Step 1: GenAI Extension Layer
# ---------------------------------------------------------------------------


def _resolve_step1_genai(label: str) -> TaxonomyResult | None:
    """If label matches a GenAI skill, return TaxonomyResult for step 1; else None."""
    records, parent_to_uri, genai_norm_to_canonical, genai_skill_to_parent = _get_store()
    if not genai_skill_to_parent or not parent_to_uri:
        return None
    norm = _normalize_label(label)
    canonical = genai_norm_to_canonical.get(norm)
    if canonical is None:
        return None
    parent_label = genai_skill_to_parent[canonical]
    parent_norm = _normalize_label(parent_label)
    uri = parent_to_uri.get(parent_norm)
    if not uri:
        return None
    return TaxonomyResult(
        original_label=label,
        esco_uri=uri,
        esco_label=parent_label,
        is_genai_extension=True,
        resolution_step=1,
        confidence=1.0,
    )


# ---------------------------------------------------------------------------
# Steps 2 & 3: ESCO exact and normalized match
# ---------------------------------------------------------------------------


def _resolve_step2_exact_esco(label: str) -> TaxonomyResult | None:
    """Exact (case-insensitive) match on preferred_label, alt_labels, hidden_labels."""
    records, *_ = _get_store()
    label_clean = (label or "").strip().lower()
    for rec in records:
        pref = (rec.get("preferred_label") or "").strip().lower()
        if pref == label_clean:
            return TaxonomyResult(
                original_label=label,
                esco_uri=rec.get("esco_uri"),
                esco_label=rec.get("preferred_label"),
                is_genai_extension=False,
                resolution_step=2,
                confidence=1.0,
            )
        for alt in rec.get("alt_labels") or []:
            if (alt or "").strip().lower() == label_clean:
                return TaxonomyResult(
                    original_label=label,
                    esco_uri=rec.get("esco_uri"),
                    esco_label=rec.get("preferred_label"),
                    is_genai_extension=False,
                    resolution_step=2,
                    confidence=1.0,
                )
        for hid in rec.get("hidden_labels") or []:
            if (hid or "").strip().lower() == label_clean:
                return TaxonomyResult(
                    original_label=label,
                    esco_uri=rec.get("esco_uri"),
                    esco_label=rec.get("preferred_label"),
                    is_genai_extension=False,
                    resolution_step=2,
                    confidence=1.0,
                )
    return None


def _resolve_step3_normalized_esco(label: str) -> TaxonomyResult | None:
    """Normalized match on normalized_label, normalized_alt_labels, normalized_hidden_labels."""
    records, *_ = _get_store()
    norm = _normalize_label(label)
    for rec in records:
        if rec.get("normalized_label") == norm:
            return TaxonomyResult(
                original_label=label,
                esco_uri=rec.get("esco_uri"),
                esco_label=rec.get("preferred_label"),
                is_genai_extension=False,
                resolution_step=3,
                confidence=1.0,
            )
        for nalt in rec.get("normalized_alt_labels") or []:
            if nalt == norm:
                return TaxonomyResult(
                    original_label=label,
                    esco_uri=rec.get("esco_uri"),
                    esco_label=rec.get("preferred_label"),
                    is_genai_extension=False,
                    resolution_step=3,
                    confidence=1.0,
                )
        for nhid in rec.get("normalized_hidden_labels") or []:
            if nhid == norm:
                return TaxonomyResult(
                    original_label=label,
                    esco_uri=rec.get("esco_uri"),
                    esco_label=rec.get("preferred_label"),
                    is_genai_extension=False,
                    resolution_step=3,
                    confidence=1.0,
                )
    return None


# ---------------------------------------------------------------------------
# Step 4: Embedding cosine similarity (Azure OpenAI text-embedding-3-small)
# ---------------------------------------------------------------------------

_esco_embedding_meta: list[tuple[str, str]] | None = None  # (uri, preferred_label)
_esco_normalized_matrix: np.ndarray | None = None  # (n_skills, dim) L2-normalized


def _embed_texts_azure(texts: list[str]) -> list[list[float]] | None:
    """Call Azure OpenAI Embeddings API (text-embedding-3-small). Returns None if env or request fails.

    Env: AZURE_OPENAI_EMBEDDING_ENDPOINT, AZURE_OPENAI_EMBEDDING_API_KEY,
         AZURE_OPENAI_EMBEDDING_API_VERSION, AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME.
    """
    endpoint = (os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT") or "").rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION", "2024-02-01")
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    if not endpoint or not api_key or not deployment:
        log.debug(
            "embedding_skip",
            reason="missing_env",
            has_endpoint=bool(endpoint),
            has_key=bool(api_key),
            has_deployment=bool(deployment),
        )
        return None
    if not texts:
        return []
    url = f"{endpoint}/openai/deployments/{deployment}/embeddings?api-version={api_version}"
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    payload: dict[str, Any] = {"input": texts if len(texts) > 1 else texts[0]}
    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        log.warning("embedding_api_failed", error=str(exc))
        return None
    items = data.get("data") if isinstance(data, dict) else None
    if not items or not isinstance(items, list):
        return None
    out: list[list[float]] = []
    for item in items:
        if not isinstance(item, dict):
            return None
        emb = item.get("embedding")
        if not isinstance(emb, list) or not all(isinstance(x, (int, float)) for x in emb):
            return None
        out.append([float(x) for x in emb])
    return out


_EMBEDDING_CHUNK_SIZE = 100  # Azure payload limit; chunk ESCO and batch queries


def _get_esco_embeddings() -> tuple[list[tuple[str, str]], np.ndarray] | None:
    """Build or return cached (meta, pre-normalized embedding matrix).

    Meta is list of (esco_uri, preferred_label). Matrix is (n_skills, dim) L2-normalized
    so Step 4 only needs to normalize the query and run a dot product.
    Uses Azure OpenAI Embeddings API with chunking to avoid payload limits.
    """
    global _esco_embedding_meta, _esco_normalized_matrix
    if _esco_embedding_meta is not None and _esco_normalized_matrix is not None:
        return _esco_embedding_meta, _esco_normalized_matrix
    records, *_ = _get_store()
    if not records:
        return None
    texts = []
    meta = []
    for rec in records:
        uri = rec.get("esco_uri") or ""
        label = rec.get("preferred_label") or ""
        desc = (rec.get("description") or "")[:200]
        text = f"{label}. {desc}".strip() if desc else label
        texts.append(text)
        meta.append((uri, label))
    vectors_list: list[list[float]] = []
    for i in range(0, len(texts), _EMBEDDING_CHUNK_SIZE):
        chunk = texts[i : i + _EMBEDDING_CHUNK_SIZE]
        res = _embed_texts_azure(chunk)
        if not res or len(res) != len(chunk):
            log.warning("embedding_init_failed", chunk_start=i, chunk_len=len(chunk))
            return None
        vectors_list.extend(res)
    vectors = np.asarray(vectors_list, dtype=np.float64)
    matrix_norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-12
    _esco_normalized_matrix = vectors / matrix_norms
    _esco_embedding_meta = meta
    return _esco_embedding_meta, _esco_normalized_matrix


def _resolve_step4_embedding_impl(label: str) -> TaxonomyResult | None:
    """Embedding cosine similarity >= threshold. Uses SKILL_TAXONOMY_SIMILARITY_THRESHOLD (default 0.92).
    Uses cached pre-normalized ESCO matrix; query is embedded via Azure API, then dot product.
    """
    threshold = float(os.getenv("SKILL_TAXONOMY_SIMILARITY_THRESHOLD", "0.92"))
    cache = _get_esco_embeddings()
    if cache is None:
        return None
    meta, matrix_norm = cache
    query_vectors = _embed_texts_azure([label])
    if not query_vectors or len(query_vectors) != 1:
        return None
    query_vec = np.asarray(query_vectors[0], dtype=np.float64)
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-12)
    # Cosine similarity: matrix already normalized, so dot product is cosine sim
    scores = matrix_norm @ query_norm  # (n_skills,)
    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])
    if best_score < threshold:
        return None
    best_uri, best_label = meta[best_idx]
    return TaxonomyResult(
        original_label=label,
        esco_uri=best_uri,
        esco_label=best_label,
        is_genai_extension=False,
        resolution_step=4,
        confidence=round(best_score, 4),
    )


# ---------------------------------------------------------------------------
# Step 5: O*NET skill match (normalized name lookup)
# ---------------------------------------------------------------------------


def _resolve_step5_onet(label: str) -> TaxonomyResult | None:
    """O*NET skill match: normalized name lookup in O*NET Skills store.

    Returns TaxonomyResult with esco_uri='urn:onet:skill:{Element ID}' and
    esco_label=Element Name. If file is missing or no match, returns None.
    """
    store = _get_onet_store()
    if not store:
        return None
    norm = _normalize_label(label)
    pair = store.get(norm)
    if pair is None:
        return None
    element_id, element_name = pair
    return TaxonomyResult(
        original_label=label,
        esco_uri="urn:onet:skill:" + element_id,
        esco_label=element_name,
        is_genai_extension=False,
        resolution_step=5,
        confidence=1.0,
    )


# ---------------------------------------------------------------------------
# Public API: resolve_taxonomy (6-step order), batch, and resolution_stats
# ---------------------------------------------------------------------------


def resolve_taxonomy(label: str) -> TaxonomyResult:
    """Resolve a single skill label against the taxonomy store.

    Parameters
    ----------
    label : str
        Raw skill label extracted from a job posting.

    Returns
    -------
    TaxonomyResult
        Resolution result with esco_uri, resolution_step, and confidence.
        Returns step-6 fallback (raw_skill) if no match in steps 1–5.
    """
    if not (label or "").strip():
        return TaxonomyResult(
            original_label=label or "",
            esco_uri=None,
            is_genai_extension=False,
            resolution_step=6,
            confidence=0.0,
        )

    result = _resolve_step1_genai(label)
    if result is not None:
        return result

    result = _resolve_step2_exact_esco(label)
    if result is not None:
        return result

    result = _resolve_step3_normalized_esco(label)
    if result is not None:
        return result

    # Step 4 (embedding) is implemented separately; when present it is called here
    result = _resolve_step4_embedding(label)
    if result is not None:
        return result

    result = _resolve_step5_onet(label)
    if result is not None:
        return result

    return TaxonomyResult(
        original_label=label,
        esco_uri=None,
        esco_label=None,
        is_genai_extension=False,
        resolution_step=6,
        confidence=0.0,
    )


def _resolve_step4_embedding(label: str) -> TaxonomyResult | None:
    """Embedding cosine similarity >= threshold (env SKILL_TAXONOMY_SIMILARITY_THRESHOLD, default 0.92)."""
    return _resolve_step4_embedding_impl(label)


def resolve_taxonomy_batch(labels: list[str]) -> list[TaxonomyResult]:
    """Resolve a batch of skill labels, sharing embedding API calls and computations.

    Deduplicates by exact label. Runs Steps 1–3 locally; labels falling through
    are sent to the Azure Embedding API in a single batched HTTP request, and
    Step 4 is resolved using batched NumPy matrix multiplication.

    Parameters
    ----------
    labels : list[str]
        Raw skill labels to resolve.

    Returns
    -------
    list[TaxonomyResult]
        One TaxonomyResult per input label, in the same order.
    """
    unique_order: list[str] = []
    seen: set[str] = set()
    for lab in labels:
        if lab not in seen:
            seen.add(lab)
            unique_order.append(lab)

    resolved_map: dict[str, TaxonomyResult] = {}
    pending_step4: list[str] = []

    # Phase 1: Try fast local steps (1–3) for all unique labels
    for lab in unique_order:
        if not (lab or "").strip():
            resolved_map[lab] = TaxonomyResult(
                original_label=lab or "",
                esco_uri=None,
                esco_label=None,
                is_genai_extension=False,
                resolution_step=6,
                confidence=0.0,
            )
            continue
        r = (
            _resolve_step1_genai(lab)
            or _resolve_step2_exact_esco(lab)
            or _resolve_step3_normalized_esco(lab)
        )
        if r is not None:
            resolved_map[lab] = r
        else:
            pending_step4.append(lab)

    # Phase 2: Single batched HTTP request for Step 4 (chunk if many pending)
    if pending_step4:
        cache = _get_esco_embeddings()
        if cache is not None:
            meta, matrix_norm = cache
            threshold = float(os.getenv("SKILL_TAXONOMY_SIMILARITY_THRESHOLD", "0.92"))
            # Batch embedding request(s) for all pending (chunk to respect API limits)
            all_query_vectors: list[list[float]] = []
            for j in range(0, len(pending_step4), _EMBEDDING_CHUNK_SIZE):
                chunk = pending_step4[j : j + _EMBEDDING_CHUNK_SIZE]
                query_vectors = _embed_texts_azure(chunk)
                if not query_vectors or len(query_vectors) != len(chunk):
                    break
                all_query_vectors.extend(query_vectors)
            if len(all_query_vectors) == len(pending_step4):
                query_matrix = np.asarray(all_query_vectors, dtype=np.float64)
                query_norms = np.linalg.norm(query_matrix, axis=1, keepdims=True) + 1e-12
                query_matrix_norm = query_matrix / query_norms
                # (n_queries, n_skills)
                scores = query_matrix_norm @ matrix_norm.T
                best_indices = np.argmax(scores, axis=1)
                for i, lab in enumerate(pending_step4):
                    best_idx = int(best_indices[i])
                    best_score = float(scores[i, best_idx])
                    if best_score >= threshold:
                        best_uri, best_label = meta[best_idx]
                        resolved_map[lab] = TaxonomyResult(
                            original_label=lab,
                            esco_uri=best_uri,
                            esco_label=best_label,
                            is_genai_extension=False,
                            resolution_step=4,
                            confidence=round(best_score, 4),
                        )

    # Phase 2.5: Step 5 (O*NET) for any still unresolved
    for lab in pending_step4:
        if lab not in resolved_map:
            r5 = _resolve_step5_onet(lab)
            if r5 is not None:
                resolved_map[lab] = r5

    # Phase 3: Step 6 for anything still unresolved
    for lab in pending_step4:
        if lab not in resolved_map:
            resolved_map[lab] = TaxonomyResult(
                original_label=lab,
                esco_uri=None,
                esco_label=None,
                is_genai_extension=False,
                resolution_step=6,
                confidence=0.0,
            )

    return [resolved_map[lab] for lab in labels]


def resolution_stats(results: list[TaxonomyResult]) -> dict[int, int]:
    """Return per-step counts (1-6) for a batch of resolution results.

    Taxonomy coverage = (steps 1-5 total) / len(results); target ≥ 95%.
    """
    counts: dict[int, int] = {i: 0 for i in range(1, 7)}
    for r in results:
        step = r.resolution_step
        if 1 <= step <= 6:
            counts[step] = counts.get(step, 0) + 1
    return counts
