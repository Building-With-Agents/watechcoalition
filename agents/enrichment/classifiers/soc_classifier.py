"""SOC occupation classification using ``dbo.socc`` reference rows (2018 / 2010 versions)."""

from __future__ import annotations

import re
from collections.abc import Callable

import structlog
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from agents.common.data_store.models import SOCC

log = structlog.get_logger()

_CLOUD_ENGINEER_DIAG_TITLE = "Cloud Engineer"

# Extract SOC-shaped tokens from noisy LLM text; matches are kept only if in candidate_codes.
_SOC_CODE_IN_TEXT = re.compile(r"\d{2}-\d{4}(?:\.\d{2})?")

# Title signals an IT / software-style role (not civil/mechanical "engineer" alone).
_TECH_TITLE_RE = re.compile(
    r"\b(cloud|saas|software|devops|backend|front[\s-]?end|frontend|full[\s-]?stack|fullstack|"
    r"platform|kubernetes|docker|\baws\b|\bazure\b|\bgcp\b|mlops|data\s+engineer|data\s+scientist|"
    r"machine\s+learning|\bml\b|deep\s+learning|\bai\b|artificial\s+intelligence|\bsre\b|"
    r"site\s+reliability|programmer|developer|typescript|javascript|\bpython\b|\bjava\b|golang|"
    r"react|node\.?js|cyber|infosec|penetration|\bdba\b|database\s+admin|\bsql\b|analytics|"
    r"network\s+engineer|systems\s+admin|help\s+desk|it\s+support|computer\s+science)\b",
    re.IGNORECASE,
)

# Needles that match almost every non-IT "… Engineer" SOC row — drop from substring OR when tech title.
_GENERIC_ENGINEERING_NEEDLES = frozenset({"engineer", "engineering"})

# ``dbo.socc.title`` substrings that anchor computer / software / IT occupations (2010/2018 SOC wording).
_TECH_SOCC_TITLE_FRAGMENTS: tuple[str, ...] = (
    "computer",
    "software",
    "information",
    "developer",
    "programmer",
    "database",
    "systems analyst",
    "web developer",
    "network architect",
    "computer network",
    "computer support",
    "computer occupation",
    "computer research",
    "computer user",
    "cyber",
    "technology",
)


def _title_has_tech_profile(title: str) -> bool:
    return bool(_TECH_TITLE_RE.search(title or ""))


def _first_title_word_lower(title: str) -> str | None:
    parts = (title or "").strip().split()
    if not parts:
        return None
    return parts[0].lower()


def _soc_digits_key(code: str) -> str:
    """Normalize SOC / O*NET strings for comparison (DB often stores codes without hyphens)."""
    return re.sub(r"\D", "", code or "")


def _canonical_catalog_code(picked: str, candidate_codes: set[str]) -> str | None:
    """Map resolver output to the exact ``code`` string stored for a candidate row."""
    if not picked or picked == "unclassified":
        return None
    s = picked.strip()
    if s in candidate_codes:
        return s
    pk = _soc_digits_key(s)
    if not pk:
        return None
    for c in candidate_codes:
        if _soc_digits_key(c) == pk:
            return c
    return None


def _digits_to_canonical_codes(candidate_codes: set[str]) -> dict[str, str]:
    """Map digit-only key → single catalog code; ambiguous keys are omitted."""
    buckets: dict[str, list[str]] = {}
    for c in candidate_codes:
        k = _soc_digits_key(c)
        if not k:
            continue
        buckets.setdefault(k, []).append(c)
    return {k: v[0] for k, v in buckets.items() if len(v) == 1}


