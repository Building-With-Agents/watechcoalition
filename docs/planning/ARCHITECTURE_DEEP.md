# Job Intelligence Engine — Canonical Architecture (Phase 1 / Phase 2)
**Audience:** Implementing engineers, Claude Code
**Version:** 2.0 | **Source of truth:** `job_intelligence_engine_architecture.docx` + JIE Client Specs (v2)
**Last updated:** 2026-03-12
**Status:** Reference implementation for Phase 1. Tool decisions classified as Student ADR in `ARCHITECTURAL_DECISIONS.md` are subject to team ADR decisions. If a team selects a different technology, adapt the corresponding agent implementation accordingly. Architectural and Product decisions marked as Fixed are set by the existing platform. Phase 2 items are marked explicitly — do not implement them in Phase 1 unless instructed.

---

## Non-Negotiable Rules

1. **One agent = one responsibility.** Helper logic (dedup, validation, field mapping, confidence scoring) stays encapsulated inside the owning agent. Never promoted to its own agent.
2. **Agents communicate via typed, versioned events only.** Direct function calls between agents are forbidden.
3. **The Orchestration Agent is the sole consumer** of `*Failed` and `*Alert` events. No other agent reacts to another agent's failures.
4. **No agent writes to another agent's internal state.**
5. **Every agent exposes a `health_check()` method** and emits self-evaluation metrics.
6. **Python agents access PostgreSQL via SQLAlchemy only.** Prisma is Next.js-only.
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
    ├── skills_extraction/     ← Work Intelligence Agent (directory kept for git history)
    │   ├── agent.py
    │   ├── models/            ← LLM wrappers + prompt files
    │   ├── extractors/        ← Per-dimension extraction: skills, tools, tasks, responsibilities, context
    │   ├── taxonomy/          ← ESCO store, GenAI Extension Layer, taxonomy resolution
    │   ├── cost/              ← Token cost tracking, budget enforcement
    │   └── tests/
    ├── enrichment/
    │   ├── agent.py
    │   ├── classifiers/       ← Role, seniority, quality, spam, SOC/NAICS, temporal period
    │   ├── resolvers/         ← Company, geo, Borderplex subregion, employer profile
    │   ├── dedup/             ← Fuzzy deduplication (cosine similarity)
    │   ├── adapters/          ← External data: BLS, ONET, Census (stubs in Phase 1)
    │   └── tests/
    ├── analytics/
    │   ├── agent.py
    │   ├── aggregators/       ← 10 aggregate table builders
    │   ├── clustering/        ← CanonicalRole discovery, embedding pipelines
    │   ├── disruption/        ← DisruptionFingerprint computation, 4 disruption patterns
    │   ├── query_engine/      ← Workforce Intelligence Q&A + SQL guardrails
    │   ├── triggers/          ← On-demand: gap analysis, employer comparison, benchmarks
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
    │   ├── message_bus/       ← Tool #14 — reference impl: in-process pub/sub (Phase 1)
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

> **Note:** The patterns below use reference implementation technologies. If your team's ADRs selected different tools for Student ADR decisions, adapt the implementation while preserving the contract (the abstract interface, event types, and method signatures). Engineering rules apply regardless of technology choices.

### Event envelope

```python
from pydantic import BaseModel

class EventEnvelope(BaseModel):
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
def health_check(self) -> bool:
    """Return True only if all dependencies are reachable."""
    # Check DB connection, fixture files, LLM connectivity as needed
    return True
```

---

## Canonical Schemas

### Work Intelligence Extraction Schemas

```python
class SpanRecord(BaseModel):
    """Source text span for provenance tracking."""
    text: str
    field_source: str             # title | description | requirements | responsibilities
    char_start: int
    char_end: int

class SkillRecord(BaseModel):
    skill_id: Optional[str]
    label: str
    type: str                     # Technical | Domain | Soft | Certification | Tool
    confidence: float
    field_source: str             # title | description | requirements | responsibilities
    required_flag: Optional[bool]
    esco_uri: Optional[str]       # ESCO digital skills cluster URI
    is_genai_extension: bool = False  # True if from GenAI Extension Layer
    source_span: Optional[SpanRecord]

class ToolRecord(BaseModel):
    tool_id: Optional[str]
    label: str
    category: str                 # language | framework | platform | database | devops | ai_tool | other
    confidence: float
    field_source: str
    source_span: Optional[SpanRecord]

class TaskRecord(BaseModel):
    task_id: Optional[str]
    description: str
    complexity: Optional[str]     # routine | analytical | creative | strategic
    confidence: float
    field_source: str
    source_span: Optional[SpanRecord]

class ResponsibilityRecord(BaseModel):
    responsibility_id: Optional[str]
    description: str
    scope: Optional[str]          # individual | team | department | organization
    confidence: float
    field_source: str
    source_span: Optional[SpanRecord]

class ContextSignal(BaseModel):
    signal_type: str              # remote_policy | team_size | reporting_structure | growth_stage | ai_usage
    value: str
    confidence: float
    field_source: str

class ExtractionMetadata(BaseModel):
    extraction_version: str
    extraction_model: str         # Model used (e.g., "claude-sonnet-4-5", "claude-haiku-4-5")
    extraction_tokens_used: int
    extraction_cost_usd: float
    pass1_pattern_matches: int    # Hybrid Pass 1: pattern matching hits
    pass2_llm_calls: int          # Hybrid Pass 2: LLM inference calls
    extraction_warnings: List[str] = []
```

