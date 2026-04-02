# Week 6 findings: SOC classification

## What we built

- **Tier 1 — fuzzy SOC candidate lookup:** Query `dbo.socc` (2018 / 2010 rows) using up to **five** title tokens (plus optional description tokens), with **tech-aware** OR conditions for IT-style titles (cloud, software, devops, etc.) so candidates include computer/software occupations—not only rows that match a generic token like “engineer.”
- **Tier 2 — LLM selection:** The model chooses the best-matching code from that candidate set only, using Azure OpenAI via `agents.common.llm_client` (aligned with `LLM_PROVIDER=azure_openai` and existing Azure env vars). Resolver output is mapped back to the **exact catalog code** via digit-normalized matching (`_canonical_catalog_code()`).
- **DB write-back:** After classification, we persist the chosen code to `dbo.normalized_jobs.occupation_code` on the row that matches both `external_id` and `source`, and—via `agents.enrichment.job_postings_promotion`—to **`dbo.job_postings.occupation_code`** when enrichment promotion runs (together with `naics_code`).

Supporting surfaces include `run_soc_demo.py` for end-to-end smoke checks against the database, and enrichment helpers in `agents/enrichment/classification.py` / `agents/enrichment/classifiers/soc_classifier.py`.

## How it works

The pipeline is intentionally **two-step**:

1. **Candidate generation (deterministic):** Matching against `dbo.socc` returns a bounded, ranked set of candidates. For tech-profile titles, generic needles such as “engineer” are de-emphasized and catalog substrings such as “computer,” “software,” and “developer” are OR’d in so the pool stays relevant. Results are deduped by code and ranked (e.g. favoring 151xxx-style computer occupations when appropriate).
2. **Disambiguation (LLM):** The LLM receives the job title, description, and the candidate list. It must pick **only** from those codes. Any output that is not an allowed candidate is resolved using normalization (hyphens / digits) and `_canonical_catalog_code()`; otherwise we fall back to `unclassified`, so the system does not trust free-form SOC strings from the model.

Together, this yields a cheap, explainable first stage and a second stage that handles ambiguity without inventing occupation codes.

## Validation

- **Environment:** Exercised against the **dev** database (`PYTHON_DATABASE_URL`).
- **Example job:** Title **“Engineering Intern @ EverestX LLC”** was classified as **17-3029** — *Engineering Technologists and Technicians, Except Drafters* (SOC 2018).
- **Tech title:** **“Cloud Engineer”** correctly resolves to **151133** — *Software Developers, Systems Software* (after candidate retrieval and catalog mapping fixes below).
- **Write-back:** Confirmed updates to `normalized_jobs.occupation_code` and, where a resolvable `job_postings` row exists, to `job_postings.occupation_code` and `job_postings.naics_code` via `apply_enrichment_to_job_postings()`.

## SOC classification fixes

**Root cause**

- Candidate matching was **too narrow** (originally only the first word of the title, no tech-aware search), so many IT titles surfaced irrelevant “engineer” rows (e.g. aerospace/civil) instead of computer/software SOCs.
- The **LLM pick** did not always **map back to catalog codes** correctly because of hyphen vs. digit-only code shapes and strict `in candidate_codes` checks after resolution.
- An **async / ordering issue** in `run_soc_demo.py` meant the demo could **print before** `classify_soc()` finished (and Tier 1 used slightly inconsistent title/description args vs. enrichment). Structured logs could appear after stdout, and a second LLM path could confuse debugging.

**Fix**

- Broadened needles to **up to five tokens** (with description support when needed).
- Added **tech-aware fragment search** for IT-style titles (cloud, software, devops, backend/frontend/fullstack, platform, ML/AI, SRE, etc.) plus OR matches on IT-oriented `dbo.socc.title` substrings; rank/dedupe candidates toward 151xxx computer occupations when appropriate.
- Introduced **`_canonical_catalog_code()`** for **digit-normalized** matching so the returned SOC always matches a row in the candidate set.
- Fixed **`run_soc_demo.py`** to use a single `desc_for_soc`, **`await classify_soc()`** once, print **`soc_result`**, and pass **`soc_code_override`** into **`enrich_job_profile_soc()`** to avoid duplicate LLM calls; added **`sys.stdout.flush()`** where helpful for log ordering.

**Result**

- **“Cloud Engineer”** resolves to **151133** (*Software Developers, Systems Software*), with Tier 1 candidates and final printed `soc_code` aligned with logs (`soc_classifier_llm_resolution`).

## NAICS + SOC wired into `job_postings`

- **`occupation_code`** on **`job_postings`** was missing from promotion **`UPDATE`**s (SOC was persisted on **`normalized_jobs`** only). **`naics_code`** was already included in **`job_postings_promotion.py`**; **`occupation_code`** needed the same treatment so SOC and NAICS stay aligned on the promoted row.
- **`agents/enrichment/job_postings_promotion.py`** was updated so all three promotion **`UPDATE`** statements set **`occupation_code = :occupation_code`**, sourced from the enrichment payload’s **`soc_code`**, alongside **`naics_code`**.
- Both the **`EnrichmentAgent.process()`** single-record path and the **batch** path (after **`enrich_record()`**) call **`apply_enrichment_to_job_postings()`** with payloads that include **`soc_code`** and **`naics_code`** when classification succeeds.

## Migrations

- **`naics_code`** column presence was **confirmed** on the cloud Postgres instance (**pg-jobintel-cfa-dev**).
- Schema updates were applied using: **`python agents/scripts/db_check.py migrate`** (per team runbook).

## Design decisions

**Why constrain the LLM to candidates instead of free generation**

SOC codes are structured and easy for models to “sound right” while being wrong or nonexistent. Restricting the LLM to a closed set derived from `dbo.socc` ensures every emitted code exists in our reference data and keeps auditing and downstream joins trustworthy. Parsing logic normalizes noisy replies (punctuation, hyphen vs. numeric forms) and maps through **`_canonical_catalog_code()`** so the stored value matches the catalog row; otherwise we fall back to `unclassified`.

**Why match on both `external_id` and `source`**

`external_id` is only unique in combination with `source` (see index `ix_normalized_jobs_source_eid`). Updating on `external_id` alone could touch multiple rows if the same external identifier appears under different ingestion sources. Requiring both fields targets exactly one normalized job row for write-back.

## What’s next

- **NAICS classification** — extend product coverage, quality review, and any remaining consumers beyond the current enrichment + `job_postings` path.
- **`EmployerProfile` population** — fill employer-level fields on `JobProfile` (size, maturity signal, sector, etc.) from enrichment rules and resolvers.
- **Wiring into `EnrichedJobProfile`** — integrate SOC, NAICS, and employer outputs into the canonical enriched profile type and any API paths that consume it.
