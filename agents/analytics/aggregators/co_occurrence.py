"""Skill pair co-occurrence aggregates (Analytics step 9).

Join path and spam/dedup/extraction filters match
:mod:`agents.analytics.aggregators.demand_weekly` (``_SKILLS_EXPANDED``).

Per posting, skills are deduped, sorted, capped at 20, then unordered pairs are
counted with **lexicographic** ``skill_a < skill_b`` so each pair appears once
(symmetric matrix, no ``(B,A)`` duplicate of ``(A,B)``). Only the top 200 pairs
by frequency are persisted (ties: ascending ``skill_a``, then ``skill_b``).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from itertools import combinations

import structlog
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from agents.analytics.aggregators.demand_weekly import _SKILLS_EXPANDED
from agents.common.data_store.models import SkillCoOccurrence
from agents.enrichment.classifiers.spam_preview import get_spam_thresholds

log = structlog.get_logger()

_TOP_PAIR_LIMIT = 200


def _extract_cooccurrence_pairs(posting_skills: list[list[str]]) -> dict[tuple[str, str], int]:
    """Count skill co-occurrences. Returns: ``{(skill_a, skill_b): count}``."""
    pairs: dict[tuple[str, str], int] = {}
    for skills in posting_skills:
        unique = sorted(set(skills))[:20]  # Cap per-posting to prevent explosion
        for a, b in combinations(unique, 2):
            skill_a, skill_b = sorted((a, b))
            pairs[(skill_a, skill_b)] = pairs.get((skill_a, skill_b), 0) + 1
    # Top N by count; ties broken by (skill_a, skill_b) so SQL verification matches.
    ranked = sorted(
        pairs.items(),
        key=lambda kv: (-kv[1], kv[0][0], kv[0][1]),
    )[:_TOP_PAIR_LIMIT]
    return dict(ranked)


def refresh_skill_co_occurrence(session: Session, week_start: date) -> int:
    """Delete then recompute ``dbo.skill_co_occurrence`` for ``week_start``.

    Returns number of rows inserted (at most ``_TOP_PAIR_LIMIT``).
    """
    _, reject_threshold = get_spam_thresholds()
    computed_at = datetime.now(timezone.utc)
    binds = {"week_start": week_start, "reject_threshold": reject_threshold}

    expanded = _SKILLS_EXPANDED.subquery("exp_skills")
    stmt = select(expanded.c.job_posting_id, expanded.c.skill_label).select_from(expanded)

    result_rows = session.execute(stmt, binds).all()

    by_posting: dict[str, list[str]] = defaultdict(list)
    for job_posting_id, skill_label in result_rows:
        by_posting[str(job_posting_id)].append(str(skill_label))

    posting_skills = list(by_posting.values())
    pairs = _extract_cooccurrence_pairs(posting_skills)

    t = SkillCoOccurrence.__table__
    session.execute(delete(t).where(t.c.week_start == week_start))

    if not pairs:
        log.info(
            "skill_co_occurrence_refreshed_empty",
            week_start=str(week_start),
            rows_inserted=0,
        )
        return 0

    payload = [
        {
            "skill_a": a,
            "skill_b": b,
            "co_occurrence_count": cnt,
            "week_start": week_start,
            "computed_at": computed_at,
        }
        for (a, b), cnt in pairs.items()
    ]
    session.execute(insert(t), payload)
    inserted = len(payload)
    log.info(
        "skill_co_occurrence_refreshed",
        week_start=str(week_start),
        rows_inserted=inserted,
    )
    return inserted
