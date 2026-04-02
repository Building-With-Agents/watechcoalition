# Week 6 findings: SOC, NAICS, and employer enrichment

## What we built

### SOC (occupation)

- **Tier 1 — fuzzy SOC candidate lookup:** Query `dbo.socc` (2018 / 2010 rows) using up to **five** title tokens (plus optional description tokens), with **tech-aware** OR conditions for IT-style titles (cloud, software, devops, etc.) so candidates include computer/software occupations—not only rows that match a generic token like “engineer.”
- **Tier 2 — LLM selection:** The model chooses the best-matching code from that candidate set only, using Azure OpenAI via `agents.common.llm_client` (aligned with `LLM_PROVIDER=azure_openai` and existing Azure env vars). Resolver output is mapped back to the **exact catalog code** via digit-normalized matching (`_canonical_catalog_code()`).
- **DB write-back:** We save the SOC to **`normalized_jobs.occupation_code`** (matching `external_id` + `source`). When enrichment promotes to **`job_postings`**, we also set **`job_postings.occupation_code`**, plus industry and employer links when we have them (`naics_code`, `employer_profile_id`).

### NAICS (industry)

- **Data:** Industry codes live in **`dbo.naics`** (NAICS 2022 titles and codes).
- **Flow (similar idea to SOC):** Pull a short list of likely industries from the DB using words from the title (and description if needed), then ask the model to pick **one code from that list only** (`naics_classifier.py`). If nothing fits or the model’s answer isn’t on the list, we store **`unknown`**—we don’t invent codes.
- **Where it lands:** Enrichment fills **`naics_code`** on the payload; promotion copies it to **`job_postings.naics_code`**. For **`JobProfile`**-style code paths, **`classification.py`** can set **`JobProfile.naics_code`** via **`enrich_job_profile_naics()`**.

### EmployerProfile (company-level fields)

- **Fields:** Company size, AI maturity signal, sector, and whether we recognize the company in **`dbo.companies`** (`is_known_employer`). Missing or weak signals become **`unknown`** where appropriate (`job_profile.py`).
- **Model:** We ask the LLM once, from company name + job description, for size / AI maturity / sector from a fixed list of sectors (`employer_classifier.py`). If the LLM fails, we still set **`is_known_employer`** from a simple exact name match in **`dbo.companies`**—no fuzzy matching.
- **Where it lands:** If we have a **`company_id`**, we insert or update one row per company in **`employer_profiles`**. If we don’t, we store the same info as JSON on **`normalized_jobs.employer_metadata`**.
- **Promotion:** When we promote to **`job_postings`**, we link **`employer_profile_id`**. If the run has no employer payload, we **keep** any **`employer_profile_id`** already on the row instead of wiping it.

**Code map:** SOC demo: `run_soc_demo.py`. Enrichment pipeline: `agent.py`, `classification.py`, `soc_classifier.py`, `naics_classifier.py`, `employer_classifier.py`.

## How SOC works

The SOC pipeline is intentionally **two-step**:

1. **Candidate generation (deterministic):** Matching against `dbo.socc` returns a bounded, ranked set of candidates. For tech-profile titles, generic needles such as “engineer” are de-emphasized and catalog substrings such as “computer,” “software,” and “developer” are OR’d in so the pool stays relevant. Results are deduped by code and ranked (e.g. favoring 151xxx-style computer occupations when appropriate).
2. **Disambiguation (LLM):** The LLM receives the job title, description, and the candidate list. It must pick **only** from those codes. Any output that is not an allowed candidate is resolved using normalization (hyphens / digits) and `_canonical_catalog_code()`; otherwise we fall back to `unclassified`, so the system does not trust free-form SOC strings from the model.

Together, this yields a cheap, explainable first stage and a second stage that handles ambiguity without inventing occupation codes.

## How NAICS works

