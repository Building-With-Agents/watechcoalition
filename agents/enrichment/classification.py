"""Deterministic role and seniority classification for Phase 1 lite enrichment.

Role labels: pick the best-matching ``technology_areas.title`` (or sector title)
by token overlap between a normalized job corpus and each reference title.

Tokenization: lowercase the text, split on non-alphanumeric boundaries, keep
tokens with length >= 2. Stopwords are not removed (small reference sets).

Token match: a reference token *rt* matches the corpus if *rt* is in the corpus
token set, or (when len(rt) >= 3) *rt* is a substring of some corpus token or
some corpus token is a substring of *rt* (handles engineer/engineering).

Seniority: ordered regex rules (first win). If none match, optional internship
flag forces *intern*; else *mid* when the title looks like a typical IC role,
otherwise *unknown*.
"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from typing import Any

from sqlalchemy import update
from sqlalchemy.orm import Session

from agents.common.data_store.models import NormalizedJob
from agents.common.types.job_profile import JobProfile
from agents.common.types.job_record import JobRecord
from agents.enrichment.classifiers.soc_classifier import classify_soc

# Role classification
MIN_TOKEN_LEN = 2
MIN_FUZZY_TOKEN_LEN = 3
MIN_ROLE_OVERLAP_SCORE = 1

# Substring hints checked against ``title.lower()`` first (longer phrases first).
_TITLE_ROLE_HINTS: tuple[tuple[str, str], ...] = (
    ("machine learning", "Machine Learning"),
    ("data scientist", "Data Science"),
    ("data science", "Data Science"),
    ("data engineer", "Data Engineering"),
    ("data analyst", "Data Analytics"),
    ("data analytics", "Data Analytics"),
    ("full stack", "Software Engineering"),
    ("fullstack", "Software Engineering"),
    ("backend", "Software Engineering"),
    ("front end", "Software Engineering"),
    ("frontend", "Software Engineering"),
    ("software engineer", "Software Engineering"),
    ("software developer", "Software Engineering"),
    ("devops", "DevOps"),
    ("ml platform", "Machine Learning"),
    ("ml engineer", "Machine Learning"),
    ("platform engineer", "Software Engineering"),
)

# Walking-skeleton / offline DB fallback — mirrors common technology area labels.
FALLBACK_TECH_AREA_LABELS: tuple[tuple[str, str], ...] = (
    ("ta-data-eng", "Data Engineering"),
    ("ta-sw-eng", "Software Engineering"),
    ("ta-ml", "Machine Learning"),
    ("ta-ds", "Data Science"),
    ("ta-devops", "DevOps"),
    ("ta-data-analytics", "Data Analytics"),
)

IC_ROLE_RE = re.compile(
    r"\b(engineer|developer|scientist|analyst|architect|programmer)\b",
    re.IGNORECASE,
)

# (pattern, label) — first match wins; patterns are case-insensitive.
_SENIORITY_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\b(chief\s+\w+?\s+officer|c\.?e\.?o\.?|c\.?t\.?o\.?|c\.?i\.?o\.?|"
            r"cfo|cmo|cpo|executive\s+vice\s+president|evp|svp|"
            r"vice\s+president|\bvp\b|v\.?p\.?\s+of|president|managing\s+director)\b",
            re.IGNORECASE,
        ),
        "executive",
    ),
    (
        re.compile(
            r"\b(director|head\s+of)\b",
            re.IGNORECASE,
        ),
        "executive",
    ),
    (
        re.compile(
            r"\b(tech\s+lead|team\s+lead|engineering\s+manager|people\s+manager|"
            r"product\s+manager|program\s+manager|project\s+manager)\b",
            re.IGNORECASE,
        ),
        "lead",
    ),
    (
        re.compile(r"\b(lead\s+\w+|^\s*lead\b|\blead\s+engineer\b)", re.IGNORECASE),
        "lead",
    ),
    (
        re.compile(
            r"\b(senior|sr\.?|principal|staff|distinguished)\b",
            re.IGNORECASE,
        ),
        "senior",
    ),
    (
        re.compile(
            r"\b(junior|jr\.?|entry[\s-]level|associate\s+\w+|graduate\s+\w+)\b",
            re.IGNORECASE,
        ),
        "junior",
    ),
    (
        re.compile(r"\b(intern|internship|co-?op)\b", re.IGNORECASE),
        "intern",
    ),
    (
        re.compile(r"\b(mid[\s-]level|intermediate|\bmid\b)\b", re.IGNORECASE),
        "mid",
    ),
)


def tokenize(text: str) -> set[str]:
    """Lowercase *text* and return a set of alphanumeric tokens (len >= MIN_TOKEN_LEN)."""
    if not text:
        return set()
    parts = re.split(r"[^a-z0-9]+", text.lower())
    return {p for p in parts if len(p) >= MIN_TOKEN_LEN}


def _tokens_linked(ref_t: str, corpus_tokens: set[str]) -> bool:
    if ref_t in corpus_tokens:
        return True
    if len(ref_t) < MIN_FUZZY_TOKEN_LEN:
        return False
    for c in corpus_tokens:
        if len(c) < MIN_FUZZY_TOKEN_LEN:
            continue
        if ref_t in c or c in ref_t:
            return True
    return False


def _role_score_for_title(ref_title: str, corpus_tokens: set[str]) -> int:
    ref_tokens = tokenize(ref_title)
    if not ref_tokens:
        return 0
    return sum(1 for rt in ref_tokens if _tokens_linked(rt, corpus_tokens))


def _pick_best_role(
    candidates: list[tuple[str, str]],
    corpus_tokens: set[str],
) -> tuple[str | None, int]:
    """Return (title, score) for the winning reference row.

    Tie-break: higher score, then longer title, then lexicographic ref id.
    """
    best_title: str | None = None
    best_score = -1
    best_id = ""
    for ref_id, title in candidates:
        score = _role_score_for_title(title, corpus_tokens)
        cand = (score, len(title), ref_id)
        cur = (best_score, len(best_title or ""), best_id)
        if cand > cur:
            best_score = score
            best_title = title
            best_id = ref_id
    if best_title is None:
        return None, 0
    return best_title, best_score


def _hint_role(title: str) -> str | None:
    tl = (title or "").lower()
    for phrase, label in _TITLE_ROLE_HINTS:
        if phrase in tl:
            return label
    return None


def flatten_extraction_json(
    skills: list[Any] | None,
    tools: list[Any] | None,
    tasks: list[Any] | None,
    responsibilities: list[Any] | None,
    context: list[Any] | None,
) -> str:
    """Flatten JSONB extraction dimensions into one searchable string."""

    def walk(obj: Any, out: list[str]) -> None:
        if obj is None:
            return
        if isinstance(obj, str):
            if obj.strip():
                out.append(obj)
            return
        if isinstance(obj, dict):
            for key in (
                "task_description",
                "description",
                "responsibility_description",
                "skill_name",
                "label",
                "tool_name",
                "text",
                "name",
            ):
                if key in obj and isinstance(obj[key], str):
                    walk(obj[key], out)
            span = obj.get("source_span")
            if isinstance(span, dict):
                walk(span.get("text"), out)
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    walk(v, out)
            return
        if isinstance(obj, list):
            for item in obj:
                walk(item, out)

    chunks: list[str] = []
    for blob in (skills, tools, tasks, responsibilities, context):
        if blob:
            walk(blob, chunks)
    return " ".join(chunks)


def build_job_corpus(
    job_title: str,
    job_description: str | None,
    extraction: dict[str, Any] | None,
) -> str:
    parts = [job_title or "", job_description or ""]
    if extraction:
        parts.append(
            flatten_extraction_json(
                extraction.get("skills"),
                extraction.get("tools"),
                extraction.get("tasks"),
                extraction.get("responsibilities"),
                extraction.get("context"),
            )
        )
    return " ".join(p for p in parts if p)


def classify_role(
    job_title: str,
    corpus: str,
    technology_areas: list[tuple[str, str]],
    industry_sectors: list[tuple[str, str]],
    min_score: int = MIN_ROLE_OVERLAP_SCORE,
) -> str:
    """
    Return best ``technology_areas.title``, or a title hint, or ``unclassified``.

    *technology_areas* / *industry_sectors* are ``(id, title)`` rows from the DB.
    """
    hinted = _hint_role(job_title)
    if hinted:
        return hinted

    corpus_tokens = tokenize(corpus)
    best_tech, tech_score = _pick_best_role(list(technology_areas), corpus_tokens)
    best_sec, sec_score = _pick_best_role(list(industry_sectors), corpus_tokens)

    if tech_score >= min_score:
        return best_tech or "unclassified"
    if sec_score >= min_score:
        return best_sec or "unclassified"
    return "unclassified"


def classify_seniority(
    job_title: str,
    job_description: str | None,
    extraction: dict[str, Any] | None,
    *,
    is_internship: bool = False,
) -> str:
    """
    Closed set: intern | junior | mid | senior | lead | executive | unknown.

    Primary text: title + flattened tasks/responsibilities; then description if still unknown.
    """
    if is_internship:
        return "intern"

    task_resp = ""
    if extraction:
        task_resp = flatten_extraction_json(
            None,
            None,
            extraction.get("tasks"),
            extraction.get("responsibilities"),
            None,
        )

    segments = [job_title or "", task_resp]
    for segment in segments:
        for pattern, label in _SENIORITY_RULES:
            if pattern.search(segment):
                return label

    desc = job_description or ""
    for pattern, label in _SENIORITY_RULES:
        if pattern.search(desc):
            return label

    if IC_ROLE_RE.search(job_title or ""):
        return "mid"
    return "unknown"


def classify_job(
    job_title: str,
    job_description: str | None,
    extraction: dict[str, Any] | None,
    technology_areas: list[tuple[str, str]],
    industry_sectors: list[tuple[str, str]],
    *,
    is_internship: bool = False,
) -> tuple[str, str]:
    """Return ``(role_classification, seniority)``."""
    corpus = build_job_corpus(job_title, job_description, extraction)
    role = classify_role(job_title, corpus, technology_areas, industry_sectors)
    seniority = classify_seniority(
        job_title, job_description, extraction, is_internship=is_internship
    )
    return role, seniority


async def enrich_job_profile_soc(
    job_profile: JobProfile,
    session: Session,
    llm: Callable[[str], str],
    *,
    soc_code_override: str | None = None,
) -> None:
    desc = job_profile.description if isinstance(job_profile.description, str) else ""
    if soc_code_override is not None:
        soc_code = soc_code_override
    else:
        soc_code = await classify_soc(job_profile.title, desc, session, llm)
    job_profile.soc_code = soc_code
    oc_value = ((soc_code or "").strip()[:20]) or None
    stmt = (
        update(NormalizedJob)
        .where(NormalizedJob.external_id == job_profile.external_id)
        .where(NormalizedJob.source == job_profile.source)
        .values(occupation_code=oc_value)
    )
    session.execute(stmt)


async def build_job_profile_with_soc(
    job_record: JobRecord,
    session: Session,
    llm: Callable[[str], str],
    *,
    soc_code_override: str | None = None,
) -> JobProfile:
    job_profile = JobProfile.model_validate(job_record.model_dump())
    await enrich_job_profile_soc(
        job_profile, session, llm, soc_code_override=soc_code_override
    )
    return job_profile


def enrich_job_profile_soc_blocking(
    job_profile: JobProfile,
    session: Session,
    llm: Callable[[str], str],
    *,
    soc_code_override: str | None = None,
) -> None:
    asyncio.run(
        enrich_job_profile_soc(
            job_profile, session, llm, soc_code_override=soc_code_override
        )
    )
