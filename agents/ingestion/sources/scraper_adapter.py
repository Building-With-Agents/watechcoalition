"""
Scraper adapter: crawl URLs from SCRAPING_TARGETS via Crawl4AI, emit staging records, write JSON.
Splits page markdown into job postings by [Apply](url) boundaries.
"""
import asyncio
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import structlog
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

# Load .env from agents/ (three levels up from sources/)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

logger = structlog.get_logger()

SOURCE_NAME = "crawl4ai"
OUTPUT_FILENAME = "raw_scrape_sample.json"
MIN_CHUNK_LENGTH = 50

# Each job posting ends with [Apply](url); split on that boundary.
APPLY_LINK_PATTERN = re.compile(r"\[Apply\]\([^)]+\)")


def _split_markdown_into_postings(markdown: str) -> list[str]:
    """Split markdown into chunks ending with [Apply](url); drop chunks shorter than MIN_CHUNK_LENGTH."""
    if not markdown or not markdown.strip():
        return []
    chunks: list[str] = []
    last_end = 0
    for m in APPLY_LINK_PATTERN.finditer(markdown):
        chunk = markdown[last_end : m.end()].strip()
        if len(chunk) >= MIN_CHUNK_LENGTH:
            chunks.append(chunk)
        last_end = m.end()
    return chunks


def _staging_dir() -> Path:
    agents_root = Path(__file__).resolve().parent.parent.parent
    return agents_root / "data" / "staging"


def _record_from_result(
    url: str,
    raw_text: str,
    run_id: str,
    timestamp: str,
) -> dict:
    payload = f"{url}{raw_text}"
    raw_payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return {
        "source": SOURCE_NAME,
        "source_url": url,
        "ingestion_run_id": run_id,
        "ingestion_timestamp": timestamp,
        "raw_payload_hash": raw_payload_hash,
        "raw_text": raw_text,
    }


async def main() -> None:
    targets_raw = os.environ.get("SCRAPING_TARGETS", "")
    urls = [u.strip() for u in targets_raw.split(",") if u.strip()]
    try:
        batch_size = int(os.environ.get("BATCH_SIZE", "100"))
    except ValueError:
        batch_size = 100
    urls = urls[:batch_size]

    if not urls:
        logger.warning("scraper_no_targets", reason="SCRAPING_TARGETS empty or missing")
        return

    run_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    records: list[dict] = []
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        for url in urls:
            try:
                result = await crawler.arun(url, config=run_config)
                raw_text = ""
                if result.success and result.markdown is not None:
                    raw_text = str(result.markdown)
                chunks = _split_markdown_into_postings(raw_text)
                for chunk in chunks:
                    record = _record_from_result(url, chunk, run_id, timestamp)
                    records.append(record)
                logger.info("raw_scrape_result", url=url, record_count=len(chunks))
            except Exception as e:
                logger.warning("raw_scrape_result", url=url, record_count=0, error=str(e))

    staging_dir = _staging_dir()
    staging_dir.mkdir(parents=True, exist_ok=True)
    out_path = staging_dir / OUTPUT_FILENAME
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("scraper_output_saved", path=str(out_path), total_records=len(records))


if __name__ == "__main__":
    asyncio.run(main())
