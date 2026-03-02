# Job Intelligence Engine — Canonical Architecture (Phase 1 / Phase 2)
**Audience:** Implementing engineers, Claude Code
**Version:** 1.1 | **Source of truth:** `job_intelligence_engine_architecture.docx`
**Last updated:** 2026-02-18
**Status:** Reference implementation for Phase 1. Technology choices classified as SA (Student ADR) in `ARCHITECTURAL_DECISIONS.md` are subject to team ADR decisions. If a team selects a different technology, adapt the corresponding agent implementation accordingly. Infrastructure constraints (IC) are fixed by the existing platform. Phase 2 items are marked explicitly — do not implement them in Phase 1 unless instructed.

---

## Non-Negotiable Rules

1. **One agent = one responsibility.** Helper logic (dedup, validation, field mapping, confidence scoring) stays encapsulated inside the owning agent. Never promoted to its own agent.
2. **Agents communicate via typed, versioned events only.** Direct function calls between agents are forbidden.
3. **The Orchestration Agent is the sole consumer** of `*Failed` and `*Alert` events. No other agent reacts to another agent's failures.
4. **No agent writes to another agent's internal state.**
5. **Every agent exposes a `health_check()` method** and emits self-evaluation metrics.
6. **Python agents access MSSQL via SQLAlchemy only.** Prisma is Next.js-only.
7. **No credentials in code.** Environment variables only.
8. **Do not modify the Next.js app or `prisma/schema.prisma`** unless explicitly instructed.

---

## Repository Structure

```
/                              ← Next.js app root (DO NOT MODIFY)
├── app/
├── prisma/schema.prisma       ← Read-only from Python
└── agents/
    ├── ingestion/
    │   ├── agent.py
    │   ├── sources/           ← jsearch_adapter.py, scraper_adapter.py
    │   ├── deduplicator.py
    │   └── tests/
    ├── normalization/
    │   ├── agent.py
    │   ├── schema/            ← Canonical JobRecord + Pydantic validators
    │   ├── field_mappers/
    │   └── tests/
    ├── skills_extraction/
    │   ├── agent.py
    │   ├── models/            ← LLM wrappers + prompt files
    │   ├── taxonomy/
    │   └── tests/
    ├── enrichment/
    │   ├── agent.py
    │   ├── classifiers/       ← Role, seniority, quality, spam (Phase 1)
    │   ├── resolvers/         ← Company, geo, labor-market lookups (Phase 2)
    │   └── tests/
    ├── analytics/
    │   ├── agent.py
    │   ├── aggregators/
    │   ├── query_engine/      ← Text-to-SQL + guardrails
    │   └── tests/
    ├── visualization/
    │   ├── agent.py
    │   ├── renderers/
    │   ├── exporters/         ← PDF, CSV, JSON
    │   └── tests/
    ├── orchestration/
    │   ├── agent.py
    │   ├── scheduler/         ← APScheduler wrapper
    │   ├── circuit_breaker/   ← Phase 2
    │   ├── saga/              ← Phase 2
    │   ├── admin_api/         ← Phase 2
    │   └── tests/
    ├── demand_analysis/       ← Phase 2 — scaffold only in Phase 1
    │   ├── agent.py
    │   ├── time_series/
    │   ├── forecasting/
    │   └── tests/
    ├── common/
    │   ├── events/
    │   ├── message_bus/       ← SA #14 — reference impl: in-process pub/sub (Phase 1)
    │   ├── llm_adapter.py
    │   ├── data_store/
    │   ├── config/
    │   ├── observability/
    │   └── errors/
    ├── dashboard/
    │   └── streamlit_app.py
    ├── platform/              ← Scaffold in Phase 1; populated in Phase 2
    │   ├── infrastructure/
    │   ├── ci_cd/
    │   ├── monitoring/
    │   └── runbooks/
    ├── data/
    │   ├── staging/
    │   ├── normalized/
    │   ├── enriched/
    │   ├── analytics/
    │   ├── demand_signals/    ← Phase 2
    │   ├── rendered/
    │   └── dead_letter/
    ├── eval/                  ← 30–50 hand-labeled JSON records
    ├── docs/
    │   ├── architecture/
    │   ├── api/               ← Agent & admin API contracts
    │   └── adr/               ← Architecture Decision Records
    └── tests/
```

