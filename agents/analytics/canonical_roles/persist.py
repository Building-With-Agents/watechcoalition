"""Persist clustering results: canonical_roles, job_postings.canonical_role_id, orphan cleanup."""

from __future__ import annotations

import re
import uuid
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from agents.analytics.clustering.types import ClusteringResult, RankedSkill, RankedTool
from agents.common.data_store.models import CanonicalRole

log = structlog.get_logger()

_ROLE_ID_NAMESPACE = uuid.UUID("2aa66a2d-6325-4309-b667-e73f2ba3e0a3")
_ROLE_TOKEN_SPLIT_RE = re.compile(r"\s+")


def _ranked_skills_json(skills: list[RankedSkill]) -> list[dict[str, Any]]:
    return [{"skill_name": s.skill_name, "count": s.count} for s in skills]


def _ranked_tools_json(tools: list[RankedTool]) -> list[dict[str, Any]]:
    return [{"tool_name": t.tool_name, "count": t.count} for t in tools]


def _normalize_role_token(value: object | None) -> str | None:
    if value is None:
        return None
    text_value = _ROLE_TOKEN_SPLIT_RE.sub(" ", str(value).strip()).casefold()
    return text_value or None


def _unique_normalized_tokens(values: Iterable[object | None], *, limit: int) -> tuple[str, ...]:
    tokens: list[str] = []
    seen: set[str] = set()
    for value in values:
        token = _normalize_role_token(value)
        if token is None or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
        if len(tokens) >= limit:
            break
    return tuple(tokens)


def _cluster_role_seed_parts(cluster: Any) -> tuple[str, str]:
    label = _normalize_role_token(getattr(cluster, "label", None))
    if label is None:
        label = _normalize_role_token(next(iter(getattr(cluster, "representative_titles", []) or []), None))
    if label is None:
        label = "unlabeled-role"

    disambiguators = _unique_normalized_tokens(
        [
            *(getattr(cluster, "representative_titles", []) or []),
            *[skill.skill_name for skill in getattr(cluster, "top_skills", []) or []],
            *[tool.tool_name for tool in getattr(cluster, "top_tools", []) or []],
        ],
        limit=6,
    )
    return label, "|".join(disambiguators)


def _build_cluster_role_ids(clusters: list[Any]) -> dict[str, str]:
    base_counts = Counter(_cluster_role_seed_parts(cluster)[0] for cluster in clusters)
    role_ids: dict[str, str] = {}

    for cluster in clusters:
        label_seed, disambiguator = _cluster_role_seed_parts(cluster)
        seed = f"canonical-role|{label_seed}"
        if base_counts[label_seed] > 1 and disambiguator:
            seed = f"{seed}|{disambiguator}"
        role_ids[cluster.cluster_id] = str(uuid.uuid5(_ROLE_ID_NAMESPACE, seed))

    return role_ids


def persist_clustering_result(
    session: Session,
    result: ClusteringResult,
    *,
    correlation_id: str,
) -> dict[str, Any]:
    """Insert or update canonical roles, then map postings to their stable role ids.

    Assigns a deterministic UUID ``role_id`` per cluster signature so canonical role ids
    remain stable across reruns when the role label/signature is stable.
    Updates only postings that appear in ``result.assignments`` (embedded + clustered rows);
    noise rows get NULL ``canonical_role_id``. Postings without embeddings are unchanged.

    Returns a dict including ``cluster_id_to_role_id`` for alert mapping.
    """
    if result.skipped:
        log.info("clustering_persist_skipped", reason=result.skip_reason, correlation_id=correlation_id)
        return {"cluster_id_to_role_id": {}, "roles_inserted": 0, "postings_updated": 0, "orphans_deleted": 0}

    cluster_id_to_role_id = _build_cluster_role_ids(list(result.clusters))
    desired_role_ids = set(cluster_id_to_role_id.values())
    existing_roles = {
        row.role_id: row
        for row in session.execute(select(CanonicalRole).where(CanonicalRole.role_id.in_(desired_role_ids)))
        .scalars()
        .all()
    }

    now = datetime.now(timezone.utc)
    roles_inserted = 0

    for cluster in result.clusters:
        role_id = cluster_id_to_role_id[cluster.cluster_id]
        row = existing_roles.get(role_id)
        if row is None:
            row = CanonicalRole(role_id=role_id)
            session.add(row)
            roles_inserted += 1

        row.label = cluster.label or f"cluster_{cluster.raw_cluster_label}"
        row.description = cluster.description
        row.posting_count = cluster.member_count
        row.cluster_centroid = list(cluster.centroid_embedding) if cluster.centroid_embedding else None
        row.representative_titles = list(cluster.representative_titles)
        row.top_skills = _ranked_skills_json(list(cluster.top_skills)) if cluster.top_skills else None
        row.top_tools = _ranked_tools_json(list(cluster.top_tools)) if cluster.top_tools else None
        row.is_llm_generated = cluster.is_llm_generated_label
        row.computed_at = now
        row.updated_at = now

    session.flush()

    postings_updated = 0
    for a in result.assignments:
        pid = a.posting_id
        if a.is_noise:
            session.execute(
                text("UPDATE dbo.job_postings SET canonical_role_id = NULL WHERE job_posting_id = CAST(:pid AS text)"),
                {"pid": pid},
            )
            postings_updated += 1
            continue
        cid = a.cluster_id
        if cid is None:
            session.execute(
                text("UPDATE dbo.job_postings SET canonical_role_id = NULL WHERE job_posting_id = CAST(:pid AS text)"),
                {"pid": pid},
            )
            postings_updated += 1
            continue
        role_id = cluster_id_to_role_id.get(cid)
        if role_id is None:
            session.execute(
                text("UPDATE dbo.job_postings SET canonical_role_id = NULL WHERE job_posting_id = CAST(:pid AS text)"),
                {"pid": pid},
            )
            postings_updated += 1
            continue
        session.execute(
            text("UPDATE dbo.job_postings SET canonical_role_id = :rid WHERE job_posting_id = CAST(:pid AS text)"),
            {"rid": role_id, "pid": pid},
        )
        postings_updated += 1

    log.info(
        "clustering_persisted",
        correlation_id=correlation_id,
        roles_inserted=roles_inserted,
        postings_updated=postings_updated,
        role_count=len(result.clusters),
    )

    return {
        "cluster_id_to_role_id": cluster_id_to_role_id,
        "roles_inserted": roles_inserted,
        "postings_updated": postings_updated,
        "orphans_deleted": 0,
    }


def cleanup_orphan_canonical_roles(session: Session) -> int:
    """Delete canonical roles that are no longer referenced by postings or snapshots."""
    orphan_result = session.execute(
        text(
            """
            DELETE FROM dbo.canonical_roles cr
            WHERE NOT EXISTS (
                SELECT 1 FROM dbo.job_postings jp
                WHERE jp.canonical_role_id = cr.role_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM dbo.role_snapshot_weekly rsw
                WHERE rsw.canonical_role_id = cr.role_id
            )
            """
        )
    )
    orphans_deleted = orphan_result.rowcount or 0
    log.info("canonical_roles_orphan_cleanup_complete", orphans_deleted=orphans_deleted)
    return orphans_deleted
