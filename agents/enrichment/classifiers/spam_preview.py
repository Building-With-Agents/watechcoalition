"""Spam scoring for Decision #8 preview (diagnostic only; not wired to job_postings writes).

Uses Azure OpenAI via :func:`agents.common.llm_client.invoke_skills_llm` (same deployment
env as skills extraction). On LLM failure or missing config, returns **degraded** null
scores unless ``SPAM_PREVIEW_ALLOW_HEURISTIC=1`` (offline-only noisy estimate).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

import structlog
from pydantic import BaseModel, Field, field_validator

log = structlog.get_logger()

AUDIT_AGENT_SPAM_PREVIEW = "enrichment-spam-preview"


def _threshold(name: str, default: str) -> float:
    raw = os.getenv(name, default)
    try:
        return float(raw)
    except ValueError:
        return float(default)


def get_spam_thresholds() -> tuple[float, float]:
    """Current flag and reject thresholds from env (for reporting)."""
    return (
        _threshold("SPAM_FLAG_THRESHOLD", "0.7"),
        _threshold("SPAM_REJECT_THRESHOLD", "0.9"),
    )


def apply_spam_tiers(
    spam_score: float,
    *,
    flag: float | None = None,
    reject: float | None = None,
) -> tuple[bool | None, str]:
    """Map numeric score to ``(is_spam, tier_label)`` per IC #8.

    * ``< flag`` → ``(False, "clean")``
    * ``<= reject`` → ``(None, "flagged")``
    * ``> reject`` → ``(True, "rejected")``

    Thresholds default from ``SPAM_FLAG_THRESHOLD`` (0.7) and ``SPAM_REJECT_THRESHOLD`` (0.9).
    """
    f = _threshold("SPAM_FLAG_THRESHOLD", "0.7") if flag is None else flag
    r = _threshold("SPAM_REJECT_THRESHOLD", "0.9") if reject is None else reject
    if spam_score < f:
        return False, "clean"
    if spam_score <= r:
        return None, "flagged"
    return True, "rejected"


class SpamClassifierOutput(BaseModel):
    """Expected JSON shape from the spam preview LLM."""

    spam_score: float = Field(..., ge=0.0, le=1.0)
    rationale: str | None = None
    spam_confidence: float | None = None
    signals: dict[str, float] | None = None

    @field_validator("spam_confidence", mode="before")
    @classmethod
    def clamp_conf(cls, v: Any) -> float | None:
        if v is None:
            return None
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return None

    @field_validator("signals", mode="before")
    @classmethod
    def empty_signals(cls, v: Any) -> dict[str, float] | None:
        if v is None or v == {}:
            return None
        if isinstance(v, dict):
            out: dict[str, float] = {}
            for k, val in v.items():
                try:
                    out[str(k)] = float(val)
                except (TypeError, ValueError):
                    continue
            return out or None
        return None


@dataclass
class SpamPreviewResult:
    """Outcome of :func:`score_spam_preview` for one job."""

    spam_score: float | None
    is_spam: bool | None
    tier: str
    field_confidence: dict[str, float]
    overall_confidence: float | None
    rationale: str | None
    degraded: bool
    extraction_note: str | None
    used_heuristic: bool


def _parse_json_object(text: str) -> dict[str, Any] | None:
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        t = "\n".join(lines)
    try:
        data = json.loads(t)
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _default_spam_confidence(spam_score: float) -> float:
    """Higher when score is near 0 or 1 (decisive); lower near 0.5 (ambiguous)."""
    return max(0.0, min(1.0, 1.0 - abs(spam_score - 0.5) * 2))


def _build_prompt(
    job_title: str,
    job_description: str | None,
    extraction: dict[str, Any] | None,
    extraction_failed: bool,
    extraction_empty: bool,
) -> str:
    ei_note = ""
    if extraction_failed:
        ei_note = (
            "\nUpstream extraction reported FAILURE. Scores may be unreliable; "
            "prefer flagging uncertain postings rather than assuming legitimate.\n"
        )
    elif extraction_empty:
        ei_note = (
            "\nExtraction payload is EMPTY (no skills/tasks/responsibilities/context). "
            "Legitimate jobs may score like spam due to missing structure — factor that in.\n"
        )
    ex_json = json.dumps(extraction or {}, ensure_ascii=False)[:12000]
    desc = (job_description or "")[:20000]
    return f"""You are a job-posting spam classifier for a labor-market analytics pipeline.

Return a single JSON object with:
- "spam_score": float from 0.0 (legitimate job posting) to 1.0 (spam/scam/placeholder)
- "rationale": short string (no PII)
- "spam_confidence": optional float 0-1 for how confident you are in spam_score
- "signals": optional map of string -> float for sub-signals (e.g. "promo_language": 0.8)

Spam includes: obvious scams, unrelated content, empty boilerplate, lead-gen with no real role,
repeated nonsense, or postings that are not real jobs. Legitimate thin postings should not
automatically get spam_score near 1.0 unless clearly abusive.

{ei_note}
Job title: {job_title}

Structured extraction (JSON, may be empty):
{ex_json}