---

## Common Patterns — Follow Exactly

> **Note:** The patterns below use reference implementation technologies. If your team's ADRs selected different tools for SA-classified decisions, adapt the implementation while preserving the contract (the abstract interface, event types, and method signatures). Engineering rules apply regardless of technology choices.

### Event envelope

```python
@dataclass
class AgentEvent:
    event_id: str          # uuid4
    correlation_id: str    # propagated unchanged from IngestBatch onward
    agent_id: str
    timestamp: datetime
    schema_version: str    # "1.0"
    payload: dict
```

### LLM adapter

```python
from agents.common.llm_adapter import get_adapter
adapter = get_adapter(provider=os.getenv("LLM_PROVIDER", "azure_openai"))
result = adapter.complete(prompt=prompt, schema=OutputSchema)
```

Fallback: 2 retries → log to `llm_audit_log` → `extraction_status = "failed"` → continue batch.

### Structured logging (no PII)

```python
import structlog
log = structlog.get_logger()
log.info("ingestion_batch_complete", batch_id=batch_id, record_count=n, dedup_count=d)
```

### Health check (required on every agent)

```python
def health_check(self) -> dict:
    return {"status": "ok", "agent": "ingestion", "last_run": self.last_run_at.isoformat(), "metrics": self.last_run_metrics}
```

---

## Canonical JobRecord Schema

```python
class SkillRecord(BaseModel):
    skill_id: Optional[str]
    label: str
    type: str                     # Technical | Domain | Soft | Certification | Tool
    confidence: float
    field_source: str             # title | description | requirements | responsibilities
    required_flag: Optional[bool]

class JobRecord(BaseModel):
    # Identity
    external_id: str
    source: str                   # "jsearch" | "crawl4ai"
    ingestion_run_id: str
    raw_payload_hash: str

    # Core
    title: str
    company: str
    location: Optional[str]
    salary_raw: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_currency: Optional[str]
    salary_period: Optional[str]  # annual | hourly | monthly
    employment_type: Optional[str]
    date_posted: Optional[datetime]
    description: Optional[str]

    # Skills Extraction output
    skills: List[SkillRecord] = []
    extraction_status: Optional[str]  # ok | failed | partial

    # Phase 1 Enrichment output
    seniority: Optional[str]
    role_classification: Optional[str]
    sector_id: Optional[int]
    quality_score: Optional[float]
    is_spam: Optional[bool]
    spam_score: Optional[float]
    ai_relevance_score: Optional[float]
    company_id: Optional[int]
    location_id: Optional[int]
    overall_confidence: Optional[float]
    field_confidence: Optional[dict]

    # Phase 2 Enrichment additions (commented out — do not implement in Phase 1)
    # company_industry: Optional[str]
    # company_size_band: Optional[str]
    # company_funding_stage: Optional[str]
    # region: Optional[str]
    # metro_area: Optional[str]
    # remote_classification: Optional[str]
    # soc_code: Optional[str]
    # noc_code: Optional[str]
    # prevailing_wage_band: Optional[str]
    # enrichment_partial: Optional[bool]
    # enrichment_quality_score: Optional[float]
```

---

## Agent Specifications

### 1. Ingestion Agent
**File:** `agents/ingestion/agent.py` | **Emits:** `IngestBatch` | **Writes to:** `raw_ingested_jobs`

