# Week 6 findings: SOC classification

## What we built

- **Tier 1 — fuzzy SOC candidate lookup:** Query `dbo.socc` (2018 SOC) using the first word of the job title (case-insensitive substring match on title) to produce a short list of plausible occupation codes.
- **Tier 2 — LLM selection:** The model chooses the best-matching code from that candidate set only, using Azure OpenAI via `agents.common.llm_client` (aligned with `LLM_PROVIDER=azure_openai` and existing Azure env vars).
- **DB write-back:** After classification, we persist the chosen code to `dbo.normalized_jobs.occupation_code` on the row that matches both `external_id` and `source`.

Supporting surfaces include `run_soc_demo.py` for end-to-end smoke checks against the database, and enrichment helpers in `agents/enrichment/classification.py` / `agents/enrichment/classifiers/soc_classifier.py`.

## How it works

The pipeline is intentionally **two-step**:

1. **Candidate generation (deterministic):** Fuzzy title matching against `dbo.socc` returns a bounded set of candidates (e.g. top matches within a limit). This grounds every downstream choice in real catalog rows.
2. **Disambiguation (LLM):** The LLM receives the job title, description, and the numbered candidate list. It must pick **only** from those codes. Any output that is not an allowed candidate is resolved to a safe fallback (e.g. `unclassified`), so the system does not trust free-form SOC strings from the model.

Together, this yields a cheap, explainable first stage and a second stage that handles ambiguity without inventing occupation codes.

## Validation

- **Environment:** Exercised against the **dev** database (`PYTHON_DATABASE_URL`).
- **Example job:** Title **“Engineering Intern @ EverestX LLC”** was classified as **17-3029** — *Engineering Technologists and Technicians, Except Drafters* (SOC 2018).
- **Write-back:** Confirmed that `normalized_jobs.occupation_code` was updated for the corresponding normalized job row after enrichment.

## Design decisions

**Why constrain the LLM to candidates instead of free generation**

SOC codes are structured and easy for models to “sound right” while being wrong or nonexistent. Restricting the LLM to a closed set derived from `dbo.socc` ensures every emitted code exists in our reference data and keeps auditing and downstream joins trustworthy. Parsing logic can still normalize noisy replies (e.g. extra punctuation) as long as the final value remains in the candidate set or falls back to `unclassified`.

**Why match on both `external_id` and `source`**

`external_id` is only unique in combination with `source` (see index `ix_normalized_jobs_source_eid`). Updating on `external_id` alone could touch multiple rows if the same external identifier appears under different ingestion sources. Requiring both fields targets exactly one normalized job row for write-back.

## What’s next

- **NAICS classification** — parallel industry-code enrichment where product requirements define scope.
- **`EmployerProfile` population** — fill employer-level fields on `JobProfile` (size, maturity signal, sector, etc.) from enrichment rules and resolvers.
- **Wiring into `EnrichedJobProfile`** — integrate SOC (and future NAICS / employer) outputs into the canonical enriched profile type and any promotion or API paths that consume it.
