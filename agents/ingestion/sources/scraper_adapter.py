"""
Scraper adapter for ingestion using Crawl4AI.

This module:
- Reads the target URL from the SCRAPER_TARGET_URL environment variable
- Uses Crawl4AI's AsyncWebCrawler to fetch the page
- Extracts raw text content (no PII processing or enrichment)
- Writes a small sample of 5–10 "postings" to agents/data/staging/raw_scrape_sample.json

Each JSON record includes:
- source: identifier for this adapter
- url: page URL
- timestamp: UTC ISO-8601
- raw_text: raw text content

Logging:
- Uses structlog
- Does NOT log PII — only metadata such as URL and record counts
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import structlog
from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

log = structlog.get_logger()


@dataclass
class RawScrapeRecord:
    source: str
    url: str
    timestamp: str
    raw_text: str


def load_env() -> None:
    """Load environment variables from common .env locations, if present."""
    repo_root = Path(__file__).resolve().parents[3]
    candidate_paths = [
        repo_root / ".env",
        repo_root / "agents" / ".env",
        repo_root / "agents" / ".env.example",
    ]

    for env_path in candidate_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)
            break


def get_target_url() -> str:
    """Read the scraper target URL from SCRAPER_TARGET_URL."""
    url = os.getenv("SCRAPER_TARGET_URL")
    if not url:
        raise RuntimeError(
            "SCRAPER_TARGET_URL is not set. "
            "Set it in your .env to the page you want to scrape."
        )
    return url


def get_output_path() -> Path:
    """Return the path where the raw scrape sample will be written."""
    repo_root = Path(__file__).resolve().parents[3]
    staging_dir = repo_root / "agents" / "data" / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    return staging_dir / "raw_scrape_sample.json"


async def scrape_page(url: str, max_records: int = 10) -> List[RawScrapeRecord]:
    """
    Use Crawl4AI AsyncWebCrawler to fetch a page and create sample records.

    Crawl4AI returns a single result for the URL; we slice the content into
    coarse chunks to simulate 5–10 separate postings without parsing PII.
    """
    log.info("scraper_start", url=url)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

    # Prefer markdown if available; fall back to raw HTML/text attributes
    text = getattr(result, "markdown", None) or getattr(result, "cleaned_html", None) or ""
    text = text.strip()

    if not text:
        log.warning("scraper_empty_content", url=url)
        return []

    # Simple heuristic: split by headings or double newlines to create "chunks"
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]

    if not chunks:
        # Fallback: treat entire page as one record
        chunks = [text]

    # Bound number of records between 5 and max_records, if possible
    desired = min(max_records, len(chunks))
    if desired < 5 and len(chunks) >= 1:
        desired = len(chunks)

    selected = chunks[:desired]
    now = datetime.now(timezone.utc).isoformat()

    records = [
        RawScrapeRecord(
            source="crawl4ai_scraper",
            url=url,
            timestamp=now,
            raw_text=chunk,
        )
        for chunk in selected
    ]

    log.info(
        "raw_scrape_result",
        url=url,
        record_count=len(records),
    )

    return records


def save_records(path: Path, records: List[RawScrapeRecord]) -> None:
    """Serialize records to JSON at the given path."""
    serializable = [asdict(r) for r in records]
    path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    log.info(
        "raw_scrape_saved",
        path=str(path),
        record_count=len(records),
    )


async def run() -> None:
    """Entry point for async scraping and persistence."""
    load_env()
    url = get_target_url()
    output_path = get_output_path()

    records = await scrape_page(url=url, max_records=10)
    if not records:
        log.warning("raw_scrape_no_records", url=url)
        return

    save_records(output_path, records)


def main() -> None:
    """Synchronous wrapper for CLI execution."""
    asyncio.run(run())


if __name__ == "__main__":
    main()