### GenAI Extension Layer

10 predefined GenAI skills injected atop ESCO taxonomy when detected in job postings:

| GenAI Skill | ESCO Mapping |
|---|---|
| Prompt Engineering | Digital skills cluster — extension |
| RAG (Retrieval-Augmented Generation) | Digital skills cluster — extension |
| LLM Fine-tuning | Digital skills cluster — extension |
| AI Governance | Digital skills cluster — extension |
| Agentic Systems Design | Digital skills cluster — extension |
| AI Output Validation | Digital skills cluster — extension |
| AI Tool Integration | Digital skills cluster — extension |
| Foundation Model Selection | Digital skills cluster — extension |
| Vector Database Management | Digital skills cluster — extension |
| AI Safety and Alignment | Digital skills cluster — extension |

### Enrichment Schemas

```python
class TemporalPeriod(str, Enum):
    PRE_CHATGPT = "pre_chatgpt"       # Before Nov 2022
    EARLY_GENAI = "early_genai"        # Dec 2022 – Mar 2023
    POST_GPT4 = "post_gpt4"           # Apr 2023 – May 2024
    AGENTIC_ERA = "agentic_era"        # Jun 2024 – present

class EmployerProfile(BaseModel):
    company_size: str             # startup | smb | mid_market | enterprise | unknown
    ai_maturity_signal: str       # ai_native | ai_adopting | ai_exploring | traditional | unknown
    sector: Optional[str]
    is_known_employer: bool

class EnrichedJobProfile(BaseModel):
    """Wraps JobRecord + all enrichment fields for downstream consumption."""
    job_record: JobRecord
    temporal_period: TemporalPeriod
    borderplex_subregion: Optional[str]  # el_paso | las_cruces | ciudad_juarez | regional
    employer_profile: Optional[EmployerProfile]
    soc_code: Optional[str]
    naics_code: Optional[str]
    is_duplicate: bool = False
    duplicate_cluster_id: Optional[str]
```

### Analytics Schemas

```python
class CanonicalRole(BaseModel):
    role_id: str
    label: str
    cluster_centroid: List[float]  # Embedding vector
    posting_count: int
    representative_titles: List[str]
    top_skills: List[str]
    top_tools: List[str]

class DisruptionFingerprint(BaseModel):
    canonical_role_id: str
    disruption_category: List[str]    # Displacement | Augmentation | Transformation | Emergence
    disruption_intensity: float       # 0.0 – 1.0
    skill_velocity: List[dict]        # [{skill, direction, magnitude}]
    tool_transition: List[dict]       # [{old_tool, new_tool, adoption_rate}]
    task_shift: List[dict]            # [{task, change_type, magnitude}]
    responsibility_expansion: float   # Net change in responsibility scope
    ai_intensity_trend: str           # increasing | stable | decreasing
    workflow_restructuring_score: float
    trajectory: str                   # expanding | stable | contracting | emerging
    period_comparison: List[dict]     # [{period, metrics}]

class TrajectoryRecord(BaseModel):
    canonical_role_id: str
    direction: str                    # expanding | stable | contracting | emerging
    confidence: float
    estimated_stabilization_quarters: Optional[int]
    key_drivers: List[str]
    workforce_program_signal: Optional[str]  # Curriculum recommendation
```

### JobRecord (Canonical)

```python
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

    # Work Intelligence extraction output
    skills: List[SkillRecord] = []
    tools: List[ToolRecord] = []
    tasks: List[TaskRecord] = []
    responsibilities: List[ResponsibilityRecord] = []
    context_signals: List[ContextSignal] = []
    extraction_metadata: Optional[ExtractionMetadata]
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
    temporal_period: Optional[TemporalPeriod]
    borderplex_subregion: Optional[str]
    soc_code: Optional[str]
    naics_code: Optional[str]
    employer_profile: Optional[EmployerProfile]
    is_duplicate: bool = False
```

