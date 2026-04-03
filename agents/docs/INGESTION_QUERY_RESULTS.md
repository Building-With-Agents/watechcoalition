# Ingestion Query Keyword Results

Date: 2026-04-03
Source: JSearch API via `batch_ingest.py`
Total raw records staged: **1,065** across 32 query variants and 320 API requests (2 keys).

## Budget Summary


| Key       | Capacity  | Used     | Remaining | Notes                                     |
| --------- | --------- | -------- | --------- | ----------------------------------------- |
| Key 1     | 500       | ~500     | 0         | Exhausted (429) from prior runs + round 2 |
| Key 2     | 500       | ~320     | ~180      | Round 2 (200 req) + Round 3 (120 req)     |
| **Total** | **1,000** | **~820** | **~180**  | Reserve for student/testing               |


## Round 1 Results (6 broad queries, 50 requests)

All results from Key 1. First ingestion run — zero prior records, so no dedup skips.

| Query Name           | Keywords                                                      | Pages | Staged | Dedup Skipped | Yield | Notes                                          |
| -------------------- | ------------------------------------------------------------- | ----- | ------ | ------------- | ----- | ---------------------------------------------- |
| ai-engineering       | AI engineer, machine learning engineer                        | 10    | 78     | 0             | 100%  | Strong AI/ML role coverage                     |
| data-science         | data scientist, data analyst, data engineer                   | 10    | 89     | 0             | 100%  | Broad data roles, high volume                  |
| prompt-llm           | prompt engineer, LLM, generative AI                           | 10    | 48     | 0             | 100%  | Good agentic era signal                        |
| software-engineering | software engineer, backend developer, full stack              | 10    | 95     | 0             | 100%  | Highest volume — broad tech roles              |
| devops-cloud         | DevOps engineer, cloud architect, platform engineer           | 5     | 42     | 0             | 100%  | Cloud infra roles                              |
| cybersecurity        | cybersecurity analyst, security engineer                      | 5     | 30     | 0             | 100%  | Security roles baseline                        |

**Round 1 Total: 382 new records from 50 requests (7.64 records/request, zero dedup)**

## Round 2 Results (20 targeted queries, 200 requests)

Key 1 exhausted on first query; all results from Key 2.

### Core AI/ML Roles


| Query Name       | Keywords                                              | Staged | Dedup Skipped | Yield | Notes                                                     |
| ---------------- | ----------------------------------------------------- | ------ | ------------- | ----- | --------------------------------------------------------- |
| ai-engineering   | AI engineer, machine learning engineer                | 0      | 0             | 0%    | Key 1 429'd; no records                                   |
| data-science     | data scientist, data analyst                          | 24     | 2             | 92%   | Good yield, broad role coverage                           |
| prompt-llm       | prompt engineer, LLM, generative AI                   | 2      | 12            | 14%   | High dedup — overlaps with ai-engineering from prior runs |
| ml-ops           | MLOps engineer, ML infrastructure, model deployment   | 3      | 8             | 27%   | High dedup — niche role, few unique listings              |
| deep-learning    | deep learning engineer, NLP engineer, computer vision | 12     | 4             | 75%   | Good for specialized AI roles                             |
| data-engineering | data engineer, data pipeline, ETL developer           | 28     | 0             | 100%  | Excellent — zero dedup, strong pipeline/tooling signals   |
| ai-research      | AI researcher, applied scientist, research engineer   | 18     | 0             | 100%  | Excellent — no overlap, research-heavy postings           |
| agentic-ai       | AI agent developer, autonomous systems engineer       | 19     | 0             | 100%  | Excellent — unique niche, zero dedup                      |


### Adjacent Tech Roles


| Query Name           | Keywords                                                    | Staged | Dedup Skipped | Yield | Notes                                         |
| -------------------- | ----------------------------------------------------------- | ------ | ------------- | ----- | --------------------------------------------- |
| software-engineering | software engineer, backend developer                        | 43     | 5             | 90%   | Highest volume core tech query                |
| full-stack           | full stack developer, full stack engineer                   | 16     | 3             | 84%   | Good volume                                   |
| python-developer     | Python developer, Python engineer                           | 37     | 0             | 100%  | Strong yield, often includes AI/ML tooling    |
| devops-cloud         | DevOps engineer, cloud architect, platform engineer         | 3      | 16            | 16%   | High dedup — overlaps with prior runs         |
| cloud-data           | cloud data engineer, Azure data engineer, AWS data engineer | 19     | 0             | 100%  | Good — cloud + data combo unique              |
| site-reliability     | site reliability engineer, SRE, infrastructure engineer     | 50     | 0             | 100%  | Max results, zero dedup — very distinct niche |
| cybersecurity        | cybersecurity analyst, security engineer                    | 1      | 17            | 6%    | Nearly all duplicates from prior runs         |


### Emerging/Analytics Roles


| Query Name          | Keywords                                                  | Staged | Dedup Skipped | Yield | Notes                                     |
| ------------------- | --------------------------------------------------------- | ------ | ------------- | ----- | ----------------------------------------- |
| analytics-bi        | business intelligence analyst, analytics engineer         | 28     | 1             | 97%   | Good volume, BI/analytics tooling signals |
| solutions-architect | solutions architect, technical architect, cloud solutions | 15     | 0             | 100%  | Clean yield, architecture-level roles     |
| robotics-automation | robotics engineer, automation engineer                    | 50     | 0             | 100%  | Max results, zero dedup — highly distinct |
| quant-fintech       | quantitative analyst, fintech engineer                    | 2      | 0             | 100%  | Very niche — few results but all unique   |
| product-tech        | technical product manager, AI product manager             | 27     | 2             | 93%   | Good for AI product signals               |


