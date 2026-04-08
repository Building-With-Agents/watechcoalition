"""Persist clustering results: canonical_roles, job_postings.canonical_role_id, orphan cleanup."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from agents.analytics.clustering.types import ClusteringResult, RankedSkill, RankedTool
from agents.common.data_store.models import CanonicalRole

log = structlog.get_logger()


def _ranked_skills_json(skills: list[RankedSkill]) -> list[dict[str, Any]]:
    return [{"skill_name": s.skill_name, "count": s.count} for s in skills]


def _ranked_tools_json(tools: list[RankedTool]) -> list[dict[str, Any]]:
    return [{"tool_name": t.tool_name, "count": t.count} for t in tools]


def persist_clustering_result(
    session: Session,
    result: ClusteringResult,
    *,
    correlation_id: str,
) -> dict[str, Any]:
    """Insert canonical roles, update postings, remove unreferenced roles.

    Assigns a new stable UUID ``role_id`` per ``ClusterSummary.cluster_id`` for this run.
    Updates only postings that appear in ``result.assignments`` (embedded + clustered rows);
    noise rows get NULL ``canonical_role_id``. Postings without embeddings are unchanged.

    Returns a dict including ``cluster_id_to_role_id`` for alert mapping.
    """
    if result.skipped:
        log.info("clustering_persist_skipped", reason=result.skip_reason, correlation_id=correlation_id)
        return {"cluster_id_to_role_id": {}, "roles_inserted": 0, "postings_updated": 0, "orphans_deleted": 0}

    cluster_id_to_role_id: dict[str, str] = {}
    for cluster in result.clusters:
        cluster_id_to_role_id[cluster.cluster_id] = str(uuid.uuid4())

    now = datetime.now(timezone.utc)

    for cluster in result.clusters:
        role_id = cluster_id_to_role_id[cluster.cluster_id]
        row = CanonicalRole(
            role_id=role_id,
            label=cluster.label or f"cluster_{cluster.raw_cluster_label}",
            description=cluster.description,
            posting_count=cluster.member_count,
            cluster_centroid=list(cluster.centroid_embedding) if cluster.centroid_embedding else None,
            representative_titles=list(cluster.representative_titles),
            top_skills=_ranked_skills_json(list(cluster.top_skills)) if cluster.top_skills else None,
            top_tools=_ranked_tools_json(list(cluster.top_tools)) if cluster.top_tools else None,
            is_llm_generated=cluster.is_llm_generated_label,
            computed_at=now,
        )
        session.add(row)

    session.flush()

    postings_updated = 0
    for a in result.assignments:
        pid = a.posting_id
        if a.is_noise:
            session.execute(
                text("UPDATE dbo.job_postings SET canonical_role_id = NULL WHERE job_posting_id = CAST(:pid AS uuid)"),
                {"pid": pid},
            )
            postings_updated += 1
            continue
        cid = a.cluster_id
        if cid is None:
            session.execute(
                text("UPDATE dbo.job_postings SET canonical_role_id = NULL WHERE job_posting_id = CAST(:pid AS uuid)"),
                {"pid": pid},
            )
            postings_updated += 1
            continue
        role_id = cluster_id_to_role_id.get(cid)
        if role_id is None:
            session.execute(
                text("UPDATE dbo.job_postings SET canonical_role_id = NULL WHERE job_posting_id = CAST(:pid AS uuid)"),
                {"pid": pid},
            )
            postings_updated += 1
            continue
        session.execute(
            text("UPDATE dbo.job_postings SET canonical_role_id = :rid WHERE job_posting_id = CAST(:pid AS uuid)"),
            {"rid": role_id, "pid": pid},
        )
        postings_updated += 1

    orphan_result = session.execute(
        text(
            """
            DELETE FROM dbo.canonical_roles cr
            WHERE NOT EXISTS (
                SELECT 1 FROM dbo.job_postings jp
                WHERE jp.canonical_role_id = cr.role_id
            )
            """
        )
    )
    orphans_deleted = orphan_result.rowcount or 0

    log.info(
        "clustering_persisted",
        correlation_id=correlation_id,
        roles_inserted=len(result.clusters),
        postings_updated=postings_updated,
        orphans_deleted=orphans_deleted,
    )

    return {
        "cluster_id_to_role_id": cluster_id_to_role_id,
        "roles_inserted": len(result.clusters),
        "postings_updated": postings_updated,
        "orphans_deleted": orphans_deleted,
    }