---

## Agent Specifications

### 1. Ingestion Agent
**File:** `agents/ingestion/agent.py` | **Emits:** `IngestBatch` | **Writes to:** `raw_ingested_jobs`

**Phase 1 responsibilities:**
- Poll JSearch via `httpx`; scrape via Crawl4AI [Tool #12 — reference implementation]
- Fingerprint: `sha256(source + external_id + title + company + date_posted)`
- Dedup against `raw_ingested_jobs.raw_payload_hash`; discard silently; increment counter
- JSearch wins over scraped when same job appears in both (Product #9)
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

### 3. Work Intelligence Agent *(formerly Skills Extraction Agent)*
**File:** `agents/skills_extraction/agent.py` (directory kept for git history) | **Consumes:** `NormalizationComplete` | **Emits:** `SkillsExtracted` | **Writes to:** `extracted_intelligence`

**Phase 1 responsibilities:**

**Hybrid extraction strategy (two-pass):**
- **Pass 1 — Pattern matching:** Extract tools and context signals using regex, keyword lists, and heuristic patterns. Fast, cheap, high-precision for structured data.
- **Pass 2 — LLM inference:** Extract skills, tasks, and responsibilities using structured LLM prompts over `title`, `description`, `requirements`, `responsibilities` fields.

**Six extraction dimensions:**

| Dimension | Strategy | Model Tier | Output Schema |
|---|---|---|---|
| Skills | LLM (Pass 2) | Sonnet-class | `SkillRecord` |
| Tools | Pattern matching (Pass 1) | N/A | `ToolRecord` |
| Tasks | LLM (Pass 2) | Haiku-class | `TaskRecord` |
| Responsibilities | LLM (Pass 2) | Sonnet-class | `ResponsibilityRecord` |
| Context | Pattern matching (Pass 1) | N/A | `ContextSignal` |
| *Trajectory* | *Phase 2 — Analytics Agent computes from aggregated data* | — | `TrajectoryRecord` |

**Model tier routing:**
- Sonnet-class (e.g., claude-sonnet-4-5): Skills, Responsibilities — requires nuanced understanding
- Haiku-class (e.g., claude-haiku-4-5): Tasks — simpler extraction, cost-optimized

**Taxonomy resolution:**
- Primary source: ESCO digital skills cluster
- Resolution order:
  1. Exact name match → ESCO skills store
  2. Normalized name match → ESCO skills store
  3. Embedding cosine similarity ≥ 0.92 → ESCO skills store
  4. O*NET occupation code match
  5. GenAI Extension Layer match (10 predefined GenAI skills)
  6. Emit as `raw_skill` (null taxonomy ID) — flagged for review

**GenAI Extension Layer:**
- 10 predefined GenAI skills injected atop ESCO taxonomy (see GenAI Extension Layer table above)
- `is_genai_extension = True` on SkillRecord when matched

**Cost tracking (required):**
- Per-record: `extraction_tokens_used`, `extraction_cost_usd` stored in `extracted_intelligence` table
- Per-dimension token budgets enforced via `compute_extraction_cost()`
- Batch cost projections at 1k / 10k / 100k volumes as required artifact

**All LLM calls logged to `llm_audit_log`**

**Error handling:**
- LLM timeout: retry once → `extraction_status = "failed"`, empty dimension arrays; continue batch
- Rate limit: back-off and queue; alert Orchestrator if queue > threshold
- Pattern matching failure: log warning, skip dimension, continue
- Cost overrun: alert Orchestrator, continue with reduced-tier fallback

| Metric | Target |
|--------|--------|
| Precision at taxonomy link | ≥ 92% (human eval) |
| Recall of key skills | ≥ 88% |
| Taxonomy coverage | ≥ 95% |
| Tool extraction precision | ≥ 95% (pattern matching) |
| Avg confidence | ≥ 0.80 |
| Throughput | ≥ 500 records/min at p50 |
| Cost per 1k records | Tracked; budget TBD |

---

### 4. Enrichment Agent
**File:** `agents/enrichment/agent.py` | **Consumes:** `SkillsExtracted` | **Emits:** `RecordEnriched` | **Writes to:** `job_postings`

#### Phase 1 — Full (implement now)

**Core enrichment (carried forward):**
- Classify job role and seniority
- Quality score [0–1]: completeness, linguistic clarity, AI keyword density, structural coherence
- Spam detection (Product #8):
  - < 0.7 → proceed
  - 0.7–0.9 → flag for operator review (`is_spam = null`)
  - > 0.9 → auto-reject; do not write to `job_postings`
- Resolve `company_id`: match `companies` by normalized name → no match: create placeholder
- Resolve `location_id`: match `company_addresses` → no match: store text, `location_id = null`
- Write to `job_postings` only after `company_id` resolved
- Map `sector_id` → `industry_sectors`

**New: Classification expansions (promoted from Phase 2):**
- **SOC code classification:** Map job titles → Standard Occupational Classification codes
- **NAICS code classification:** Map employer/sector → North American Industry Classification System
- **EmployerProfile construction:**
  - `company_size`: startup | smb | mid_market | enterprise | unknown
  - `ai_maturity_signal`: ai_native | ai_adopting | ai_exploring | traditional | unknown
  - `sector`: industry sector string
  - `is_known_employer`: boolean (matched against known employer list)

**New: Temporal period classification:**
- Classify `date_posted` into temporal periods for longitudinal analysis:
  - `pre_chatgpt`: before Nov 2022
  - `early_genai`: Dec 2022 – Mar 2023
  - `post_gpt4`: Apr 2023 – May 2024
  - `agentic_era`: Jun 2024 – present

**New: Borderplex subregion tagging:**
- Tag location into Borderplex subregions: `el_paso` | `las_cruces` | `ciudad_juarez` | `regional`

**New: Fuzzy deduplication:**
- Embedding-based near-duplicate detection
- Cosine similarity > 0.92 for same company within 30-day window → flag as duplicate
- Cluster survivor selection: keep most complete record, mark others `is_duplicate = true`

**New: External data adapter stubs (Phase 1 = mock data; Phase 2 = full integration):**
- BLS adapter: labor statistics lookups
- ONET adapter: occupation/skill crosswalk
- Census adapter: regional demographics

**Output:** `EnrichedJobProfile` wrapping JobRecord + all enrichment fields

#### Phase 2 — Extended (do not implement in Phase 1)
- Full BLS/ONET/Census integration (replace stubs with live API calls)
- Company-level data: funding stage, detailed industry taxonomy
- Geographic enrichment: metro area, remote classification
- Composite enrichment quality score

**Error handling:**
- Classifier unavailable → skip scoring, flag, continue
- External lookup failure → null field, `enrichment_partial = true`, continue
- Dedup embedding failure → skip dedup for record, log warning

| Metric | Phase | Target |
|--------|-------|--------|
| Classification F1 | 1 | Tracked |
| Spam precision | 1 | High — minimize false positives |
| Quality correlation | 1 | Tracked vs human |
| SOC/NAICS coverage | 1 | ≥ 85% |
| Temporal classification accuracy | 1 | ≥ 99% (date-based) |
| Dedup precision | 1 | ≥ 95% |
| Company match rate | 1 | ≥ 90% |
| Geo enrichment rate | 2 | ≥ 95% |
| Enrichment quality avg | 2 | ≥ 0.85 |

---

### 5. Analytics Agent
**File:** `agents/analytics/agent.py` | **Consumes:** `RecordEnriched` | **Emits:** `AnalyticsRefreshed`, `EmergenceAlert`, `DisruptionRefreshed`
**Exposes:** `POST /analytics/query` (REST) [Contract #18 — reference implementation]

**Phase 1 responsibilities:**

**10 aggregate tables** (replacing single `analytics_aggregates`):

| Table | Purpose | Refresh |
|---|---|---|
| `skill_demand_weekly` | Per-skill posting counts, growth rates | Nightly batch |
| `tool_demand_weekly` | Per-tool posting counts, adoption trends | Nightly batch |
| `role_snapshot_weekly` | Per-CanonicalRole summary stats | Nightly batch |
| `sector_summary_weekly` | Per-sector demand, salary, skill mix | Nightly batch |
| `geo_demand_weekly` | Per-Borderplex-subregion demand | Nightly batch |
| `skill_velocity` | Week-over-week demand change, 4-week rolling trend | Nightly batch |
| `skill_co_occurrence` | Skill pairs appearing together, PMI scores | Nightly batch |
| `trajectory_map` | CanonicalRole trajectory over temporal periods | Nightly batch |
| `posting_freshness` | Data recency, volume tracking, staleness flags | Nightly batch |
| `cohort_gap_cache` | Pre-computed gap analysis for common queries | On-demand + cache |

**13-step internal processing pipeline** (ordered dependency chain):
1. Data validation + freshness check
2. Skill demand aggregation
3. Tool demand aggregation
4. Role clustering (CanonicalRole discovery)
5. Role snapshot computation
6. Sector summary computation
7. Geographic demand aggregation
8. Skill velocity computation
9. Skill co-occurrence computation
10. Disruption fingerprint computation
11. Trajectory mapping
12. Posting freshness update
13. LLM insight summary generation (template fallback)

**CanonicalRole clustering:**
- Discover roles from data using embedding similarity
- Minimum thresholds: 500 total postings, minimum 10 per cluster
- Clustering algorithm: EBS decision (HDBSCAN vs k-means vs hierarchical — Sprint 5)
- Embedding model: EBS decision (Sprint 5)
- Output: `CanonicalRole` records with centroid, representative titles, top skills/tools

**Disruption analysis:**
- Compute `DisruptionFingerprint` per CanonicalRole
- 4 disruption patterns:
  - **Displacement:** AI replacing human tasks, declining posting volume
  - **Augmentation:** AI tools added to existing roles, skill mix expanding
  - **Transformation:** Role fundamentally changing, new skill clusters emerging
  - **Emergence:** New roles with no historical precedent, rapid growth
- `EmergenceAlert` event for posting clusters with no CanonicalRole match

**Nightly batch scheduling:**
- Minimum data guard: skip refresh if < 50 new postings since last run
- Full refresh target: 15 min for 50k records

**On-demand trigger API** (for Workforce Intelligence Q&A):
- `cohort_gap_analysis`: compare skill supply vs demand for a cohort
- `custom_employer_comparison`: compare employer profiles
- `role_benchmark`: benchmark a role against CanonicalRoles
- `emerging_skills_scan`: identify skills with highest velocity

**Workforce Intelligence Q&A:**
- Intent classification: trend | role_evolution | disruption | emergence | curriculum | employer | workflow | geographic | comparison | other
- Knowledge base routing: translates classified intent into structured database queries against aggregate tables
- Synthesis engine: generates natural language answers with evidence citations
- Follow-up scaffolding: suggests 2-3 related questions after each answer
- Response quality requirements:
  - Evidence citation (reference specific aggregate data)
  - Confidence transparency (flag when confidence < 0.6)
  - Volume transparency (flag when based on < 30 postings)
  - Temporal precision (specify which period the data covers)
  - Curriculum relevance (connect insights to workforce programs)
  - Refusal on hallucination (decline rather than fabricate)

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
- Clustering failure: fall back to previous CanonicalRole set; emit warning

| Metric | Target |
|--------|--------|
| Aggregate accuracy | ≥ 99.5% vs raw recount |
| Query p50 latency | < 500ms |
| Aggregate freshness | Within 15 min of new enriched batch |
| Batch processing (50k records) | < 15 min |
| On-demand query response | < 60s |
| Salary distribution coverage | ≥ 80% of role/region intersections with sufficient N |

---

### 6. Visualization Agent
**File:** `agents/visualization/agent.py` + `agents/dashboard/streamlit_app.py`
**Consumes:** `AnalyticsRefreshed`, `DisruptionRefreshed`, `DemandSignalsUpdated` (Phase 2)
**Emits:** `RenderComplete` | **DB:** Read-only SQLAlchemy

**Phase 1 dashboard pages:**

| Page | Features |
|------|---------|
| Ingestion Overview | Runs per day, records ingested, dedup rate, error rate, recent runs table |
| Normalization Quality | Quarantine count by error type, field mapping spot-check, salary coverage |
| Skill Taxonomy Coverage | % mapped vs unmapped (gauge), skill type distribution, unmapped list, GenAI extension hits |
| Weekly Insights | LLM or template summary + supporting charts, disruption highlights |
| Ask the Data (Workforce Intelligence) | Conversational Q&A interface with intent classification, evidence citations, follow-up suggestions |
| Operations & Alerts | Active alerts (severity-sorted), alert history, per-agent health, token cost summary |

**Workforce Intelligence conversational interface** (replaces simple text-to-SQL):
- Natural language input with intent classification
- Structured response with evidence citations from aggregate tables
- Follow-up scaffolding: 2-3 suggested related questions after each answer
- Confidence and volume transparency indicators
- History of recent queries within session

**Exports:** PDF summaries, CSV, JSON — all standard in Phase 1, not stretch.

**Cache:** TTL-based. Stale data served with banner + `VisualizationDegraded` alert — never blank page.

**Error handling:**
- Upstream unavailable: stale + banner + alert
- Render failure: retry once → `RenderFailed` → placeholder
- Export timeout: stream partial with truncation notice
- Q&A synthesis failure: return "insufficient data" with available raw numbers

| Metric | Target |
|--------|--------|
| Render success rate | ≥ 99.5% |
| Freshness | Within 5 min of trigger |
| Export p95 | < 10s |
| Cache hit rate | ≥ 70% |
| Q&A response time | < 10s for standard queries |

---

### 7. Orchestration Agent
**File:** `agents/orchestration/agent.py` | **Framework:** LangGraph StateGraph [Tool #13/#16] + APScheduler [Fixed]

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
**File:** `agents/demand_analysis/agent.py` | **Consumes:** `RecordEnriched`, `AnalyticsRefreshed` | **Emits:** `DemandSignalsUpdated`, `DemandAnomaly`

**Phase 2 scope (enriched from client spec):**
- Time-series index: skill, role, industry, region — aligned with CanonicalRole clustering from Analytics
- Velocity windows: 7d, 30d, 90d
- Emerging vs declining skills identification
- `TrajectoryRecord` time-series: career path projections per CanonicalRole
  - Direction, confidence, estimated stabilization quarters
  - Key drivers (skill shifts, tool transitions, task changes)
  - Workforce program signals (curriculum recommendations)
- 30-day demand forecasts with confidence intervals
- Anomaly detection with significance testing (not just threshold-based)
- Supply/demand gap estimation where candidate-side data available
- `DemandAnomaly` events on detected spikes or cliffs

| Metric | Target |
|--------|--------|
| Forecast MAPE (30-day) | < 15% |
| Trend accuracy | ≥ 85% |
| Signal freshness | Within 1h of new batch |
| Anomaly precision | ≥ 80% |
| Trajectory confidence calibration | Within ±10% |

---

## Event Catalog

| Event | Producer | Consumers | Payload Notes |
|-------|----------|-----------|---------------|
| `IngestBatch` | Ingestion | Normalization, Orchestrator | batch_id, record_count, source |
| `NormalizationComplete` | Normalization | Work Intelligence, Orchestrator | batch_id, normalized_count, quarantine_count |
| `SkillsExtracted` | Work Intelligence | Enrichment, Orchestrator | batch_id, per-dimension counts (skills, tools, tasks, responsibilities, context), extraction_cost_usd |
| `RecordEnriched` | Enrichment | Analytics, Demand Analysis*, Orchestrator | batch_id, enriched_count, temporal_period, borderplex_subregion, duplicate_count |
| `ProfileComplete` | Work Intelligence | Enrichment | record_id — mirrors client spec naming (alias for per-record SkillsExtracted) |
| `AnalyticsRefreshed` | Analytics | Visualization, Orchestrator | refresh_id, tables_updated, records_processed |
| `DisruptionRefreshed` | Analytics | Visualization, Orchestrator | refresh_id, roles_analyzed, new_fingerprints |
| `EmergenceAlert` | Analytics | Orchestrator | cluster_id, posting_count, representative_titles — new canonical role candidates |
| `DemandSignalsUpdated` | Demand Analysis* | Analytics, Visualization, Orchestrator | *Phase 2* |
| `DemandAnomaly` | Demand Analysis* | Orchestrator | *Phase 2* |
| `RenderComplete` | Visualization | Orchestrator | page, render_time_ms |
| `*Failed` / `*Alert` | Any agent | **Orchestrator only** | error_type, severity, context |
| `SourceFailure` | Ingestion | Orchestrator | source, error, retry_count |

*Phase 2

---

## Database Schema Extensions

```sql
-- Phase 1 additions to job_postings (SQLAlchemy migration only — never touch schema.prisma)
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS source TEXT;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS ingestion_run_id TEXT;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS ai_relevance_score DOUBLE PRECISION;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS is_spam BOOLEAN;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS spam_score DOUBLE PRECISION;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS overall_confidence DOUBLE PRECISION;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS field_confidence JSONB;

-- Phase 1 additions: Enrichment expansion
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS soc_code TEXT;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS naics_code TEXT;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS temporal_period TEXT;       -- pre_chatgpt | early_genai | post_gpt4 | agentic_era
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS borderplex_subregion TEXT;  -- el_paso | las_cruces | ciudad_juarez | regional
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT FALSE;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS duplicate_cluster_id TEXT;

-- Phase 1: extracted_intelligence table (Work Intelligence Agent output)
CREATE TABLE IF NOT EXISTS extracted_intelligence (
    id SERIAL PRIMARY KEY,
    normalized_job_id INTEGER NOT NULL REFERENCES normalized_jobs(id),
    extraction_version TEXT NOT NULL,
    extracted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    extraction_model TEXT NOT NULL,
    extraction_tokens_used INTEGER NOT NULL,
    extraction_cost_usd DOUBLE PRECISION NOT NULL,
    skills JSONB NOT NULL DEFAULT '[]',
    tools JSONB NOT NULL DEFAULT '[]',
    tasks JSONB NOT NULL DEFAULT '[]',
    responsibilities JSONB NOT NULL DEFAULT '[]',
    context JSONB NOT NULL DEFAULT '[]',
    overall_confidence DOUBLE PRECISION,
    extraction_warnings JSONB DEFAULT '[]',
    extraction_failed BOOLEAN DEFAULT FALSE
);

-- Phase 1: employer_profiles table
CREATE TABLE IF NOT EXISTS employer_profiles (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    company_size TEXT,              -- startup | smb | mid_market | enterprise | unknown
    ai_maturity_signal TEXT,        -- ai_native | ai_adopting | ai_exploring | traditional | unknown
    sector TEXT,
    is_known_employer BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Phase 1: 10 aggregate tables (replacing single analytics_aggregates)
CREATE TABLE IF NOT EXISTS skill_demand_weekly (id SERIAL PRIMARY KEY, week_start DATE, skill_label TEXT, posting_count INT, growth_rate DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS tool_demand_weekly (id SERIAL PRIMARY KEY, week_start DATE, tool_label TEXT, posting_count INT, growth_rate DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS role_snapshot_weekly (id SERIAL PRIMARY KEY, week_start DATE, canonical_role_id TEXT, posting_count INT, avg_salary DOUBLE PRECISION, top_skills JSONB);
CREATE TABLE IF NOT EXISTS sector_summary_weekly (id SERIAL PRIMARY KEY, week_start DATE, sector TEXT, posting_count INT, avg_salary DOUBLE PRECISION, skill_mix JSONB);
CREATE TABLE IF NOT EXISTS geo_demand_weekly (id SERIAL PRIMARY KEY, week_start DATE, subregion TEXT, posting_count INT, top_roles JSONB);
CREATE TABLE IF NOT EXISTS skill_velocity (id SERIAL PRIMARY KEY, skill_label TEXT, week_start DATE, velocity DOUBLE PRECISION, trend TEXT);
CREATE TABLE IF NOT EXISTS skill_co_occurrence (id SERIAL PRIMARY KEY, skill_a TEXT, skill_b TEXT, co_count INT, pmi_score DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS trajectory_map (id SERIAL PRIMARY KEY, canonical_role_id TEXT, period TEXT, direction TEXT, confidence DOUBLE PRECISION, key_drivers JSONB);
CREATE TABLE IF NOT EXISTS posting_freshness (id SERIAL PRIMARY KEY, checked_at TIMESTAMP, total_postings INT, new_since_last INT, staleness_flag BOOLEAN);
CREATE TABLE IF NOT EXISTS cohort_gap_cache (id SERIAL PRIMARY KEY, cohort_key TEXT, computed_at TIMESTAMP, gap_data JSONB);

-- Phase 1: canonical_roles table
CREATE TABLE IF NOT EXISTS canonical_roles (
    id SERIAL PRIMARY KEY,
    role_id TEXT UNIQUE NOT NULL,
    label TEXT NOT NULL,
    cluster_centroid JSONB,        -- Embedding vector
    posting_count INT,
    representative_titles JSONB,
    top_skills JSONB,
    top_tools JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Phase 1: disruption_fingerprints table
CREATE TABLE IF NOT EXISTS disruption_fingerprints (
    id SERIAL PRIMARY KEY,
    canonical_role_id TEXT REFERENCES canonical_roles(role_id),
    disruption_category JSONB,     -- ["Displacement", "Augmentation", ...]
    disruption_intensity DOUBLE PRECISION,
    skill_velocity JSONB,
    tool_transition JSONB,
    task_shift JSONB,
    responsibility_expansion DOUBLE PRECISION,
    ai_intensity_trend TEXT,
    workflow_restructuring_score DOUBLE PRECISION,
    trajectory TEXT,
    period_comparison JSONB,
    computed_at TIMESTAMP DEFAULT NOW()
);

-- Phase 2 additions
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS enrichment_quality_score DOUBLE PRECISION;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS enrichment_partial BOOLEAN;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS remote_classification TEXT;
```

**Agent-managed tables:**

| Table | Phase | Owner Agent | Purpose |
|-------|-------|-------------|---------|
| `raw_ingested_jobs` | 1 | Ingestion | Ingestion staging |
| `normalized_jobs` | 1 | Normalization | Post-normalization records |
| `extracted_intelligence` | 1 | Work Intelligence | 6-dimension extraction output (JSONB per dimension) |
| `job_ingestion_runs` | 1 | Ingestion | Batch tracking |
| `employer_profiles` | 1 | Enrichment | Employer classification data |
| `alerts` | 1 | Orchestration | Active and historical alerts |
| `orchestration_audit_log` | 1 | Orchestration | All orchestration decisions |
| `llm_audit_log` | 1 | Common | All LLM calls across agents |
| `skill_demand_weekly` | 1 | Analytics | Weekly skill demand aggregates |
| `tool_demand_weekly` | 1 | Analytics | Weekly tool demand aggregates |
| `role_snapshot_weekly` | 1 | Analytics | Weekly role summaries |
| `sector_summary_weekly` | 1 | Analytics | Weekly sector summaries |
| `geo_demand_weekly` | 1 | Analytics | Weekly geographic demand |
| `skill_velocity` | 1 | Analytics | Skill demand velocity |
| `skill_co_occurrence` | 1 | Analytics | Skill pair co-occurrence |
| `trajectory_map` | 1 | Analytics | Role trajectory over time |
| `posting_freshness` | 1 | Analytics | Data recency tracking |
| `cohort_gap_cache` | 1 | Analytics | Cached gap analysis results |
| `canonical_roles` | 1 | Analytics | Discovered role clusters |
| `disruption_fingerprints` | 1 | Analytics | Per-role disruption patterns |
| `demand_signals` | 2 | Demand Analysis | Trend and forecast outputs |

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

> Variables for Student ADR tools reflect the **reference implementation**. If the team selects different technologies via their ADRs, the corresponding env vars will change (e.g., a different tracing tool replaces `LANGSMITH_API_KEY`).

<!-- Variable names must match watechcoalition/.env.example (canonical source) -->

```bash
# Tool #11 — LLM provider (reference: Azure OpenAI)
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_VERSION="2025-01-01-preview"
AZURE_OPENAI_DEPLOYMENT_NAME=
LLM_PROVIDER=azure_openai             # azure_openai | openai | anthropic

# Embeddings
AZURE_OPENAI_EMBEDDING_ENDPOINT=
AZURE_OPENAI_EMBEDDING_API_KEY=
AZURE_OPENAI_EMBEDDING_API_VERSION="2024-02-01"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=

# Architectural #19 — Database (PostgreSQL — fixed)
# POSTGRES MIGRATION: change from sqlserver:// to postgresql://
DATABASE_URL=                          # Prisma / Next.js connection string
# POSTGRES MIGRATION: change from mssql+pyodbc:// to postgresql+psycopg2://
PYTHON_DATABASE_URL=                   # SQLAlchemy connection string (Python agents)

# Tool #17 — Agent tracing (reference: LangSmith)
LANGSMITH_API_KEY=
LANGCHAIN_TRACING_V2=true

# Tool #12 — Ingestion sources (reference: httpx + Crawl4AI)
JSEARCH_API_KEY=
SCRAPING_TARGETS=                      # Comma-separated URLs

# Architectural #3 — Scheduling
INGESTION_SCHEDULE=0 2 * * *           # Cron — default: daily at 2am

# Product #8 — Spam thresholds
SPAM_FLAG_THRESHOLD=0.7
SPAM_REJECT_THRESHOLD=0.9
SKILL_CONFIDENCE_THRESHOLD=0.75
BATCH_SIZE=100

# Model tier routing (Work Intelligence Agent)
EXTRACTION_MODEL_SKILLS=claude-sonnet-4-5      # Sonnet-class for skills/responsibilities
EXTRACTION_MODEL_RESPONSIBILITIES=claude-sonnet-4-5
EXTRACTION_MODEL_TASKS=claude-haiku-4-5        # Haiku-class for tasks (cost-optimized)
EXTRACTION_TOKEN_BUDGET_PER_RECORD=4000        # Max tokens per record across all dimensions

# Cost tracking
TOKEN_COST_LOG_ENABLED=true
COST_ALERT_THRESHOLD_USD=50.0                  # Alert when cumulative cost exceeds threshold
```

---

## Build Order

| Week(s) | Deliverable |
|---------|------------|
| 1–2 | Environment, first scrape, walking skeleton (8 agent stubs, pipeline runner, journey dashboard) |
| 3 | Ingestion Agent + Normalization Agent |
| 4 | **Work Intelligence Agent Part 1:** Skills + Tools + Taxonomy + Cost Modeling |
| 5 | **Work Intelligence Agent Part 2:** Tasks + Responsibilities + Context + Enrichment-lite |
| 6 | **Enrichment Agent (Full Phase 1)** + Visualization Foundations |
| 7 | Analytics Agent — Aggregates + **Role Clustering** + Disruption Fingerprints |
| 8 | Analytics Agent — **Disruption Analysis + Workforce Intelligence Q&A** |
| 9 | **Orchestration Agent** + Visualization Completion |
| 10 | **Pipeline Hardening** + Event Contract Enforcement |
| 11 | **Testing + Security + Documentation** (merged) |
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
