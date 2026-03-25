"""Sync ESCO skill embeddings from Azure PostgreSQL to local PostgreSQL.

Pulls pre-computed embeddings from the shared Azure database and writes them
to your local PostgreSQL. No Azure OpenAI API calls — zero LLM cost.

Usage:
    cd agents
    .venv\\Scripts\\Activate.ps1   # Windows
    # source .venv/bin/activate   # macOS/Linux

    python scripts/sync_embeddings_from_azure.py

    # Check status only (no sync):
    python scripts/sync_embeddings_from_azure.py --status

    # Override Azure source URL:
    python scripts/sync_embeddings_from_azure.py --azure-url "postgresql+psycopg2://..."

Prerequisites:
    - Local PostgreSQL running with dbo.skills table (run migrations first)
    - Azure PostgreSQL has embeddings (admin ran seed_esco_embeddings.py)
    - PYTHON_DATABASE_URL in .env points to your LOCAL database
    - AZURE_DATABASE_URL in .env points to the shared Azure database
      (or pass --azure-url)

What it does:
    1. Connects to Azure PostgreSQL (read-only)
    2. Reads all (skill_name, embedding) pairs where embedding IS NOT NULL
    3. Connects to your local PostgreSQL
    4. For each skill that exists locally with NULL embedding, writes the vector
    5. Reports: matched, skipped (already has embedding), missing (not in local DB)
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import structlog
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add repo root so agents.* imports work from any CWD
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _repo_root)

# Load .env — check repo root first, then agents/, then CWD
load_dotenv(os.path.join(_repo_root, ".env"))
load_dotenv(os.path.join(_repo_root, "agents", ".env"))
load_dotenv()  # fallback: CWD

from agents.common.data_store.database import session_scope  # noqa: E402

log = structlog.get_logger()

# Default Azure connection — override with --azure-url or AZURE_DATABASE_URL env var
_DEFAULT_AZURE_URL = (
    "postgresql+psycopg2://azadmin:Jx9gfIHmmiXq4yyR9bdUTVU%40k"
    "@pg-jobintel-cfa-dev.postgres.database.azure.com:5432"
    "/talent_finder?sslmode=require"
)


def _get_azure_url(cli_override: str | None = None) -> str:
    """Resolve Azure DB URL from CLI arg > env var > default."""
    if cli_override:
        return cli_override
    return os.getenv("AZURE_DATABASE_URL", _DEFAULT_AZURE_URL)


def status_local() -> dict[str, int]:
    """Check local DB embedding status."""
    with session_scope() as s:
        total = s.execute(text("SELECT COUNT(*) FROM dbo.skills")).scalar() or 0
        with_emb = (
            s.execute(
                text("SELECT COUNT(*) FROM dbo.skills WHERE embedding IS NOT NULL")
            ).scalar()
            or 0
        )
    return {"total": total, "with_embeddings": with_emb, "missing": total - with_emb}


def sync(azure_url: str) -> None:
    """Pull embeddings from Azure and write to local DB."""

    # --- Step 1: Read from Azure ---
    log.info("connecting_to_azure")
    azure_engine = create_engine(azure_url, echo=False)

    with azure_engine.connect() as conn:
        azure_rows = conn.execute(
            text(
                "SELECT skill_name, embedding::text "
                "FROM dbo.skills WHERE embedding IS NOT NULL "
                "ORDER BY skill_name"
            )
        ).fetchall()

    azure_engine.dispose()
    log.info("azure_read_complete", skills_with_embeddings=len(azure_rows))

    if not azure_rows:
        log.error("no_embeddings_on_azure", hint="Admin needs to run seed_esco_embeddings.py first")
        return

    # Build lookup: skill_name -> embedding vector string
    azure_embeddings: dict[str, str] = {}
    for row in azure_rows:
        skill_name = row[0]
        vec_str = row[1]  # Already a string from ::text cast
        azure_embeddings[skill_name] = vec_str

    # --- Step 2: Check local status ---
    local_status = status_local()
    log.info("local_status_before", **local_status)

    if local_status["missing"] == 0:
        log.info("sync_not_needed", message="All local skills already have embeddings")
        return

    # --- Step 3: Write to local DB ---
    updated = 0
    skipped_has_embedding = 0
    skipped_not_in_azure = 0

    with session_scope() as s:
        # Get local skills that need embeddings
        local_rows = s.execute(
            text(
                "SELECT skill_id, skill_name FROM dbo.skills "
                "WHERE embedding IS NULL ORDER BY skill_name"
            )
        ).fetchall()

        for skill_id, skill_name in local_rows:
            vec_str = azure_embeddings.get(skill_name)
            if vec_str is None:
                skipped_not_in_azure += 1
                continue

            # Parse the vector string and re-serialize as JSON for the CAST
            try:
                vec_list = json.loads(vec_str)
                vec_json = json.dumps(vec_list)
            except (json.JSONDecodeError, TypeError):
                # vec_str might be in pgvector format [1,2,3] — try direct
                vec_json = vec_str

            s.execute(
                text(
                    "UPDATE dbo.skills SET embedding = CAST(:vec AS vector), "
                    "updatedat = NOW() WHERE skill_id = :sid"
                ),
                {"vec": vec_json, "sid": skill_id},
            )
            updated += 1

            if updated % 500 == 0:
                log.info("sync_progress", updated=updated, total=len(local_rows))

    log.info(
        "sync_complete",
        updated=updated,
        skipped_already_had_embedding=skipped_has_embedding,
        skipped_not_in_azure=skipped_not_in_azure,
    )

    # --- Step 4: Final status ---
    final = status_local()
    log.info("local_status_after", **final)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync ESCO embeddings from Azure PostgreSQL to local DB (zero LLM cost)"
    )
    parser.add_argument("--status", action="store_true", help="Check local status only")
    parser.add_argument(
        "--azure-url",
        type=str,
        default=None,
        help="Override Azure PostgreSQL URL (default: AZURE_DATABASE_URL env var)",
    )
    args = parser.parse_args()

    if args.status:
        s = status_local()
        log.info("local_embedding_status", **s)
    else:
        azure_url = _get_azure_url(args.azure_url)
        sync(azure_url)


if __name__ == "__main__":
    main()
