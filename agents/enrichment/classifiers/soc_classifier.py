"""SOC occupation classification using dbo.socc reference rows only (2018)."""

from __future__ import annotations

import re
from collections.abc import Callable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agents.common.data_store.models import SOCC

# Extract SOC-shaped tokens from noisy LLM text; matches are kept only if in candidate_codes.
_SOC_CODE_IN_TEXT = re.compile(r"\d{2}-\d{4}(?:\.\d{2})?")


def _first_title_word_lower(title: str) -> str | None:
    parts = (title or "").strip().split()
    if not parts:
        return None
    return parts[0].lower()


def _resolve_llm_pick(raw: str, candidate_codes: set[str]) -> str:
    """Return a code from *candidate_codes* or ``unclassified``; never trust uncatalogued strings."""
    s = (raw or "").strip()
    if not s or s.lower() == "unclassified":
        return "unclassified"
    if s in candidate_codes:
        return s
    unquoted = s.strip("`\"'")
    if unquoted in candidate_codes:
        return unquoted
    contained = [c for c in candidate_codes if c and c in s]
    if len(contained) == 1:
        return contained[0]
    if len(contained) > 1:
        return "unclassified"
    regex_hits = [
        m.group(0)
        for m in _SOC_CODE_IN_TEXT.finditer(s)
        if m.group(0) in candidate_codes
    ]
    unique_hits = list(dict.fromkeys(regex_hits))
    if len(unique_hits) == 1:
        return unique_hits[0]
    return "unclassified"


async def get_soc_candidates(title: str, session: Session) -> list[dict[str, str]]:
    needle = _first_title_word_lower(title)
    if not needle:
        return []

    stmt = (
        select(SOCC.code, SOCC.title)
        .where(SOCC.version == "2018")
        .where(func.lower(SOCC.title).contains(needle))
        .limit(10)
    )
    rows = session.execute(stmt).all()
    return [{"code": str(r[0]).strip(), "title": str(r[1]).strip()} for r in rows if r[0]]


async def classify_soc(
    title: str,
    description: str,
    session: Session,
    llm: Callable[[str], str],
) -> str:
    candidates = await get_soc_candidates(title, session)
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
    picked = _resolve_llm_pick(raw, candidate_codes)
    if picked == "unclassified":
        return "unclassified"
    if picked not in candidate_codes:
        return "unclassified"
    return picked.strip()
