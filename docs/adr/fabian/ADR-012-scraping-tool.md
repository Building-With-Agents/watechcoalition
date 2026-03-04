# ADR-012: Scraping Tool

**Status:** Proposed  
**Decision makers:** Engineering / Product  
**Related:** ARCHITECTURAL_DECISIONS.md #12

---

## Context and problem statement

The Ingestion Agent must scrape job postings from target URLs in addition to pulling from the JSearch API. We need a scraping tool that is pip-installable (no separate service for Phase 1), supports JavaScript-rendered pages where needed, and fits the 12-week curriculum and structlog-only logging. Week 1 already delivered a Crawl4AI-based scraper; this ADR formalizes the choice and documents alternatives.

## Considered options

* **Crawl4AI + httpx** — Crawl4AI for web scraping (AsyncWebCrawler, Playwright under the hood); httpx for JSearch API. Pip-installable; used in Week 1.
* **Firecrawl** — API-based scraping service. Less local setup but adds an external dependency and cost.
* **ScrapeGraphAI** — Graph-based scraping with LLM. Heavier and more complex for raw HTML extraction.
* **Browser-use / Spider** — Other browser-automation or lightweight scrapers; varying maturity and fit for batch ingestion.

## Decision outcome

**Chosen option:** Crawl4AI for web scraping and httpx for JSearch API (reference implementation).

**Rationale:** Crawl4AI is pip-installable and was already validated in Week 1: it runs in-process, uses structlog-friendly patterns, and writes to staging without extra infrastructure. JSearch is an HTTP API, so httpx is a natural fit and keeps API vs scrape concerns separate. Firecrawl and similar services introduce a paid dependency and a single point of failure for Phase 1. ScrapeGraphAI and heavy LLM-based scrapers add latency and cost for a task (raw page text) that does not require LLM in the ingestion stage. The evaluation criteria (setup complexity, cost, output completeness, error handling) favor the existing Crawl4AI + httpx setup.

## Consequences

* **Positive:** No new services; Week 1 evidence applies; clear separation between API (httpx) and scrape (Crawl4AI) code.
* **Negative:** Playwright/browser dependency for Crawl4AI; local resource use when scraping many URLs.
* **Neutral:** If the team later needs a managed scraper, an adapter can wrap Firecrawl behind the same interface.

## References

* docs/planning/ARCHITECTURAL_DECISIONS.md — #12 options and evaluation criteria
* agents/ingestion/sources/scraper_adapter.py — existing Crawl4AI usage
* agents/ingestion/sources/ — JSearch adapter (httpx) lives alongside scraper
