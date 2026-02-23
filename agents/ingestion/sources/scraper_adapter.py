"""
Crawl4AI scraper adapter — Exercise 1.2

Scrapes job postings from configured target URLs using Crawl4AI and writes
raw output to agents/data/staging/raw_scrape_sample.json.

Usage:
    python -m agents.ingestion.sources.scraper_adapter
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import structlog
from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

load_dotenv()

log = structlog.get_logger()

DEFAULT_SCRAPING_TARGETS = [
    "https://jobs.lever.co/openai",
    "https://jobs.lever.co/anthropic",
]

OUTPUT_PATH = Path(__file__).resolve().parents[3] / "data" / "staging" / "raw_scrape_sample.json"


def _get_targets() -> list[str]:
    raw = os.getenv("SCRAPING_TARGETS", "")
    if raw.strip():
        return [url.strip() for url in raw.split(",") if url.strip()]
    return DEFAULT_SCRAPING_TARGETS


def _extract_postings(url: str, markdown: str, max_per_page: int = 5) -> list[dict]:
    """
    Extract individual job posting blocks from crawled markdown text.
    Splits on blank-line-separated sections and returns the first max_per_page
    non-trivial blocks as raw posting records.
    """
    sections = [s.strip() for s in markdown.split("\n\n") if len(s.strip()) > 80]
    postings = []
    for section in sections[:max_per_page]:
        postings.append(
            {
                "source": "crawl4ai",
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "raw_text": section,
            }
        )
    return postings


async def scrape_targets(targets: list[str]) -> list[dict]:
    all_records: list[dict] = []

    async with AsyncWebCrawler() as crawler:
        for url in targets:
            log.info("scraping_url", url=url)
            try:
                result = await crawler.arun(url=url)
                if not result.success:
                    log.warning("scrape_failed", url=url, reason=result.error_message)
                    continue

                postings = _extract_postings(url, result.markdown or "")
                all_records.extend(postings)
                log.info("raw_scrape_result", url=url, record_count=len(postings))

            except Exception as exc:
                log.warning("scrape_error", url=url, error=str(exc))

    return all_records


def run() -> None:
    targets = _get_targets()
    log.info("scraper_starting", target_count=len(targets))

    records = asyncio.run(scrape_targets(targets))

    if not records:
        log.warning("no_records_scraped")
        print("WARNING: No records were scraped. Check SCRAPING_TARGETS and network access.")
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    log.info(
        "scrape_complete",
        total_records=len(records),
        output_path=str(OUTPUT_PATH),
    )
    print(f"Scraped {len(records)} records → {OUTPUT_PATH}")


if __name__ == "__main__":
    run()