def _resolve_llm_pick_with_reason(raw: str, candidate_codes: set[str]) -> tuple[str, str]:
    """Return ``(picked_code_or_unclassified, reason_tag)`` for logging and auditing."""
    s = (raw or "").strip()
    if not s:
        return "unclassified", "empty_llm_response"
    if s.lower() == "unclassified":
        return "unclassified", "llm_said_unclassified"
    if s in candidate_codes:
        return s, "exact_code_match"
    unquoted = s.strip("`\"'")
    if unquoted in candidate_codes:
        return unquoted, "exact_after_strip_quotes"

    digit_map = _digits_to_canonical_codes(candidate_codes)
    raw_key = _soc_digits_key(s)
    if raw_key and raw_key in digit_map:
        return digit_map[raw_key], "digit_normalized_match"

    contained = [c for c in candidate_codes if c and c in s]
    if len(contained) == 1:
        return contained[0], "single_code_substring_of_response"
    if len(contained) > 1:
        return "unclassified", "ambiguous_multiple_catalog_codes_in_response"

    regex_hits = [
        m.group(0)
        for m in _SOC_CODE_IN_TEXT.finditer(s)
        if m.group(0) in candidate_codes
    ]
    unique_hits = list(dict.fromkeys(regex_hits))
    if len(unique_hits) == 1:
        return unique_hits[0], "regex_hyphenated_code_in_candidate_set"
    for m in _SOC_CODE_IN_TEXT.finditer(s):
        mk = _soc_digits_key(m.group(0))
        if mk and mk in digit_map:
            return digit_map[mk], "regex_then_digit_normalized"
    return "unclassified", "no_candidate_matched_llm_output"


def _resolve_llm_pick(raw: str, candidate_codes: set[str]) -> str:
    """Return a code from *candidate_codes* or ``unclassified``; never trust uncatalogued strings."""
    picked, _reason = _resolve_llm_pick_with_reason(raw, candidate_codes)
    return picked


def _soc_search_needles(title: str, description: str | None) -> list[str]:
    """Tokens for matching ``dbo.socc.title`` (mirrors NAICS needle breadth).

    The first title token alone often misses (e.g. *Senior* / *Remote* / *The*).
    """
    needles: list[str] = []
    for part in (title or "").strip().split():
        low = part.lower().strip(".,;:!?()[]\"'@#")
        if len(low) >= 3:
            needles.append(low)
            if len(needles) >= 5:
                break
    if len(needles) < 2 and description:
        try:
            from agents.enrichment.classification import tokenize

            for t in tokenize(description[:1200]):
                if len(t) >= 4 and t not in needles:
                    needles.append(t)
                if len(needles) >= 5:
                    break
        except Exception:
            pass
    if not needles:
        fw = _first_title_word_lower(title)
        if fw and len(fw) >= 2:
            needles = [fw]
    return needles[:5]


def _socc_version_clause():
    """Accept 2018 / 2010 rows; trim handles accidental whitespace in seeded ``version``."""
    v = func.trim(SOCC.version)
    return or_(v == "2018", v == "2010")


def _rank_and_dedupe_soc_candidates(
    rows: list[dict[str, str]],
    title: str,
    *,
    tech_profile: bool,
    limit: int = 15,
) -> list[dict[str, str]]:
    """Prefer computer/software SOC rows for tech titles; dedupe by code."""
    tl = (title or "").lower()
    toks = [t for t in re.findall(r"[a-z0-9]+", tl) if len(t) >= 4]

    def sort_key(row: dict[str, str]) -> tuple[int, int, str]:
        occ = (row.get("title") or "").lower()
        code = _soc_digits_key(row.get("code") or "")
        score = 0
        if tech_profile:
            if code.startswith("151"):
                score += 50
            elif code.startswith("15") and len(code) >= 4:
                score += 15
            for frag in ("software", "computer", "developer", "programmer", "database"):
                if frag in occ:
                    score += 12
            if "information" in occ and ("computer" in occ or "system" in occ):
                score += 10
            if "network" in occ and "computer" in occ:
                score += 10
            if "cloud" in tl and any(
                x in occ for x in ("software", "computer", "network", "system", "developer")
            ):
                score += 8
        for tok in toks:
            if tok in occ:
                score += 4
        return (-score, len(occ), row["code"])

    by_code: dict[str, dict[str, str]] = {}
    for r in rows:
        c = r.get("code", "")
        if c and c not in by_code:
            by_code[c] = r
    ranked = sorted(by_code.values(), key=sort_key)
    return ranked[:limit]


