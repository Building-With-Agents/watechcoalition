"""
Crawl4AI scraping adapter for the Ingestion Agent.

Scrapes 5–10 job postings from a target URL (from SCRAPING_TARGETS env).
Saves raw output to agents/data/staging/raw_scrape_sample.json.
No PII in logs; no hardcoded credentials or URLs.
"""

import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import structlog

# Load .env from repo root when this module is run as __main__
if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[3]
    env_path = repo_root / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

log = structlog.get_logger()

MIN_RECORDS = 5
MAX_RECORDS = 10

# Heuristic patterns that usually indicate a job detail page.
# You can add/remove patterns depending on the target site.
JOB_URL_HINTS = (
    "/job/",
    "/jobs/",
    "jobid=",
    "jobId=",
    "gh_jid=",
    "lever.co/",
    "boards.greenhouse.io/",
)


def _stable_id(url: str, title: str = "", company: str = "") -> str:
    raw = f"{url}|{title or ''}|{company or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _extract_raw_text(result) -> str:
    text = ""
    if result.markdown is not None:
        if hasattr(result.markdown, "raw_markdown"):
            text = result.markdown.raw_markdown or ""
        elif isinstance(result.markdown, str):
            text = result.markdown
    if not text:
        text = result.cleaned_html or result.html or ""
    return text[:50_000]


def _ensure_staging_dir() -> Path:
    agents_root = Path(__file__).resolve().parents[2]
    staging = agents_root / "data" / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    return staging


def _get_page_title(result) -> str:
    if result.metadata and isinstance(result.metadata, dict):
        t = result.metadata.get("title")
        if t and isinstance(t, str):
            return t.strip()
    return ""


def _looks_like_job_url(url: str) -> bool:
    u = (url or "").lower()
    return any(hint in u for hint in JOB_URL_HINTS)


def _is_garbage_text(raw_text: str) -> bool:
    t = (raw_text or "").strip()
    if not t:
        return True
    # Skip pages that are clearly not a posting
    if t.lower() == "loading...":
        return True
    # Too short to be a job description
    if len(t) < 300:
        return True
    return False


async def _crawl_and_collect(target_url: str) -> list[dict]:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

    records: list[dict] = []
    listing_scraped_at = datetime.now(timezone.utc).isoformat()

    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, word_count_threshold=10)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # Crawl the listing page first
        result = await crawler.arun(url=target_url, config=run_cfg)
        if not result.success:
            log.warning("crawl_target_failed", url=target_url, error=result.error_message)
            return records

        # Collect candidate links
        links_dict = result.links or {}
        candidates: list[str] = []

        for key in ("internal", "external"):
            for item in links_dict.get(key, []):
                if not isinstance(item, dict):
                    continue
                h = item.get("href") or item.get("url")
                if not h or not isinstance(h, str) or not h.startswith("http"):
                    continue
                if _looks_like_job_url(h):
                    candidates.append(h)

        # Deduplicate
        seen: set[str] = set()
        unique_candidates: list[str] = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                unique_candidates.append(c)

        # If we didn't find any job-looking links, fall back to crawling a few internal links
        if not unique_candidates:
            for item in links_dict.get("internal", []):
                if not isinstance(item, dict):
                    continue
                h = item.get("href") or item.get("url")
                if h and isinstance(h, str) and h.startswith("http"):
                    if h not in seen:
                        seen.add(h)
                        unique_candidates.append(h)

        # Crawl candidates until we actually collect 5–10 usable job postings
        # (not just "10 pages")
        for url in unique_candidates:
            if len(records) >= MAX_RECORDS:
                break

            page_result = await crawler.arun(url=url, config=run_cfg)
            if not page_result.success:
                continue

            raw_text = _extract_raw_text(page_result)
            if _is_garbage_text(raw_text):
                continue

            title = _get_page_title(page_result)
            company = ""

            records.append(
                {
                    "external_id": _stable_id(page_result.url, title, company),
                    "source": "crawl4ai",
                    "url": page_result.url,
                    "scraped_at": listing_scraped_at,
                    "raw_text": raw_text,
                    "title": title or None,
                    "company": company or None,
                }
            )

            # If we already have enough, stop early
            if len(records) >= MIN_RECORDS and len(records) >= MAX_RECORDS:
                break

    return records


def run_scrape() -> int:
    targets_raw = os.getenv("SCRAPING_TARGETS", "").strip()
    if not targets_raw:
        log.error("scrape_skipped", reason="SCRAPING_TARGETS not set")
        return 1

    target_url = targets_raw.split(",")[0].strip()
    if not target_url:
        log.error("scrape_skipped", reason="first URL in SCRAPING_TARGETS is empty")
        return 1

    records = asyncio.run(_crawl_and_collect(target_url))

    if len(records) < MIN_RECORDS:
        log.warning("scrape_incomplete", url=target_url, record_count=len(records))

    payload = {
        "source": "crawl4ai",
        "scrape_run_id": str(uuid4()),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "target_url": target_url,
        "records": records,
    }

    out_path = _ensure_staging_dir() / "raw_scrape_sample.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    log.info("raw_scrape_result", url=target_url, record_count=len(records))
    return 0


def main() -> None:
    sys.exit(run_scrape())


if __name__ == "__main__":
    main()