Job description (plain text):
{desc}
"""


def _heuristic_spam(
    job_title: str,
    job_description: str | None,
) -> tuple[float, dict[str, float], str]:
    """Noisy offline-only estimate; low confidence. Do not use for production."""
    corpus = f"{job_title or ''} {(job_description or '')}".strip()
    lower = corpus.lower()
    score = 0.45
    if len(corpus) < 35:
        score = 0.88
    elif re.search(r"\b(click here|earn \$\d|bitcoin|crypto airdrop)\b", lower):
        score = 0.92
    elif "work from home" in lower and len(corpus) < 120:
        score = 0.78
    fc = {
        "spam_score": 0.35,
    }
    rationale = "heuristic_offline_preview"
    return score, fc, rationale


def _finalize_from_score(
    spam_score: float,
    field_confidence: dict[str, float],
    overall_confidence: float | None,
    rationale: str | None,
    degraded: bool,
    extraction_note: str | None,
    used_heuristic: bool,
) -> SpamPreviewResult:
    is_spam, tier = apply_spam_tiers(spam_score)
    return SpamPreviewResult(
        spam_score=spam_score,
        is_spam=is_spam,
        tier=tier,
        field_confidence=field_confidence,
        overall_confidence=overall_confidence,
        rationale=rationale,
        degraded=degraded,
        extraction_note=extraction_note,
        used_heuristic=used_heuristic,
    )


def score_spam_preview(
    *,
    job_title: str,
    job_description: str | None,
    extraction: dict[str, Any] | None,
    extraction_failed: bool,
    extraction_empty: bool,
) -> SpamPreviewResult:
    """Score one job for spam; never raises. Degraded path uses null scores (unless heuristic env)."""
    extraction_note: str | None = None
    if extraction_failed:
        extraction_note = "extraction_failed"
    elif extraction_empty:
        extraction_note = "empty_extraction"

    allow_heuristic = os.getenv("SPAM_PREVIEW_ALLOW_HEURISTIC", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    def _degraded() -> SpamPreviewResult:
        return SpamPreviewResult(
            spam_score=None,
            is_spam=None,
            tier="uncertain",
            field_confidence={},
            overall_confidence=None,
            rationale=None,
            degraded=True,
            extraction_note=extraction_note,
            used_heuristic=False,
        )

    from agents.common.llm_client import invoke_skills_llm

    prompt = _build_prompt(
        job_title,
        job_description,
        extraction,
        extraction_failed,
        extraction_empty,
    )

    try:
        text, meta = invoke_skills_llm(prompt, agent_name=AUDIT_AGENT_SPAM_PREVIEW)
    except (ValueError, ImportError) as exc:
        log.warning("spam_preview_llm_unavailable", error=str(exc))
        if allow_heuristic:
            s, fc, rat = _heuristic_spam(job_title, job_description)
            oc = sum(fc.values()) / len(fc) if fc else None
            return _finalize_from_score(
                s,
                fc,
                oc,
                rat,
                degraded=False,
                extraction_note=extraction_note,
                used_heuristic=True,
            )
        return _degraded()

    if not meta.get("success") or not (text or "").strip():
        log.warning(
            "spam_preview_llm_failed",
            error_reason=meta.get("error_reason"),
        )
        if allow_heuristic:
            s, fc, rat = _heuristic_spam(job_title, job_description)
            oc = sum(fc.values()) / len(fc) if fc else None
            return _finalize_from_score(
                s,
                fc,
                oc,
                rat,
                degraded=False,
                extraction_note=extraction_note,
                used_heuristic=True,
            )
        return _degraded()

    raw = _parse_json_object(text)
    if not raw:
        log.warning("spam_preview_invalid_json")
        if allow_heuristic:
            s, fc, rat = _heuristic_spam(job_title, job_description)
            oc = sum(fc.values()) / len(fc) if fc else None
            return _finalize_from_score(
                s,
                fc,
                oc,
                rat,
                degraded=False,
                extraction_note=extraction_note,
                used_heuristic=True,
            )
        return _degraded()

    try:
        out = SpamClassifierOutput.model_validate(raw)
    except Exception as exc:
        log.warning("spam_preview_validation_failed", error=str(exc))
        if allow_heuristic:
            s, fc, rat = _heuristic_spam(job_title, job_description)
            oc = sum(fc.values()) / len(fc) if fc else None
            return _finalize_from_score(
                s,
                fc,
                oc,
                rat,
                degraded=False,
                extraction_note=extraction_note,
                used_heuristic=True,
            )
        return _degraded()

    s = max(0.0, min(1.0, float(out.spam_score)))
    sc = out.spam_confidence
    if sc is None:
        sc = _default_spam_confidence(s)
    field_confidence: dict[str, float] = {"spam_score": float(sc)}
    if out.signals:
        for k, v in out.signals.items():
            field_confidence[f"signal:{k}"] = float(v)
    overall = sum(field_confidence.values()) / len(field_confidence) if field_confidence else None

    return _finalize_from_score(
        s,
        field_confidence,
        overall,
        out.rationale,
        degraded=False,
        extraction_note=extraction_note,
        used_heuristic=False,
    )