**Phase 1 responsibilities:**
- Poll JSearch via `httpx`; scrape via Crawl4AI [SA #12 — reference implementation]
- Fingerprint: `sha256(source + external_id + title + company + date_posted)`
- Dedup against `raw_ingested_jobs.raw_payload_hash`; discard silently; increment counter
- JSearch wins over scraped when same job appears in both (IC #9)
- Provenance tags: `source`, `external_id`, `raw_payload_hash`, `ingestion_run_id`, `ingestion_timestamp`

**Error handling:**
- Source unreachable: exponential back-off, max 5 retries → `SourceFailure` to Orchestrator
- Partial batch: stage successful records; mark failures; do not block downstream
- Schema violation at intake: quarantine to `data/dead_letter/`

| Metric | Target |
|--------|--------|
| Ingest success rate | ≥ 98% per 24h |
| Duplicate rate forwarded | < 0.5% |
| Dead-letter volume | < 1%; alert above 2% |

---

### 2. Normalization Agent
**File:** `agents/normalization/agent.py` | **Consumes:** `IngestBatch` | **Emits:** `NormalizationComplete` | **Writes to:** `normalized_jobs`

**Phase 1 responsibilities:**
- Map source fields → `JobRecord` via per-source field mappers
- Standardize: dates (ISO 8601), salaries (min/max/currency/period), locations, employment types
- Strip HTML, clean whitespace, sanitize free-text
- Validate against Pydantic schema; quarantine violations

**Error handling:**
- Violation: quarantine with annotated error path; do not block batch
- Ambiguous mapping: best-effort; `low_confidence = true`
- Currency failure: store raw; `currency_normalized = false`
- Batch failure: `NormalizationFailed` → Orchestrator

| Metric | Target |
|--------|--------|
| Schema conformance | ≥ 99% |
| Field mapping accuracy | ≥ 97% (spot check) |
| Salary normalization coverage | ≥ 90% |
| Processing latency | Median < 200ms; p99 < 1s |
| Quarantine rate | < 1%; alert above 3% |

---

### 3. Skills Extraction Agent
**File:** `agents/skills_extraction/agent.py` | **Consumes:** `NormalizationComplete` | **Emits:** `SkillsExtracted`

**Phase 1 responsibilities:**
- LLM inference over `title`, `description`, `requirements`, `responsibilities`
- Produce `SkillRecord` per skill: `label`, `type`, `confidence`, `field_source`, `required_flag`
- Taxonomy linking order:
  1. Exact name match → `skills` table
  2. Normalized name match → `skills` table
  3. Embedding cosine similarity ≥ 0.92 → `skills` table
  4. O*NET occupation code match
  5. Emit as `raw_skill` (null taxonomy ID) — Enrichment resolves in Phase 2
- Log all LLM calls to `llm_audit_log`

**Error handling:**
- LLM timeout: retry once → `skills = []`, `extraction_status = "failed"`; continue batch
- Rate limit: back-off and queue; alert Orchestrator if queue > threshold

| Metric | Target |
|--------|--------|
| Precision at taxonomy link | ≥ 92% (human eval) |
| Recall of key skills | ≥ 88% |
| Taxonomy coverage | ≥ 95% |
| Avg confidence | ≥ 0.80 |
| Throughput | ≥ 500 records/min at p50 |

---

### 4. Enrichment Agent
**File:** `agents/enrichment/agent.py` | **Consumes:** `SkillsExtracted` | **Emits:** `RecordEnriched` | **Writes to:** `job_postings`

#### Phase 1 — Lite (implement now)
- Classify job role and seniority
- Quality score [0–1]: completeness, linguistic clarity, AI keyword density, structural coherence
- Spam detection (IC #8):
  - < 0.7 → proceed
  - 0.7–0.9 → flag for operator review (`is_spam = null`)
  - > 0.9 → auto-reject; do not write to `job_postings`
- Resolve `company_id`: match `companies` by normalized name → no match: create placeholder
- Resolve `location_id`: match `company_addresses` → no match: store text, `location_id = null`
- Write to `job_postings` only after `company_id` resolved
- Map `sector_id` → `industry_sectors`

#### Phase 2 — Full (do not implement in Phase 1)
- Resolve `raw_skill` entries against alternative taxonomy sources
- Company-level data: industry, size band, funding stage
- Geographic enrichment: region, metro, remote classification
- Labor-market: BLS/ONS, SOC/NOC code, prevailing wage band
- Composite enrichment quality score

**Error handling:**
- Phase 1: classifier unavailable → skip scoring, flag, continue
- Phase 2: external lookup failure → null field, `enrichment_partial = true`, continue

| Metric | Phase | Target |
|--------|-------|--------|
| Classification F1 | 1 | Tracked |
| Spam precision | 1 | High — minimize false positives |
| Quality correlation | 1 | Tracked vs human |
| Company match rate | 2 | ≥ 90% |
| Geo enrichment rate | 2 | ≥ 95% |
| SOC/NOC coverage | 2 | ≥ 85% |
| Raw skill resolution | 2 | ≥ 75% |
| Enrichment quality avg | 2 | ≥ 0.85 |

---

### 5. Analytics Agent
**File:** `agents/analytics/agent.py` | **Consumes:** `RecordEnriched` | **Emits:** `AnalyticsRefreshed`
**Exposes:** `POST /analytics/query` (REST) [SA #18 — reference implementation]

**Phase 1 responsibilities:**
- Aggregates across dimensions: skill, role, industry, region, experience level, company size
- Salary distributions: median, p25, p75, p95 per dimension intersection
- Co-occurrence matrices (skills appearing together)
- Posting lifecycle metrics: time-to-fill proxies, repost rates, posting duration
- Weekly insight summaries: LLM-generated; template fallback if unavailable
- Text-to-SQL Q&A with guardrails

**SQL guardrails (always enforced):**
- SELECT only — no INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, EXEC
- Allowed tables allowlist only
- 100-row max; 30-second timeout
- All attempts logged to `llm_audit_log`

**Error handling:**
- Stale data: surface timestamp; recompute if > SLA
- SQL error: retry once with self-correction → return error with explanation
- Query timeout: partial result with `is_partial = true`
- Cardinality explosion: configurable cap; coalesce long-tail into "Other"; emit warning
- LLM unavailable: template fallback; never block aggregate refresh

| Metric | Target |
|--------|--------|
| Aggregate accuracy | ≥ 99.5% vs raw recount |
| Query p50 latency | < 500ms |
| Aggregate freshness | Within 15 min of new enriched batch |
| Salary distribution coverage | ≥ 80% of role/region intersections with sufficient N |

---

### 6. Visualization Agent
**File:** `agents/visualization/agent.py` + `agents/dashboard/streamlit_app.py`
**Consumes:** `AnalyticsRefreshed`, `DemandSignalsUpdated` (Phase 2)
**Emits:** `RenderComplete` | **DB:** Read-only SQLAlchemy

**Phase 1 dashboard pages:**

| Page | Features |
|------|---------|
| Ingestion Overview | Runs per day, records ingested, dedup rate, error rate, recent runs table |
| Normalization Quality | Quarantine count by error type, field mapping spot-check, salary coverage |
| Skill Taxonomy Coverage | % mapped vs unmapped (gauge), skill type distribution, unmapped list |
| Weekly Insights | LLM or template summary + supporting charts |
| Ask the Data | Natural language input, generated SQL code block, result table |
| Operations & Alerts | Active alerts (severity-sorted), alert history, per-agent health |

**Exports:** PDF summaries, CSV, JSON — all standard in Phase 1, not stretch.

**Cache:** TTL-based. Stale data served with banner + `VisualizationDegraded` alert — never blank page.

**Error handling:**
- Upstream unavailable: stale + banner + alert
- Render failure: retry once → `RenderFailed` → placeholder
- Export timeout: stream partial with truncation notice

| Metric | Target |
|--------|--------|
| Render success rate | ≥ 99.5% |
| Freshness | Within 5 min of trigger |
| Export p95 | < 10s |
| Cache hit rate | ≥ 70% |

---

### 7. Orchestration Agent
**File:** `agents/orchestration/agent.py` | **Framework:** LangGraph StateGraph [SA #13/#16] + APScheduler [IC]

#### Phase 1 — Basic (implement now)
- Master run schedule; trigger pipeline steps in sequence
- LangGraph StateGraph for event routing
- Retry policies with exponential back-off + jitter
- Sole consumer of all `*Failed` / `*Alert` events
- Structured JSON audit log (100% completeness)
- System-wide health monitoring

**Alerting tiers:**
- **Warning:** logged + metric emitted
- **Critical:** paged to on-call
- **Fatal:** circuit broken + human escalation

**Retry policies:**

| Agent | Max retries | Back-off |
|-------|------------|---------|
| Ingestion (source unreachable) | 5 | Exponential + jitter |
| Normalization (batch failure) | 3 | Exponential |
| Skills Extraction (LLM timeout) | 2 per record | Fixed 2s |
| Any agent (transient DB error) | 3 | Exponential |

#### Phase 2 — Full (do not implement in Phase 1)
- Circuit-breaking: ≥ 90% precision target (no false positives)
- Saga pattern: explicit gates at stage transitions
- Compensating flows: re-queue at last successful checkpoint
- Admin API for manual overrides, re-runs, config changes

| Metric | Target |
|--------|--------|
| Pipeline SLA | ≥ 95% of batches |
| MTTD | < 60s |
| MTTR (auto) | < 5 min |
| Circuit-break precision | ≥ 90% (Phase 2) |
| Audit log completeness | 100% |

---

### 8. Demand Analysis Agent *(Phase 2 only — scaffold directory, do not implement)*
**File:** `agents/demand_analysis/agent.py` | **Consumes:** `RecordEnriched` | **Emits:** `DemandSignalsUpdated`

- Time-series index: skill, role, industry, region
- Velocity windows: 7d, 30d, 90d
- Emerging vs declining skills identification
- Supply/demand gap estimates where candidate-side data available
- 30-day demand forecasts (configurable horizon)
- `DemandAnomaly` events on detected spikes or cliffs

| Metric | Target |
|--------|--------|
| Forecast MAPE (30-day) | < 15% |
| Trend accuracy | ≥ 85% |
| Signal freshness | Within 1h of new batch |
| Anomaly precision | ≥ 80% |

---

## Event Catalog

| Event | Producer | Consumers |
|-------|----------|-----------|
| `IngestBatch` | Ingestion | Normalization, Orchestrator |
| `NormalizationComplete` | Normalization | Skills Extraction, Orchestrator |
| `SkillsExtracted` | Skills Extraction | Enrichment, Orchestrator |
| `RecordEnriched` | Enrichment | Analytics, Demand Analysis*, Orchestrator |
| `DemandSignalsUpdated` | Demand Analysis* | Analytics, Visualization, Orchestrator |
| `AnalyticsRefreshed` | Analytics | Visualization, Orchestrator |
| `RenderComplete` | Visualization | Orchestrator |
| `*Failed` / `*Alert` | Any agent | **Orchestrator only** |
| `SourceFailure` | Ingestion | Orchestrator |
| `DemandAnomaly` | Demand Analysis* | Orchestrator |

*Phase 2

---

## Database Schema Extensions

```sql
-- Phase 1 additions to job_postings (SQLAlchemy migration only — never touch schema.prisma)
ALTER TABLE job_postings ADD COLUMN source NVARCHAR(50);
ALTER TABLE job_postings ADD COLUMN external_id NVARCHAR(255);
ALTER TABLE job_postings ADD COLUMN ingestion_run_id NVARCHAR(36);
ALTER TABLE job_postings ADD COLUMN ai_relevance_score FLOAT;
ALTER TABLE job_postings ADD COLUMN quality_score FLOAT;
ALTER TABLE job_postings ADD COLUMN is_spam BIT;
ALTER TABLE job_postings ADD COLUMN spam_score FLOAT;
ALTER TABLE job_postings ADD COLUMN overall_confidence FLOAT;
ALTER TABLE job_postings ADD COLUMN field_confidence NVARCHAR(MAX); -- JSON

-- Phase 2 additions
ALTER TABLE job_postings ADD COLUMN enrichment_quality_score FLOAT;
ALTER TABLE job_postings ADD COLUMN enrichment_partial BIT;
ALTER TABLE job_postings ADD COLUMN soc_code NVARCHAR(20);
ALTER TABLE job_postings ADD COLUMN remote_classification NVARCHAR(50);
```

**Agent-managed tables:**

| Table | Phase | Purpose |
|-------|-------|---------|
| `raw_ingested_jobs` | 1 | Ingestion staging |
| `normalized_jobs` | 1 | Post-normalization records |
| `job_ingestion_runs` | 1 | Batch tracking |
| `alerts` | 1 | Active and historical alerts |
| `orchestration_audit_log` | 1 | All orchestration decisions |
| `llm_audit_log` | 1 | All LLM calls |
| `analytics_aggregates` | 1 | Computed aggregates |
| `demand_signals` | 2 | Trend and forecast outputs |

---

## System-Level Error-Handling

| Strategy | Phase | How It Works |
|----------|-------|-------------|
| Dead-letter store | 1 | All retry-exhausted records quarantined with full error context |
| Exponential back-off | 1 | Back-off + jitter on all retries; max per agent and error class |
| Graceful degradation | 1 | Analytics/Visualization serve stale with flags; pipeline never halts for non-critical failures |
| Alerting tiers | 1 | Warning: log + metric. Critical: page. Fatal: circuit break + escalation |
| Circuit breaker | 2 | Orchestrator opens when error rate > threshold |
| Compensating sagas | 2 | Mid-pipeline failure rolls back to last successful checkpoint |

---

## Environment Variables

> Variables for SA-classified tools reflect the **reference implementation**. If the team selects different technologies via their ADRs, the corresponding env vars will change (e.g., a different tracing tool replaces `LANGSMITH_API_KEY`).

```bash
# SA #11 — LLM provider (reference: Azure OpenAI)
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT_NAME=
LLM_PROVIDER=azure_openai             # azure_openai | openai | anthropic

# IC #19 — Database (MSSQL — fixed)
DATABASE_URL=                          # MSSQL pyodbc connection string

# SA #17 — Agent tracing (reference: LangSmith)
LANGSMITH_API_KEY=
LANGCHAIN_TRACING_V2=true

# SA #12 — Ingestion sources (reference: httpx + Crawl4AI)
JSEARCH_API_KEY=
SCRAPING_TARGETS=                      # Comma-separated URLs

# IC #3 — Scheduling
INGESTION_SCHEDULE=0 2 * * *           # Cron — default: daily at 2am

# IC #8 — Spam thresholds
SPAM_FLAG_THRESHOLD=0.7
SPAM_REJECT_THRESHOLD=0.9

# Agent configuration
SKILL_CONFIDENCE_THRESHOLD=0.75
BATCH_SIZE=100
```

---

## Build Order

| Week(s) | Deliverable |
|---------|------------|
| 1–2 | Environment, first scrape, walking skeleton (8 agent stubs, pipeline runner, journey dashboard) |
| 3 | Ingestion Agent + Normalization Agent |
| 4 | Skills Extraction Agent + evaluation harness + Enrichment-lite |
| 5 | Visualization Agent |
| 6 | Orchestration Agent |
| 7 | Analytics Agent — aggregates + weekly insights |
| 8 | Analytics Agent — Ask the Data |
| 9 | Pipeline hardening (near-dedup, event contract enforcement) |
| 10 | Testing, security review, load testing |
| 11 | Documentation |
| 12 | Capstone demo + `v0.1.0-capstone` |

---

## What NOT to Do

- Do NOT create new agents for helper logic
- Do NOT make agents call each other directly
- Do NOT use Prisma from Python
- Do NOT write to `job_postings` without a resolved `company_id`
- Do NOT store credentials in code or logs
- Do NOT implement Phase 2 items during Phase 1
- Do NOT skip tests
- Do NOT modify the Next.js app or `prisma/schema.prisma` unless explicitly instructed
