# ruff: noqa: T201
"""Run canonical role clustering on live DB data and print findings.

Usage:
    python agents/scripts/run_clustering.py
    python agents/scripts/run_clustering.py --min-postings 100
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agents.common.env import load_repo_root_dotenv

load_repo_root_dotenv()

from agents.analytics.canonical_roles.loader import load_posting_cluster_features
from agents.analytics.canonical_roles.persist import (
    cleanup_orphan_canonical_roles,
    persist_clustering_result,
)
from agents.analytics.canonical_roles.snapshots import refresh_role_snapshot_weekly
from agents.analytics.clustering.config import cluster_min_total_postings
from agents.analytics.clustering.embeddings import embed_posting_features
from agents.analytics.clustering.pipeline import run_clustering_pipeline
from agents.common.data_store.database import check_db_connection, session_scope


def _iso_week_monday(today: date) -> date:
    return today - timedelta(days=today.weekday())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-postings", type=int, default=None)
    args = parser.parse_args()

    if args.min_postings is not None:
        os.environ["CLUSTER_MIN_TOTAL_POSTINGS"] = str(args.min_postings)

    if not check_db_connection():
        print("ERROR: DB not reachable")
        sys.exit(1)

    print("=" * 70)
    print("CANONICAL ROLE CLUSTERING — LIVE DATA RUN")
    print("=" * 70)

    with session_scope() as session:
        features = load_posting_cluster_features(session)
        min_threshold = cluster_min_total_postings()
        print(f"\nFeatures loaded:  {len(features)}")
        print(f"Min threshold:    {min_threshold}")

        if len(features) < min_threshold:
            print(f"SKIP: {len(features)} < {min_threshold}")
            return

        with_skills = sum(1 for f in features if f.skills)
        with_tools = sum(1 for f in features if f.tools)
        with_resp = sum(1 for f in features if f.responsibilities)
        print(f"With skills:      {with_skills} ({100*with_skills/len(features):.1f}%)")
        print(f"With tools:       {with_tools} ({100*with_tools/len(features):.1f}%)")
        print(f"With respons.:    {with_resp} ({100*with_resp/len(features):.1f}%)")

        print("\n--- Generating embeddings (Azure OpenAI) ---")
        embedded = embed_posting_features(features, allow_partial=False)
        if embedded is None:
            print("ERROR: Embedding generation failed")
            sys.exit(1)
        print(f"Embeddings count: {len(embedded)}")

        print("\n--- Running HDBSCAN clustering ---")
        result = run_clustering_pipeline(features, embedded)

        if result.skipped:
            print(f"SKIP: {result.skip_reason}")
            return

        print("\nClustering results:")
        print(f"  Total input:        {result.total_input_postings}")
        print(f"  Eligible:           {result.eligible_posting_count}")
        print(f"  Clusters found:     {len(result.clusters)}")
        print(f"  Noise postings:     {result.noise_posting_count}")
        print(f"  Noise rate:         {100*result.noise_posting_count/result.eligible_posting_count:.1f}%")
        print(f"  Emergence cands:    {len(result.emergence_candidates)}")

        print("\n--- Top clusters ---")
        sorted_clusters = sorted(result.clusters, key=lambda c: c.member_count, reverse=True)
        for i, cl in enumerate(sorted_clusters[:20], 1):
            skills_str = ", ".join(s.skill_name for s in cl.top_skills[:5])
            tools_str = ", ".join(t.tool_name for t in cl.top_tools[:3])
            print(f"  {i:>2}. [{cl.member_count:>3} posts] {cl.label}")
            print(f"      Skills: {skills_str}")
            if tools_str:
                print(f"      Tools:  {tools_str}")
            print(f"      Titles: {', '.join(cl.representative_titles[:3])}")

        if result.emergence_candidates:
            print("\n--- Emergence candidates ---")
            for ec in result.emergence_candidates:
                print(f"  - {ec.candidate_role_label} ({ec.posting_count} posts)")
                print(f"    Novel skills: {[s.skill_name for s in ec.top_skills[:5]]}")
                print(f"    Reason: {ec.filter_reason}")

        print("\n--- Persisting to DB ---")
        persist_info = persist_clustering_result(
            session, result, correlation_id="week7-clustering-run"
        )
        print(f"  Roles inserted:    {persist_info.get('roles_inserted')}")
        print(f"  Postings updated:  {persist_info.get('postings_updated')}")

        week_start = _iso_week_monday(date.today())
        print(f"\n--- Role snapshot weekly (week_start={week_start}) ---")
        snapshot_rows = refresh_role_snapshot_weekly(session, week_start=week_start)
        print(f"  Snapshot rows:     {snapshot_rows}")

        orphans = cleanup_orphan_canonical_roles(session)
        print(f"  Orphans cleaned:   {orphans}")

        print("\n" + "=" * 70)
        print("DONE — query canonical_roles and role_snapshot_weekly for findings")
        print("=" * 70)

        findings = {
            "run_date": date.today().isoformat(),
            "features_loaded": len(features),
            "skills_coverage": f"{100*with_skills/len(features):.1f}%",
            "tools_coverage": f"{100*with_tools/len(features):.1f}%",
            "clusters_found": len(result.clusters),
            "noise_count": result.noise_posting_count,
            "noise_rate": f"{100*result.noise_posting_count/result.eligible_posting_count:.1f}%",
            "emergence_candidates": len(result.emergence_candidates),
            "roles_persisted": persist_info.get("roles_inserted"),
            "snapshot_rows": snapshot_rows,
            "top_clusters": [
                {
                    "label": cl.label,
                    "posting_count": cl.member_count,
                    "top_skills": [s.skill_name for s in cl.top_skills[:5]],
                    "top_tools": [t.tool_name for t in cl.top_tools[:3]],
                    "representative_titles": cl.representative_titles[:3],
                }
                for cl in sorted_clusters[:20]
            ],
            "emergence_details": [
                {
                    "label": ec.candidate_role_label,
                    "count": ec.posting_count,
                    "novel_skills": [s.skill_name for s in ec.top_skills[:5]],
                    "reason": ec.filter_reason,
                }
                for ec in result.emergence_candidates
            ],
        }

        out_path = Path(__file__).parent.parent / "data" / "analytics" / "clustering_findings.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(findings, indent=2, default=str), encoding="utf-8")
        print(f"\nFindings JSON saved to: {out_path}")


if __name__ == "__main__":
    main()