async def get_soc_candidates(
    title: str,
    description: str | None,
    session: Session,
) -> list[dict[str, str]]:
    needles = _soc_search_needles(title, description)
    if not needles:
        return []

    tech_profile = _title_has_tech_profile(title or "")
    needles_for_match = list(needles)
    if tech_profile:
        needles_for_match = [n for n in needles if n not in _GENERIC_ENGINEERING_NEEDLES]
        if not needles_for_match:
            needles_for_match = list(needles)

    branches: list = []
    if needles_for_match:
        branches.append(
            or_(*[func.lower(SOCC.title).contains(n) for n in needles_for_match])
        )
    if tech_profile:
        branches.append(
            or_(
                *[func.lower(SOCC.title).contains(f) for f in _TECH_SOCC_TITLE_FRAGMENTS]
            )
        )
    if not branches:
        return []

    where_match = or_(*branches) if len(branches) > 1 else branches[0]
    stmt = (
        select(SOCC.code, SOCC.title)
        .where(and_(_socc_version_clause(), where_match))
        .distinct()
        .limit(50)
    )

    diag_cloud_engineer = (title or "").strip() == _CLOUD_ENGINEER_DIAG_TITLE
    if diag_cloud_engineer:
        try:
            bind = session.get_bind()
            compiled = stmt.compile(bind)
            log.info(
                "soc_classifier_cloud_engineer_query",
                needles=list(needles),
                needles_for_match=list(needles_for_match),
                tech_profile=tech_profile,
                sql=str(compiled),
                sql_parameters=dict(compiled.params),
            )
        except Exception as exc:
            log.warning(
                "soc_classifier_cloud_engineer_sql_compile_failed",
                needles=list(needles),
                error=str(exc),
            )

    rows = session.execute(stmt).all()
    raw_out = [{"code": str(r[0]).strip(), "title": str(r[1]).strip()} for r in rows if r[0]]
    out = _rank_and_dedupe_soc_candidates(
        raw_out, title or "", tech_profile=tech_profile, limit=15
    )

    if diag_cloud_engineer:
        log.info(
            "soc_classifier_cloud_engineer_candidate_rows",
            candidate_count=len(out),
            raw_row_count_before_rank=len(raw_out),
            candidates=out,
        )

    return out


async def classify_soc(
    title: str,
    description: str,
    session: Session,
    llm: Callable[[str], str],
) -> str:
    candidates = await get_soc_candidates(title, description or None, session)
    if not candidates:
        return "unclassified"

    candidate_codes = {c["code"] for c in candidates}
    lines = [f'{c["code"]}: {c["title"]}' for c in candidates]
    candidates_block = "\n".join(lines)

    prompt = f"""Job Title: {title}
Job Description: {description or ""}

SOC Candidates:
{candidates_block}

Instructions:
- ONLY choose from the list above. DO NOT invent codes.
- If none match, return 'unclassified'.
- Reply with exactly one token: the chosen SOC code exactly as shown, or unclassified."""

    raw = llm(prompt)
    raw_stripped = (raw or "").strip()
    picked, resolution_reason = _resolve_llm_pick_with_reason(raw, candidate_codes)
    log.info(
        "soc_classifier_llm_resolution",
        title=(title or "")[:300],
        llm_raw=raw_stripped if len(raw_stripped) <= 2000 else raw_stripped[:2000] + "…",
        llm_raw_char_len=len(raw_stripped),
        llm_raw_truncated=len(raw_stripped) > 2000,
        picked_after_resolve=picked,
        resolution_reason=resolution_reason,
        candidate_codes_sample=sorted(candidate_codes)[:25],
        candidate_count=len(candidate_codes),
    )
    if picked == "unclassified":
        return "unclassified"
    canonical = _canonical_catalog_code(picked, candidate_codes)
    if canonical is None:
        log.warning(
            "soc_classifier_pick_failed_final_validation",
            picked=picked,
            note="not_in_candidate_set_even_after_digit_normalize",
        )
        return "unclassified"
    return canonical.strip()
