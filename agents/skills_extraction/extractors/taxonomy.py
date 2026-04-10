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

import contextlib
import csv
import json
import os
import re
import time
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

# Alias map: GenAI parent names that are not exact ESCO preferred_label / broader_label strings
# in our JSON → an ESCO label that appears on records (see _build_parent_label_to_uri).
_PARENT_LABEL_ALIASES: dict[str, str] = {
    "digital content creation": "create digital content",
    "software architecture": "designing ict systems or applications",
    "database management": "manage database",
    "information retrieval": "gathering information from physical or electronic sources",
    "digital ethics": "philosophy and ethics",
    "quality assurance": "quality assurance methodologies",
    "systems integration": "integrate ict data",
    "technology evaluation": "evaluating systems, programmes, equipment and products",
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
    """Build map: normalized parent cluster label → ESCO concept URI.

    GenAI extension parents (e.g. \"Machine learning\") are official ESCO concept
    titles: they match a record's ``preferred_label`` even when no other skill
    lists that string under ``broader_concept_labels``. Broader-derived entries
    are filled first; preferred_label fills remaining keys without overwriting.
    """
    out: dict[str, str] = {}
    for rec in records:
        labels = rec.get("broader_concept_labels") or []
        uris = rec.get("broader_concept_uris") or []
        for label, uri in zip(labels, uris, strict=True):
            if label and uri:
                key = _normalize_label(label)
                if key not in out:
                    out[key] = uri.strip()
    for rec in records:
        pref = rec.get("preferred_label")
        uri = (rec.get("esco_uri") or "").strip()
        if not pref or not uri:
            continue
        key = _normalize_label(pref)
        if key and key not in out:
            out[key] = uri
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


_EMBED_MAX_RETRIES = 5
_EMBED_BASE_DELAY = 1.0  # seconds
_EMBED_INTER_REQUEST_DELAY = float(os.getenv("EMBEDDING_REQUEST_DELAY", "0"))

# #108: prompt text for llm_audit_log prompt_hash only (not sent again)
_EMBEDDING_AUDIT_PROMPT_MAX_CHARS = 8000
_EMBEDDING_AUDIT_ERROR_MAX_CHARS = 1000


def _embedding_audit_prompt(texts: list[str]) -> str:
    raw = "\n".join(texts)
    if len(raw) <= _EMBEDDING_AUDIT_PROMPT_MAX_CHARS:
        return raw
    return raw[:_EMBEDDING_AUDIT_PROMPT_MAX_CHARS] + "\n...[truncated for audit hash]"


def _embedding_usage_input_tokens(data: Any) -> int:
    """Parse Azure/OpenAI embeddings response usage; owners may extend for other shapes (#108)."""
    if not isinstance(data, dict):
        log.debug("embedding_usage_missing", reason="response_not_dict")
        return 0
    usage = data.get("usage")
    if not isinstance(usage, dict):
        log.debug("embedding_usage_missing", reason="no_usage_dict")
        return 0
    pt = usage.get("prompt_tokens")
    if isinstance(pt, int) and pt >= 0:
        return pt
    tt = usage.get("total_tokens")
    if isinstance(tt, int) and tt >= 0:
        return tt
    log.debug("embedding_usage_missing", reason="no_prompt_or_total_tokens")
    return 0


def _embedding_cost_usd(input_tokens: int) -> float:
    """Rough $/1K input tokens for text-embedding-3-small class; set EMBEDDING_INPUT_USD_PER_1K_TOKENS to override (#108)."""
    raw = os.getenv("EMBEDDING_INPUT_USD_PER_1K_TOKENS", "0.00002")
    try:
        per_1k = float(raw)
    except (TypeError, ValueError):
        per_1k = 0.00002
    return (input_tokens / 1000.0) * per_1k


def _embedding_error_reason(prefix: str, detail: str | None = None) -> str:
    """Normalize and cap embedding audit error text for llm_audit_log."""
    message = prefix.strip()
    extra = (detail or "").strip()
    if extra:
        message = f"{message}: {extra}" if message else extra
    if len(message) <= _EMBEDDING_AUDIT_ERROR_MAX_CHARS:
        return message
    return message[: _EMBEDDING_AUDIT_ERROR_MAX_CHARS - 3] + "..."


def _response_json_or_none(resp: httpx.Response) -> Any | None:
    """Best-effort JSON parse for audit token extraction on success/failure."""
    try:
        return resp.json()
    except Exception:
        return None


def _log_embedding_audit_event(
    texts: list[str],
    data: Any,
    latency_ms: int,
    *,
    agent_name: str = "taxonomy-resolver",
    success: bool = True,
    error_reason: str | None = None,
) -> None:
    """Write one dbo.llm_audit_log row per embedding HTTP attempt (issue #108).

    Uses response ``usage`` when available so cost tracking works for successful
    calls and any failure responses that still report token usage.
    """
    from agents.common.llm_adapter import log_extraction_event

    input_tokens = _embedding_usage_input_tokens(data)
    log_extraction_event(
        agent_name=agent_name,
        prompt=_embedding_audit_prompt(texts),
        model="text-embedding-3-small",
        provider="azure-openai",
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=0,
        cost_usd=_embedding_cost_usd(input_tokens),
        success=success,
        error_reason=error_reason,
    )


def _extract_retry_after_embedding(error_message: str) -> int | None:
    """Extract retry-after seconds from Azure embedding 429 error."""
    match = re.search(r"retry after (\d+)\s*seconds?", error_message, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _embed_texts_azure(
    texts: list[str],
    *,
    audit_agent_name: str = "taxonomy-resolver",
) -> list[list[float]] | None:
    """Call Azure OpenAI Embeddings API with retry on 429. Returns None if env or request fails.

    Retries up to 5 times with exponential backoff + jitter on 429 rate limits.
    Honors Retry-After from error message when available.

    audit_agent_name
        Written to ``llm_audit_log`` via ``log_extraction_event`` for every HTTP
        attempt (success and failure). Use ``enrichment-dedup`` for job posting
        fuzzy dedup so shared cost tracking stays comparable.

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

    latency_ms = 0
    data: Any = None

    for attempt in range(1, _EMBED_MAX_RETRIES + 1):
        attempt_started = time.perf_counter()
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, json=payload, headers=headers)
                latency_ms = int((time.perf_counter() - attempt_started) * 1000)
                response_data = _response_json_or_none(resp)
                if resp.status_code == 429:
                    retry_after = _extract_retry_after_embedding(resp.text)
                    delay = retry_after if retry_after else _EMBED_BASE_DELAY * (2 ** (attempt - 1))
                    _log_embedding_audit_event(
                        texts,
                        response_data,
                        latency_ms,
                        agent_name=audit_agent_name,
                        success=False,
                        error_reason=_embedding_error_reason("429_rate_limited", resp.text),
                    )
                    log.warning(
                        "embedding_rate_limited",
                        attempt=attempt,
                        delay_s=round(delay, 2),
                        retry_after=retry_after,
                    )
                    if attempt == _EMBED_MAX_RETRIES:
                        log.error("embedding_rate_limit_exhausted", attempts=_EMBED_MAX_RETRIES)
                        return None
                    time.sleep(delay)
                    continue
                resp.raise_for_status()
                if response_data is None:
                    raise ValueError("embedding_response_json_invalid")
                data = response_data
                break
        except httpx.HTTPStatusError as exc:
            latency_ms = int((time.perf_counter() - attempt_started) * 1000)
            response = exc.response
            response_data = _response_json_or_none(response) if response is not None else None
            status_code = response.status_code if response is not None else "http_error"
            detail = response.text if response is not None else str(exc)
            _log_embedding_audit_event(
                texts,
                response_data,
                latency_ms,
                agent_name=audit_agent_name,
                success=False,
                error_reason=_embedding_error_reason(f"http_{status_code}", detail),
            )
            if response is not None and response.status_code == 429:
                retry_after = _extract_retry_after_embedding(str(exc))
                delay = retry_after if retry_after else _EMBED_BASE_DELAY * (2 ** (attempt - 1))
                log.warning("embedding_rate_limited", attempt=attempt, delay_s=round(delay, 2))
                if attempt == _EMBED_MAX_RETRIES:
                    return None
                time.sleep(delay)
                continue
            log.warning("embedding_api_failed", error=str(exc), attempt=attempt)
            return None
        except Exception as exc:
            latency_ms = int((time.perf_counter() - attempt_started) * 1000)
            _log_embedding_audit_event(
                texts,
                None,
                latency_ms,
                agent_name=audit_agent_name,
                success=False,
                error_reason=_embedding_error_reason(type(exc).__name__, str(exc)),
            )
            log.warning("embedding_api_failed", error=str(exc), attempt=attempt)
            return None
    else:
        return None

    # #108: one llm_audit_log row per successful embedding API call (batch chunk = one row).
    _log_embedding_audit_event(texts, data, latency_ms, agent_name=audit_agent_name)

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


_EMBEDDING_CHUNK_SIZE = 50  # Match Next.js batch size; 100 triggers Azure 429s


def _load_embeddings_from_db() -> tuple[list[tuple[str, str]], np.ndarray] | None:
    """Load pre-computed skill embeddings from PostgreSQL (pgvector).

    Returns (meta, L2-normalized matrix) where meta is list of (skill_name, skill_name).
    Embeddings are seeded by admin via agents/scripts/seed_esco_embeddings.py.
    """
    try:
        from sqlalchemy import text as sa_text

        from agents.common.data_store.database import session_scope

        with session_scope() as session:
            rows = session.execute(
                sa_text(
                    "SELECT skill_name, embedding::text FROM dbo.skills WHERE embedding IS NOT NULL ORDER BY skill_name"
                )
            ).fetchall()

        if not rows:
            return None

        meta: list[tuple[str, str]] = []
        vectors_list: list[list[float]] = []
        for row in rows:
            skill_name = row[0]
            vec_str = row[1]
            vec = json.loads(vec_str)
            meta.append((skill_name, skill_name))
            vectors_list.append(vec)

        matrix = np.asarray(vectors_list, dtype=np.float64)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12
        matrix_normalized = matrix / norms

        return meta, matrix_normalized
    except Exception as exc:
        log.warning("esco_embedding_db_load_failed", error=str(exc))
        return None


def _get_esco_embeddings() -> tuple[list[tuple[str, str]], np.ndarray] | None:
    """Load pre-computed ESCO embeddings from PostgreSQL.

    Resolution order:
    1. In-memory global cache (fastest — same process)
    2. PostgreSQL pgvector column on dbo.skills (no API calls)

    Embeddings are seeded once by admin via seed_esco_embeddings.py.
    If no embeddings exist in the DB, Step 4 is skipped (falls through to Steps 5-6).

    Meta is list of (skill_name, skill_name). Matrix is (n_skills, dim) L2-normalized
    so Step 4 only needs to normalize the query and run a dot product.
    """
    global _esco_embedding_meta, _esco_normalized_matrix

    # 1. In-memory cache
    if _esco_embedding_meta is not None and _esco_normalized_matrix is not None:
        return _esco_embedding_meta, _esco_normalized_matrix

    # 2. PostgreSQL
    db_result = _load_embeddings_from_db()
    if db_result is not None:
        _esco_embedding_meta, _esco_normalized_matrix = db_result
        log.info("esco_embeddings_loaded_from_db", skills=len(_esco_embedding_meta))
        return _esco_embedding_meta, _esco_normalized_matrix

    log.warning(
        "esco_embeddings_not_available",
        reason="No embeddings in dbo.skills — run seed_esco_embeddings.py (admin only)",
    )
    return None


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
        r = _resolve_step1_genai(lab) or _resolve_step2_exact_esco(lab) or _resolve_step3_normalized_esco(lab)
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

    results = [resolved_map[lab] for lab in labels]

    # Log taxonomy resolution metrics to Langfuse tracer (if registered)
    with contextlib.suppress(Exception):
        from agents.common.llm_adapter import get_tracer

        tracer = get_tracer()
        if tracer:
            stats = {i: 0 for i in range(1, 7)}
            for r in results:
                if 1 <= r.resolution_step <= 6:
                    stats[r.resolution_step] = stats.get(r.resolution_step, 0) + 1
            n = len(results)
            fallback = stats.get(6, 0)
            coverage = (n - fallback) / n if n else 0.0
            resolved = [r for r in results if r.resolution_step < 6]
            avg_conf = sum(r.confidence for r in resolved) / len(resolved) if resolved else 0.0
            tracer.log_event(
                "taxonomy_resolution",
                {
                    "total_labels": n,
                    "taxonomy_coverage": round(coverage, 4),
                    "avg_confidence": round(avg_conf, 4),
                    "step1_genai": stats.get(1, 0),
                    "step2_exact_esco": stats.get(2, 0),
                    "step3_normalized_esco": stats.get(3, 0),
                    "step4_embedding": stats.get(4, 0),
                    "step5_onet": stats.get(5, 0),
                    "step6_raw_fallback": fallback,
                },
            )

    return results


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


def resolution_report(results: list[TaxonomyResult]) -> dict[str, Any]:
    """Aggregate metrics for eval / runbook reporting.

    Returns counts_by_step, taxonomy_coverage (0-1), genai_extension_matches,
    raw_skill_fallback (step 6 count), and avg_resolution_confidence over
    steps 1-5 only (step 6 excluded from the average).
    """
    stats = resolution_stats(results)
    n = len(results)
    genai = sum(1 for r in results if r.is_genai_extension)
    resolved = [r for r in results if r.resolution_step < 6]
    avg_conf = sum(r.confidence for r in resolved) / len(resolved) if resolved else 0.0
    fallback = stats.get(6, 0)
    coverage = (n - fallback) / n if n else 0.0
    return {
        "counts_by_step": stats,
        "taxonomy_coverage": round(coverage, 4),
        "genai_extension_matches": genai,
        "raw_skill_fallback": fallback,
        "avg_resolution_confidence": round(avg_conf, 4),
    }
