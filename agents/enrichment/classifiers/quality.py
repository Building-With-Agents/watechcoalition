"""Deterministic job posting quality score [0–1] for Phase 1 enrichment-lite.

Composite of four signals (each 0–1), equally weighted:
- **Completeness** — title length, description length, populated extraction dimensions
- **Clarity** — token count and lexical diversity (thin / repetitive text scores lower)
- **AI / tech keyword density** — relevant terms vs corpus size (capped; weak floor when absent)
- **Structural coherence** — multi-line description, bullets, common section headers

Uses the same job corpus as role classification via :func:`agents.enrichment.classification.build_job_corpus`.
No LLM calls — safe for CI and consistent with ``score_spam_preview`` inputs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from agents.enrichment.classification import build_job_corpus

# Multi-word phrases first (substring match on whitespace-normalized corpus).
_AI_TECH_PHRASES: tuple[str, ...] = (
    "machine learning",
    "artificial intelligence",
    "deep learning",
    "data science",
    "large language",
    "neural network",
    "computer vision",
    "natural language",
    "large language model",
    "generative ai",
    "software engineering",
    "cloud computing",
)

_AI_TECH_TOKENS: frozenset[str] = frozenset(
    {
        "ai",
        "ml",
        "llm",
        "llms",
        "nlp",
        "genai",
        "pytorch",
        "tensorflow",
        "keras",
        "kubernetes",
        "docker",
        "aws",
        "azure",
        "gcp",
        "sql",
        "etl",
        "api",
        "apis",
        "devops",
        "mlops",
        "spark",
        "kafka",
    }
)

_SECTION_HINT = re.compile(
    r"\b("
    r"responsibilities|qualifications|requirements|what\s+you\s*(’|'|will)|"
    r"who\s+you\s+are|benefits|about\s+(the\s+)?role|skills\s+required"
    r")\b",
    re.IGNORECASE,
)

_BULLET_LINE = re.compile(r"^\s*([\-*•]|\d+[\.)])\s+\S", re.MULTILINE)


@dataclass(frozen=True)
class QualityScoreResult:
    """Outcome of :func:`score_quality`."""

    quality_score: float
    components: dict[str, float]


def _word_tokens(corpus: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", corpus.lower())


def _completeness(
    title: str,
    description: str | None,
    extraction: dict[str, Any] | None,
) -> float:
    t = (title or "").strip()
    d = (description or "").strip()
    title_s = min(1.0, len(t) / 24.0) if t else 0.0
    desc_s = min(1.0, len(d) / 1400.0)

    dim_filled = 0
    if extraction:
        for key in ("skills", "tools", "tasks", "responsibilities", "context"):
            blob = extraction.get(key)
            if isinstance(blob, list) and len(blob) > 0:
                dim_filled += 1
    struct_s = dim_filled / 5.0

    return 0.28 * title_s + 0.42 * desc_s + 0.30 * struct_s


def _clarity(corpus: str) -> float:
    words = [w for w in _word_tokens(corpus) if len(w) >= 2]
    n = len(words)
    if n == 0:
        return 0.0
    if n < 8:
        return 0.25 + 0.45 * (n / 8.0)

    unique_ratio = len(set(words)) / n
    length_factor = min(1.0, n / 90.0)
    diversity = min(1.0, unique_ratio / 0.55)
    base = 0.45 * length_factor + 0.55 * diversity
    if n > 12 and unique_ratio < 0.28:
        base *= 0.75
    return max(0.0, min(1.0, base))


def _ai_keyword_score(corpus: str) -> float:
    words = [w for w in _word_tokens(corpus) if len(w) >= 2]
    n = max(len(words), 1)
    lower = f" {corpus.lower()} "
    phrase_hits = sum(1 for p in _AI_TECH_PHRASES if p in lower)
    token_hits = sum(1 for w in words if w in _AI_TECH_TOKENS)
    hits = phrase_hits + token_hits
    # Floor: tech-neutral postings are not penalized to zero.
    density_bonus = min(1.0, (hits * 2.5) / n)
    return max(0.0, min(1.0, 0.38 + 0.62 * density_bonus))


def _structural(description: str | None) -> float:
    d = (description or "").strip()
    if not d:
        return 0.0
    lines = [ln for ln in d.splitlines() if ln.strip()]
    score = 0.0
    if len(lines) >= 5:
        score += 0.38
    elif len(lines) >= 3:
        score += 0.26
    elif len(lines) >= 2:
        score += 0.16

    bullets = len(_BULLET_LINE.findall(d))
    if bullets >= 3:
        score += 0.34
    elif bullets >= 1:
        score += 0.20

    if _SECTION_HINT.search(d):
        score += 0.28

    return max(0.0, min(1.0, score))


def score_quality(
    *,
    job_title: str,
    job_description: str | None,
    extraction: dict[str, Any] | None,
    extraction_failed: bool = False,
) -> QualityScoreResult:
    """Compute a single quality score in ``[0, 1]`` and per-component breakdown."""
    corpus = build_job_corpus(
        job_title or "",
        job_description if isinstance(job_description, str) else None,
        extraction,
    )
    c = _completeness(job_title, job_description, extraction)
    cl = _clarity(corpus)
    ai = _ai_keyword_score(corpus)
    st = _structural(job_description if isinstance(job_description, str) else None)

    combined = 0.25 * c + 0.25 * cl + 0.25 * ai + 0.25 * st
    if extraction_failed:
        combined *= 0.90

    final = max(0.0, min(1.0, combined))
    return QualityScoreResult(
        quality_score=round(final, 6),
        components={
            "completeness": round(c, 6),
            "clarity": round(cl, 6),
            "ai_keyword_density": round(ai, 6),
            "structural_coherence": round(st, 6),
        },
    )
