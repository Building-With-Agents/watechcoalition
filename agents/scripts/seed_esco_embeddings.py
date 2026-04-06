"""Seed ESCO skill embeddings into PostgreSQL — ADMIN ONLY.

Embeds all skills in dbo.skills where embedding IS NULL using Azure OpenAI
text-embedding-3-small, then stores the vector in the pgvector column.

This script should be run ONCE by an admin against the Azure PostgreSQL
database. Devs pull embeddings from Azure to their local DB — they should
NEVER run this script against Azure OpenAI (it costs money and hits rate
limits).

Usage:
    # Against Azure PostgreSQL (admin only):
    PYTHON_DATABASE_URL=$AZURE_POSTGRES_DATABASE_URL \\
        python agents/scripts/seed_esco_embeddings.py

    # Check status without seeding:
    python agents/scripts/seed_esco_embeddings.py --status

Environment:
    PYTHON_DATABASE_URL          PostgreSQL connection string
    AZURE_OPENAI_EMBEDDING_ENDPOINT
    AZURE_OPENAI_EMBEDDING_API_KEY
    AZURE_OPENAI_EMBEDDING_API_VERSION   (default: 2024-02-01)
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import httpx
import structlog
from dotenv import load_dotenv
from sqlalchemy import text

# Add repo root so agents.* imports work from any CWD
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _repo_root)

# Load .env — check repo root first, then agents/, then CWD
load_dotenv(os.path.join(_repo_root, ".env"))
load_dotenv(os.path.join(_repo_root, "agents", ".env"))
load_dotenv()  # fallback: CWD

from agents.common.data_store.database import session_scope  # noqa: E402

log = structlog.get_logger()

BATCH_SIZE = 50
EMBEDDING_DIMENSIONS = 1536


def _embed_batch(texts: list[str]) -> list[list[float]] | None:
    """Call Azure OpenAI Embeddings API for a batch of texts."""
    endpoint = (os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT") or "").rstrip("/")
    api_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION", "2024-02-01")
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

    if not endpoint or not api_key or not deployment:
        log.error("missing_embedding_env_vars")
        return None

    url = f"{endpoint}/openai/deployments/{deployment}/embeddings?api-version={api_version}"
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    payload = {"input": texts if len(texts) > 1 else texts[0]}

    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code == 429:
                    import re

                    match = re.search(r"retry after (\d+)\s*seconds?", resp.text, re.IGNORECASE)
                    delay = int(match.group(1)) if match else 2**attempt
                    log.warning("embedding_rate_limited", attempt=attempt, delay_s=delay)
                    if attempt == max_retries:
                        return None
                    time.sleep(delay)
                    continue
                resp.raise_for_status()
                data = resp.json()
                break
        except Exception as exc:
            log.warning("embedding_api_error", attempt=attempt, error=str(exc))
            if attempt == max_retries:
                return None
            time.sleep(2**attempt)
            continue
    else:
        return None

    items = data.get("data", [])
    return [item["embedding"] for item in items if "embedding" in item]


def status() -> None:
    """Log embedding status without modifying anything."""
    with session_scope() as s:
        total = s.execute(text("SELECT COUNT(*) FROM dbo.skills")).scalar()
        with_emb = s.execute(text("SELECT COUNT(*) FROM dbo.skills WHERE embedding IS NOT NULL")).scalar()
        log.info("embedding_status", total=total, with_embeddings=with_emb, missing=total - with_emb)


def seed() -> None:
    """Embed all skills with NULL embeddings and store in PostgreSQL."""
    with session_scope() as s:
        rows = s.execute(
            text("SELECT skill_id, skill_name FROM dbo.skills WHERE embedding IS NULL ORDER BY skill_name")
        ).fetchall()

    if not rows:
        log.info("seed_complete", message="All skills already have embeddings")
        return

    total_batches = (len(rows) + BATCH_SIZE - 1) // BATCH_SIZE
    log.info("seed_start", skills=len(rows), batch_size=BATCH_SIZE, total_batches=total_batches)
    embedded_count = 0

    for batch_idx in range(0, len(rows), BATCH_SIZE):
        batch = rows[batch_idx : batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1
        names = [row[1] for row in batch]
        ids = [row[0] for row in batch]

        vectors = _embed_batch(names)
        if not vectors or len(vectors) != len(batch):
            log.error(
                "batch_failed",
                batch=batch_num,
                expected=len(batch),
                got=len(vectors) if vectors else 0,
            )
            break

        with session_scope() as s:
            for skill_id, vector in zip(ids, vectors, strict=True):
                vec_str = json.dumps(vector)
                s.execute(
                    text(
                        "UPDATE dbo.skills SET embedding = CAST(:vec AS vector), "
                        "updatedat = NOW() WHERE skill_id = :sid"
                    ),
                    {"vec": vec_str, "sid": skill_id},
                )

        embedded_count += len(batch)
        log.info("batch_complete", batch=batch_num, total=total_batches, embedded=embedded_count)

    log.info("seed_complete", embedded=embedded_count)
    status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ESCO skill embeddings (admin only)")
    parser.add_argument("--status", action="store_true", help="Print status without seeding")
    args = parser.parse_args()

    if args.status:
        status()
    else:
        seed()


if __name__ == "__main__":
    main()
