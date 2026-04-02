# Week 6 Enrichment Findings: SOC, NAICS, and EmployerProfile

### What we Tested
* **SOC Classification:** Verified the two-tier "Candidate Generation + LLM Disambiguation" flow using `dbo.socc` as the primary grounding.
* **NAICS Mapping:** Tested industry classification against 2022 NAICS reference data, ensuring the LLM selects from a bounded list of ~25 database-backed candidates.
* **EmployerProfile:** Exercised the extraction of `company_size`, `ai_maturity_signal`, and `sector`, alongside an exact-match check for `is_known_employer` in `dbo.companies`.
* **Database Promotion:** Validated that enriched data (SOC, NAICS, and Employer ID) successfully promotes from `normalized_jobs` to the live `job_postings` table.

### What I Found
* **Tech-Awareness:** Standard fuzzy matching often missed IT roles; adding tech-aware fragments (e.g., "Cloud", "SRE") correctly steered the model toward 151xxx-series computer occupations.
* **Data Integrity:** Using `_canonical_catalog_code()` fixed issues where the LLM returned hyphenated codes that didn't match the digit-only database keys.
* **Persistence:** One-to-one mapping for `employer_profiles` using `company_id` prevented duplicate profile rows while maintaining metadata JSON for unlinked jobs.
* **Accuracy:** Defaulting to `unknown` for ambiguous signals successfully prevented the LLM from hallucinating nonexistent industry codes or company sizes.

### Recommendation
* **Standardize Classification:** Adopt the "two-step" candidate lookup (Deterministic + LLM) as the project-wide pattern for all taxonomy-based mapping to keep data trustworthy.
* **Unified Promotion:** Continue using the `apply_enrichment_to_job_postings()` method to ensure SOC and NAICS are updated together on the live table.
* **Environment Sync:** Ensure the `db_check.py migrate` script is run across all dev environments to support the new JSONB and UUID columns.

### Tradeoffs Acknowledged
* **Accuracy vs. Coverage:** We chose to store `unknown` rather than letting the LLM "guess" a code, which may lead to lower initial coverage but ensures higher data quality.
* **Latency:** The two-step SOC process adds a database lookup before the LLM call, slightly increasing processing time per record to gain significant accuracy improvements.
* **Exact Matching:** `is_known_employer` currently relies on exact name normalization; while this misses some variations, it avoids the risk of incorrect fuzzy-match company links.

### Data / Evidence
* **Case Study 1:** "Cloud Engineer" previously matched generic engineering; now correctly resolves to **151133** (Software Developers, Systems Software).
* **Case Study 2:** "Engineering Intern @ EverestX LLC" successfully mapped to **17-3029** (Engineering Technologists) via the 2018 SOC catalog.
* **Log Audits:** Verified that all classification calls are successfully appearing in `llm_audit_log` with correct token counts for cost tracking.