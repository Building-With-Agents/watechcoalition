"""
Crawl4AI-based scraper adapter for job ingestion.
Scrapes 5-10 job postings from configured target URL(s) and writes raw JSON to staging.
Uses structlog only; no PII; no hardcoded credentials or URLs.

Requires: SCRAPING_TARGETS in .env (comma-separated URLs; up to 10 used).
Crawl4AI uses Playwright — run `playwright install` once if browsers are missing.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import structlog

from agents.common.datetime_utils import utc_now_iso

# Paths: repo root for .env and for agents package; staging path from common (single source of truth)
_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[3]   # agents/ingestion/sources -> agents -> repo root
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_ENV_PATH = _REPO_ROOT / ".env"
if _ENV_PATH.exists():
    from dotenv import load_dotenv
    load_dotenv(_ENV_PATH)

from agents.common.paths import RAW_SCRAPE_SAMPLE_PATH, STAGING_DIR

log = structlog.get_logger()

SOURCE_ID = "crawl4ai"
MAX_URLS = 10


def _get_target_urls() -> list[str]:
    """Read scraping target URL(s) from environment. No hardcoded URLs."""
    raw = os.getenv("SCRAPING_TARGETS", "").strip()
    if not raw:
        return []
    urls = [u.strip() for u in raw.split(",") if u.strip()]
    return urls[:MAX_URLS]


def _raw_text_from_result(result) -> str:
    """Extract raw text from Crawl4AI result (handles string or MarkdownGenerationResult)."""
    content = getattr(result, "markdown", None)
    if content is None:
        return ""
    if hasattr(content, "raw_markdown"):
        return content.raw_markdown or ""
    if hasattr(content, "fit_markdown") and content.fit_markdown:
        return content.fit_markdown
    if isinstance(content, str):
        return content
    return str(content)


async def _scrape_urls(urls: list[str]) -> list[dict]:
    """Scrape each URL with Crawl4AI and return list of records with source, url, timestamp, raw_text."""
    from crawl4ai import AsyncWebCrawler

    try:
        from crawl4ai import CrawlerRunConfig, CacheMode
        run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    except ImportError:
        run_config = None

    records: list[dict] = []

    async with AsyncWebCrawler() as crawler:
        for url in urls:
            try:
                if run_config is not None:
                    result = await crawler.arun(url=url, config=run_config)
                else:
                    result = await crawler.arun(url)
                success = getattr(result, "success", True)
                if not success:
                    error_msg = getattr(result, "error_message", "unknown")
                    log.warning("scrape_failed", url=url, error=error_msg)
                    continue
                raw_text = _raw_text_from_result(result)
                resolved_url = getattr(result, "url", url) or url
                records.append({
                    "source": SOURCE_ID,
                    "url": resolved_url,
                    "timestamp": utc_now_iso(),
                    "raw_text": raw_text,
                })
            except Exception as e:
                log.warning("scrape_error", url=url, error=str(e))
                continue

    return records


def run() -> None:
    """Scrape configured targets and write raw_scrape_sample.json to agents/data/staging."""
    urls = _get_target_urls()
    if not urls:
        log.warning("no_target_urls", hint="Set SCRAPING_TARGETS in .env (comma-separated URLs)")
        return

    records = asyncio.run(_scrape_urls(urls))
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_SCRAPE_SAMPLE_PATH.resolve()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    log.info(
        "raw_scrape_result",
        url=urls[0] if len(urls) == 1 else f"{len(urls)}_urls",
        record_count=len(records),
        output_file=str(output_path),
    )


if __name__ == "__main__":
    run()
