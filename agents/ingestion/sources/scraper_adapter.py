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
from datetime import datetime, timezone
from pathlib import Path

import structlog

# Paths: repo root for .env; agents root for data (so path is correct when run as -m agents....)
_THIS_FILE = Path(__file__).resolve()
_AGENTS_ROOT = _THIS_FILE.parents[2]   # agents/
_REPO_ROOT = _THIS_FILE.parents[3]     # repo root
_ENV_PATH = _REPO_ROOT / ".env"
if _ENV_PATH.exists():
    from dotenv import load_dotenv
    load_dotenv(_ENV_PATH)

log = structlog.get_logger()

SOURCE_ID = "crawl4ai"
STAGING_DIR = _AGENTS_ROOT / "data" / "staging"
OUTPUT_FILE = STAGING_DIR / "raw_scrape_sample.json"
OUTPUT_FILE_PRETTY = STAGING_DIR / "raw_scrape_sample2.json"
OUTPUT_FILE_PRETTY_V3 = STAGING_DIR / "raw_scrape_sample3.json"
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
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "raw_text": raw_text,
                })
            except Exception as e:
                log.warning("scrape_error", url=url, error=str(e))
                continue

    return records


def _format_scraped_at(iso_timestamp: str) -> str:
    """Return human-readable timestamp in UTC, matching dashboard (e.g. Feb 27, 2026 at 3:45 PM UTC)."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y at %I:%M %p UTC").replace(" 0", " ")
    except (ValueError, TypeError):
        return iso_timestamp


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple blank lines to two newlines, strip each line. Improves readability without losing content."""
    if not text:
        return text
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines)


def _prettify_record(record: dict) -> dict:
    """Build a readable record: full raw_text, length, and normalized preview. No truncation."""
    raw = record["raw_text"]
    out = {
        "source": record["source"],
        "url": record["url"],
        "timestamp": record["timestamp"],
        "raw_text_full_length": len(raw),
        "raw_text": _normalize_whitespace(raw),
        "raw_text_truncated": False,
    }
    lines = [s for s in raw.splitlines() if s.strip()]
    out["raw_text_preview_lines"] = lines
    return out


def _prettify_record_v3(record: dict) -> dict:
    """Clean metadata + full body with normalized whitespace; output for raw_scrape_sample3.json. No truncation."""
    return {
        "source": record["source"],
        "url": record["url"],
        "scraped_at": _format_scraped_at(record["timestamp"]),
        "raw_text": _normalize_whitespace(record["raw_text"]),
    }


def run() -> None:
    """Scrape configured targets and write raw_scrape_sample.json to agents/data/staging."""
    urls = _get_target_urls()
    if not urls:
        log.warning("no_target_urls", hint="Set SCRAPING_TARGETS in .env (comma-separated URLs)")
        return

    records = asyncio.run(_scrape_urls(urls))
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_FILE.resolve()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    pretty_records = [_prettify_record(r) for r in records]
    output_pretty_path = OUTPUT_FILE_PRETTY.resolve()
    with open(output_pretty_path, "w", encoding="utf-8") as f:
        json.dump(pretty_records, f, indent=2, ensure_ascii=False)

    pretty_v3_records = [_prettify_record_v3(r) for r in records]
    output_pretty_v3_path = OUTPUT_FILE_PRETTY_V3.resolve()
    with open(output_pretty_v3_path, "w", encoding="utf-8") as f:
        json.dump(pretty_v3_records, f, indent=2, ensure_ascii=False)

    log.info(
        "raw_scrape_result",
        url=urls[0] if len(urls) == 1 else f"{len(urls)}_urls",
        record_count=len(records),
        output_file=str(output_path),
        output_pretty_file=str(output_pretty_path),
        output_pretty_v3_file=str(output_pretty_v3_path),
    )


if __name__ == "__main__":
    run()