1. Build a small list of possible industries from the job text and **`dbo.naics`** (up to about 25 rows).
2. Ask the model to return one code from that list (or **`unknown`**). Calls are logged like other extractors (`enrichment-naics-classifier`).
3. If the list is empty, the DB errors, the model fails, or the answer is unclear, we use **`unknown`**. We only keep codes that exist in our NAICS table.

## How EmployerProfile works

1. **`is_known_employer`:** Yes/no from an exact match on the company name in **`dbo.companies`** (normalized), not from the LLM guessing.
2. **LLM:** One pass for size, AI maturity, and sector; sector names are mapped onto our standard list (e.g. “tech” → technology).
3. **Storage:** With **`company_id`** → **`employer_profiles`**. Without it → JSON on **`normalized_jobs`** only.
4. **Events:** Payloads include **`employer_metadata`**. Batch summaries can count how many rows got a NAICS code (`naics_classified_count`) as well as SOC.

## Validation

- **Environment:** Exercised against the **dev** database (`PYTHON_DATABASE_URL`).
- **Example job:** Title **“Engineering Intern @ EverestX LLC”** was classified as **17-3029** — *Engineering Technologists and Technicians, Except Drafters* (SOC 2018).
- **Tech title:** **“Cloud Engineer”** correctly resolves to **151133** — *Software Developers, Systems Software* (after candidate retrieval and catalog mapping fixes below).
- **Write-back:** Checked **`normalized_jobs.occupation_code`** and, when a matching **`job_postings`** row exists, **`job_postings.occupation_code`**, **`naics_code`**, and **`employer_profile_id`** (when we have company + employer data), via **`apply_enrichment_to_job_postings()`**.

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

## Promotion: `job_postings` columns

- SOC used to be saved only on **`normalized_jobs`**. Promotion **`UPDATE`**s now also set **`job_postings.occupation_code`** so the live posting row matches SOC and NAICS together.
- **`employer_profile_id`:** All three promotion updates use **“set new id if we have one, else keep the old one”** so we don’t clear an existing employer link when this run has no employer payload.
- **`job_postings_promotion.py`** maps payload **`soc_code`** → **`occupation_code`**, copies **`naics_code`**, and looks up or creates **`employer_profiles`** from **`company_id`** + **`employer_metadata`** when present.
- **`EnrichmentAgent`** (single job and batch) calls **`apply_enrichment_to_job_postings()`** with **`soc_code`**, **`naics_code`**, and **`employer_metadata`** when those steps succeed.

## Migrations

- **`naics_code`** on dev Postgres (**pg-jobintel-cfa-dev**) was verified.
- Migrations add or ensure: **`naics`** reference table, **`job_postings`** columns **`naics_code`** and **`employer_profile_id`**, **`normalized_jobs`** columns **`naics_code`** and **`employer_metadata`**, and **`employer_profiles`**. On Postgres, an old **`employer_profiles`** table with a serial id may be dropped first so we can recreate with UUID keys.
- Apply with **`python agents/scripts/db_check.py migrate`** (team runbook).

## Design decisions

**Why the model only picks from DB lists (SOC and NAICS)**

Models often output plausible-looking codes that aren’t valid. Letting them choose only from rows we already have in **`socc`** / **`naics`** keeps data trustworthy. If we can’t map the answer back, we use **`unclassified`** (SOC) or **`unknown`** (NAICS).

**Why match on both `external_id` and `source`**

The same **`external_id`** can appear under different sources. Matching both fields updates exactly one normalized job.

**Why one employer row per `company_id`**

One profile per company avoids duplicates and makes repeat runs safe. Jobs without **`company_id`** still keep employer JSON on **`normalized_jobs`** until we can link them.

## What’s next

- Manually review NAICS and employer results on real jobs; adjust prompts or sector list if the same mistakes show up often.
- Keep **`naics`** / **`socc`** seed data and Azure deployment env vars aligned across dev and prod.
- Show NAICS and employer fields anywhere the product still only shows role or SOC.
- If we add a separate “enriched profile” type for APIs, keep it in sync with **`JobProfile`** (`soc_code`, `naics_code`, `employer`) and events.
