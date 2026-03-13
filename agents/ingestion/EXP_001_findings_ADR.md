# EXP_001_findings_ADR

## What I Tested

For this experiment we evaluated two different job ingestion approaches
for the El Paso / Borderplex region:

1. JSearch API adapter\
2. Crawl4AI scraper adapter

The JSearch adapter was implemented using **httpx** and integrated with
the ingestion agent. It retrieves job postings from the JSearch API
using the `RegionConfig` parameters for the El Paso / Las Cruces region.

The Crawl4AI adapter was implemented to scrape the City of El Paso
GovernmentJobs portal:

[https://www.governmentjobs.com/careers/elpaso](https://www.governmentjobs.com/careers/elpaso)

The adapter extracts job links from the page and converts them into
`RawJobRecord` objects so that both sources produce the same
standardized output format.

Both adapters were run using the same region configuration:

- Region: El Paso / Las Cruces Borderplex\
- Radius: 75 miles\
- States: Texas and New Mexico

Results were saved locally:

- `crawl4ai_elpaso_output.json`
- `ingestion_agent_output.json` (JSearch results)

Evaluation focused on:

- total number of jobs returned\
- employer coverage\
- field completeness\
- duplicate risk across sources\
- scraper stability on JavaScript-rendered pages

Additional Crawl4AI tests implemented:

- successful extraction\
- no jobs scenario\
- parser failure handling\
- health check validation

The Crawl4AI adapter returned **10 job records** and normalized them
into the `RawJobRecord` schema.

---

## Evidence

Example Crawl4AI output titles:

- Animal Services Director\
- Assistant City Attorney I\
- Biostatistician\
- Building Inspector

Source:

City of El Paso GovernmentJobs portal

Fields extracted reliably:

- external_id\
- title\
- company\
- job_url

Fields missing or weak:

- description\
- salary\
- date_posted

This reflects the limitations of extracting structured data from HTML
pages compared to structured APIs.

---

## JSearch Evidence

The JSearch adapter produced structured output including:

- job title\
- employer\
- description\
- date_posted\
- location\
- apply links

Example record:

Rehabilitation Engineer / Data Scientist / Health AI-Focused Engineer  
University of Texas at El Paso

JSearch returns structured data directly from its API, making it
significantly easier to normalize and ingest into the system.

---

## Key Differences

  Category            Crawl4AI                  JSearch

---

  Data Source         Scraping portals          Aggregated job API
  Coverage            Single site per scraper   Multiple job sites
  Structure           Inconsistent              Structured
  Reliability         Parser dependent          API stable
  Data completeness   Low                       High

---

## What I Found

The Crawl4AI scraper successfully extracted jobs from the El Paso
GovernmentJobs portal.

However, the page uses **JavaScript to populate job listings after the
initial page load**, which initially caused the scraper to capture a
loading state showing "0 jobs found."

To address this, the Crawl4AI configuration was updated to include a
delay before capturing the HTML so the JavaScript rendering could
complete.

After configuration, the scraper returned **10 job records**.

The JSearch adapter returned **25 job records** for the same region.

Unlike Crawl4AI, JSearch aggregates job postings from multiple sources
across the region, including universities, healthcare employers, and
private companies.

This means:

- Crawl4AI provided **deep extraction from a single portal**
- JSearch provided **broader coverage across many employers**

The scraped records contained reliable job IDs and URLs but fewer
structured fields compared to JSearch.

JSearch results included richer metadata such as:

- location fields
- employment type
- posting dates

---

## Tradeoffs

### Crawl4AI Advantages

- Works on sites not covered by APIs\
- Can scrape JavaScript-rendered pages\
- Useful as a fallback source

### Crawl4AI Weaknesses

- Parser fragility\
- Limited structured fields\
- Requires custom adapters per site

### JSearch Advantages

- Structured REST API\
- Aggregated job sources\
- Richer metadata\
- Easier normalization

### JSearch Weaknesses

- Dependent on external API\
- May miss niche portals

---

## Recommendation

Use **JSearch as the primary job ingestion source**.

Use **Crawl4AI as a secondary scraper** for portals not covered by
JSearch.

Rationale:

- JSearch provides structured data
- higher field completeness
- stable API responses
- broader coverage across employers

Crawl4AI remains valuable for scraping specific portals where API
coverage is insufficient.

---

## Data / Evidence

Experiment results for the El Paso / Borderplex region:

  Source     Records Returned   Coverage

---

  Crawl4AI   10                 City of El Paso GovernmentJobs portal
  JSearch    25                 Multiple employers across the region

Evidence files generated during testing:

- `crawl4ai_elpaso_output.json`
- `ingestion_agent_output.json`

Crawl4AI required additional configuration to handle JavaScript-rendered
job listings, demonstrating that scraper-based ingestion can be
sensitive to page behavior and timing.

JSearch provided stable structured responses through a REST API.

---

## Detecting Silent Scraper Failures

Scrapers can fail silently if a website changes its HTML structure or
page behavior.

Several safeguards were implemented:

1. **Health checks** verify the target site is reachable and that
  expected job-link patterns exist in the HTML.
2. **Parser validation** ensures the page contains expected job link
  patterns. If a large HTML page is returned but no job links are
    detected, the adapter raises a parser error instead of returning
    empty results.
3. **Job count monitoring** flags anomalies when a source that normally
  returns jobs suddenly returns zero.

These checks ensure failures are visible instead of silently producing
incorrect data.

---

## What This Means for Downstream Work

### EXP-001 → EXP-003 Deduplication Requirements

The quality and structure of ingestion sources directly affect
downstream deduplication complexity.

JSearch aggregates job postings from multiple job boards and employer
sites. While this increases coverage, it also increases the likelihood
that the **same job appears multiple times across different sources**.

Normalization and deduplication stages must therefore rely on signals
such as:

- employer name
- job title
- location
- job URL
- posting metadata

Scraped sources like Crawl4AI usually produce fewer duplicates because
they pull from a single site, but they provide narrower coverage.

This experiment demonstrates a common tradeoff in job aggregation
systems:

**Higher source coverage increases deduplication complexity.**