**Round 2 Total: 397 new records from 200 requests (1.99 records/request after dedup)**

## Round 3 Results (12 additional queries, 120 requests)

Key 1 exhausted on first query; all results from Key 2.


| Query Name        | Keywords                                                         | Staged | Dedup Skipped | Yield | Notes                                        |
| ----------------- | ---------------------------------------------------------------- | ------ | ------------- | ----- | -------------------------------------------- |
| react-frontend    | React developer, frontend engineer, TypeScript developer         | 0      | 0             | 0%    | Key 1 429'd; no records                      |
| java-enterprise   | Java developer, Java engineer, Spring Boot developer             | 49     | 1             | 98%   | Very high volume, enterprise tooling         |
| systems-engineer  | systems engineer, Linux engineer, systems administrator          | 50     | 0             | 100%  | Max results, zero dedup                      |
| blockchain-web3   | blockchain developer, Web3 engineer, smart contract developer    | 2      | 0             | 100%  | Very niche — few listings                    |
| data-governance   | data governance analyst, data quality engineer, data steward     | 8      | 0             | 100%  | Niche but clean                              |
| ai-safety         | AI safety engineer, responsible AI, AI ethics                    | 8      | 0             | 100%  | Niche but 100% unique — good for agentic era |
| mobile-dev        | mobile developer, iOS developer, Android developer               | 50     | 0             | 100%  | Max results (98 fetched, capped at 50)       |
| database-engineer | database engineer, DBA, database architect                       | 28     | 0             | 100%  | Good volume                                  |
| rust-go-modern    | Rust developer, Go developer, Golang engineer                    | 5      | 0             | 100%  | Very niche — few listings                    |
| ml-scientist      | machine learning scientist, applied ML, ML researcher            | 49     | 1             | 98%   | Excellent for ML research roles              |
| technical-lead    | technical lead, engineering manager, staff engineer              | 18     | 0             | 100%  | Good for senior-level signals                |
| platform-engineer | platform engineer, developer experience, internal tools engineer | 19     | 0             | 100%  | Good DevEx/platform signals                  |


**Round 3 Total: 286 new records from 120 requests (2.38 records/request after dedup)**

## Top Performers for AI/Agentic Role Coverage

Ranked by value for exercising AI/agentic pipeline features (SOC classification, ESCO taxonomy, temporal period analysis, skill/tool signal density):

### Tier 1 — Best AI/ML signal density


| Query             | Staged | Why                                                |
| ----------------- | ------ | -------------------------------------------------- |
| **ml-scientist**  | 49     | ML research roles with rich skill taxonomies       |
| **ai-research**   | 18     | Applied science roles, strong ESCO mapping         |
| **agentic-ai**    | 19     | Direct agentic era roles, autonomous systems       |
| **deep-learning** | 12     | NLP/CV specialists, dense tool signals             |
| **ai-safety**     | 8      | Responsible AI, emerging agentic era roles         |
| **prompt-llm**    | 2      | High dedup (overlap), but exact target when unique |


### Tier 2 — Strong AI-adjacent signal density


| Query                    | Staged | Why                                                |
| ------------------------ | ------ | -------------------------------------------------- |
| **data-engineering**     | 28     | Pipeline tools (Spark, Airflow, dbt), ETL patterns |
| **data-science**         | 24     | Broad ML/stats tooling, Python ecosystem           |
| **python-developer**     | 37     | Often includes ML/AI libraries in requirements     |
| **cloud-data**           | 19     | Cloud-native data infra (Azure ML, SageMaker)      |
| **software-engineering** | 43     | Broad tech stack signals, high volume              |
| **product-tech**         | 27     | AI product management, strategy signals            |


### Tier 3 — Volume but lower AI signal


| Query                   | Staged | Why                                             |
| ----------------------- | ------ | ----------------------------------------------- |
| **site-reliability**    | 50     | Max volume, strong infra tooling but less AI    |
| **robotics-automation** | 50     | Max volume, good for automation but less LLM/AI |
| **mobile-dev**          | 50     | Max volume, framework signals but minimal AI    |
| **systems-engineer**    | 50     | Max volume, Linux/infra but little AI           |
| **java-enterprise**     | 49     | High volume, enterprise patterns but less AI    |


### Tier 4 — Low yield or high dedup


| Query               | Staged | Why                                     |
| ------------------- | ------ | --------------------------------------- |
| **ml-ops**          | 3      | Niche + high dedup from prior runs      |
| **devops-cloud**    | 3      | High dedup — "cloud architect" overlaps |
| **cybersecurity**   | 1      | Nearly all duplicates                   |
| **quant-fintech**   | 2      | Very niche, few listings                |
| **blockchain-web3** | 2      | Very niche, few listings                |
| **rust-go-modern**  | 5      | Niche modern languages                  |


## Recommendations for Future Ingestion Runs

1. **Prioritize Tier 1 + Tier 2 queries** for AI/agentic pipeline testing.
2. **Drop high-dedup queries** (cybersecurity, devops-cloud, ml-ops) unless prior-run records are purged.
3. **Add date filters** to JSearch queries if the API supports them, to get fresher postings with agentic era signals.
4. **Rotate keyword variants** between runs: e.g., "generative AI engineer" instead of "AI engineer" to avoid dedup.
5. **Tier 3 queries are useful for volume** when you need diverse role types for analytics/visualization testing, but contribute less to AI taxonomy coverage.

