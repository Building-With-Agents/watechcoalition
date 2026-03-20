Command to run seed_esco that will get skill records from ESCO v1.2.1 English CSV. 

These two files MUST be downloaded to run seed_esco.py script:
skills_en.csv and digitalSkillsCollection_en.csv
```
python scripts/seed_esco.py
```

**Record count:** By default the script writes the **full** ESCO digital collection to `esco_digital_skills.json` (filter is off). For a smaller Week-4-style subset, set `ESCO_SEED_APPLY_FILTER=1`; that runs `filter_records()` then **`merge_missing_genai_parent_concepts()`** so GenAI parent concepts (e.g. official `machine learning`) are not dropped.

```bash
ESCO_SEED_APPLY_FILTER=1 python scripts/seed_esco.py
```

Add this flag to upload skills into database
```
python scripts/seed_esco.py --seed-db
```

Run this command to confirm postgress table.
```
python - <<'PY'
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

load_dotenv(dotenv_path=Path(".env"))

engine = create_engine(os.getenv("PYTHON_DATABASE_URL"))

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM esco_digital_skills"))
    print("rows in db:", result.scalar())
PY
```

command to view tables
```
python - <<'PY'
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

load_dotenv(dotenv_path=Path(".env"))

db_url = os.getenv("PYTHON_DATABASE_URL")
print("db url loaded:", bool(db_url))

engine = create_engine(db_url)

with engine.connect() as conn:
    tables = conn.execute(text("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name ILIKE '%esco%'
        ORDER BY table_schema, table_name
    """)).fetchall()

    print("matching tables:")
    for row in tables:
        print(row)

    result = conn.execute(text("SELECT COUNT(*) FROM esco_digital_skills"))
    print("rows in db:", result.scalar())
PY
```

Taxonomy finished
ESCO digital skills store
- Load ESCO digital skills clusters into a queryable format

Work to do next 
ESCO digital skills store
- Support exact match, normalized match, and embedding-based similarity lookup

resolve_taxonomy()
resolve_taxonomy_batch()

---

## Partner handoff (Angel → Fabian)

Angel's completed work:

- **ESCO digital skills store:** CSVs in `agents/skills_extraction/taxonomy/` (`digitalSkillsCollection_en.csv`, `skills_en.csv`), parsed into `esco_digital_skills.json`, plus `esco_source_metadata.json`. Row count matches the seed mode (full vs `ESCO_SEED_APPLY_FILTER=1`).
- **Seed script:** `scripts/seed_esco.py` — `normalize_text()`, `build_record()`, `filter_records()`, `merge_missing_genai_parent_concepts()`, optional `--seed-db` for PostgreSQL. Optional env: `ESCO_SEED_APPLY_FILTER=1`.
- **"Taxonomy finished"** above = store is in a queryable format. The **resolver** (`resolve_taxonomy` / `resolve_taxonomy_batch`) was still stub; that's what we build next.

---

## Fabian's scope (Week 4)

- GenAI Extension Layer: 10 skills → ESCO parent cluster (config + step 1 resolution).
- ESCO store loader: in-memory from JSON (and optional DB when `--seed-db` used).
- Resolver: 6-step order (1 GenAI exact → 2 ESCO exact → 3 ESCO normalized → 4 embedding ≥ threshold → 5 O*NET stub → 6 raw_skill).
- `resolve_taxonomy_batch()`: dedupe labels, shared embedding computation, same-order results.
- Resolution statistics: per-step counts for taxonomy coverage (target ≥ 95%).
- Optional: posting selection for ground truth (30–50 for human labeling).
- Eval harness (basic): document coverage formula and commands; checklist below.

---

## Resolver implementation (Fabian)

- **GenAI Extension Layer:** `agents/skills_extraction/taxonomy/genai_extension.json` — 10 skills → ESCO parent cluster label. Step 1 resolves by normalized exact match on the skill name; parent label → URI uses `_build_parent_label_to_uri`: **`broader_concept_labels`/`broader_concept_uris` first**, then any **unfilled key** from each record’s **`preferred_label` → `esco_uri`** (so parents like “Machine learning” resolve to the official ESCO concept), then **`_PARENT_LABEL_ALIASES`** where names still differ from ESCO strings.
- **ESCO store:** Loaded from `agents/skills_extraction/taxonomy/esco_digital_skills.json` (in-memory). Steps 2 (exact) and 3 (normalized) use `preferred_label`, `alt_labels`, `hidden_labels` and their normalized variants.
- **Step 4 (embedding):** Azure OpenAI Embeddings API (text-embedding-3-small). No local model — HTTP calls via `AZURE_OPENAI_EMBEDDING_*` env vars. ESCO texts are sent in chunks of 100 to respect API payload limits; cache is built once and reused. Threshold via `SKILL_TAXONOMY_SIMILARITY_THRESHOLD` (default `0.92`). If the API is unavailable, step 4 is skipped and labels fall through to step 5/6; cosine similarity is computed with NumPy on the returned vectors.
- **Step 5 (O*NET):** O*NET skill match: load from `taxonomy/onet_skills.txt` (tab-delimited, O*NET 25.0 Skills). Normalized name lookup; returns `urn:onet:skill:{Element ID}` and Element Name. File optional: if missing, step 5 is skipped.
- **Batch:** `resolve_taxonomy_batch(labels)` deduplicates by exact label, runs Steps 1–3 for all unique labels, then **one batched** embedding request (chunked by 100) for labels that need Step 4, then Step 5 (O*NET) for any still unresolved, then Step 6. Results are returned in the same order as input. No N+1 API calls.
- **Resolution stats:** `resolution_stats(results)` returns `{1: n1, 2: n2, ...}` (counts per step). Taxonomy coverage = (steps 1–5 total) / len(results); target ≥ 95%. **`resolution_report(results)`** adds `taxonomy_coverage`, `genai_extension_matches`, `raw_skill_fallback`, and `avg_resolution_confidence` (steps 1–5 only).

### Commands (resolver)

Run from **repo root** with venv activated (no need to `cd agents`):

```bash
# Run all taxonomy resolver tests (recommended: from repo root)
# Tests mock _embed_texts_azure via pytest monkeypatch — no live Azure API calls.
pytest agents/tests/test_taxonomy_resolver.py -v
```

Other resolver commands (from repo root with venv activated and `PYTHONPATH=.` or from `agents/`):

```bash
# Resolve a single label
python -c "
from agents.skills_extraction.extractors.taxonomy import resolve_taxonomy
r = resolve_taxonomy('Prompt Engineering')
print('Step', r.resolution_step, 'uri', r.esco_uri, 'genai', r.is_genai_extension)
"

# Resolve a batch and print resolution stats
# NOTE: Make sure your Azure API keys are in your .env file before running this, 
# If env vars do not load look for the test command below, under step 5
# as unresolved skills will trigger live network calls to Step 4!
python -c "
from agents.skills_extraction.extractors.taxonomy import resolve_taxonomy_batch, resolution_stats
labels = ['Python', 'ABAP', 'Prompt Engineering', 'machine learning', 'Unknown Skill XYZ']
results = resolve_taxonomy_batch(labels)
stats = resolution_stats(results)
total = sum(stats.values())
resolved_1_5 = total - stats.get(6, 0)
coverage = (resolved_1_5 / total * 100) if total else 0
print('Step counts:', stats)
print('Taxonomy coverage:', round(coverage, 1), '%')
"
```

**Step 4 — Azure OpenAI Embeddings:** Step 4 calls the Azure OpenAI Embeddings API (text-embedding-3-small). Set these in `.env` (see `.env.example`):

If any of these are missing or the API request fails, step 4 is skipped and labels fall through to step 5/6 (no local model or PyTorch).

**O*NET data (Step 5):** Download the [O*NET 25.0 Skills](https://www.onetcenter.org/dl_files/database/db_25_0_text/Skills.txt) tab-delimited file and save it as `agents/skills_extraction/taxonomy/onet_skills.txt`. If the file is missing, step 5 is skipped (no-op). No env vars required.

Optional env for step 4 threshold:

```bash
export SKILL_TAXONOMY_SIMILARITY_THRESHOLD=0.92
```

### Two levels of testing

- **pytest (logic test):** `pytest agents/tests/test_taxonomy_resolver.py -v` mocks the embedding API via monkeypatch. Use this in CI or when you don’t have Azure keys — it checks that the resolver logic and fallbacks are correct without live calls.
- **CLI with `.env` (integration test):** The script below loads `.env` and calls the real Azure Embeddings API. It confirms endpoint, key, and connectivity. If the API returns 429 or fails, the resolver falls back to Step 5 (O*NET) or Step 6 (raw_skill) instead of crashing; seeing step counts like `{1: 0, 2: 2, 3: 0, 4: 0, 5: 1, 6: 3}` even when Step 4 fails is expected and shows defensive behavior.

### API integration test script (for Angel)

Run from **repo root** with venv activated and `.env` containing the `AZURE_OPENAI_EMBEDDING_*` variables. This hits the real Azure API; if you get 429 or timeouts, the resolver still completes and falls back to O*NET/raw_skill.

```bash
python -c "
from dotenv import load_dotenv
load_dotenv()

from agents.skills_extraction.extractors.taxonomy import resolve_taxonomy_batch, resolution_stats
labels = ['Python', 'ABAP', 'Prompt Engineering', 'machine learning', 'Reading Comprehension', 'Unknown Skill XYZ']
results = resolve_taxonomy_batch(labels)
print(resolution_stats(results))
"
```

Expected: a dict like `{1: 0, 2: 2, 3: 0, 4: 0, 5: 1, 6: 3}` (exact counts depend on API success). If you see `embedding_api_failed` or `embedding_init_failed` in the logs, Step 4 was skipped and the rest of the pipeline still ran.

**Handoff note (for Gary / Angel):** If you hit 429 during ESCO cache init, the batch still completes via Step 5/6 fallback. For a full production run, consider raising TPM/RPM on the Azure embedding deployment. The O*NET file is in `agents/skills_extraction/taxonomy/onet_skills.txt` and is ready for Step 5 refinements.

---

## Posting selection for ground truth

Criteria: select 30–50 postings that span roles and skill mix for human labeling (for eval harness precision/recall).

Script (optional):

```bash
python -m agents.skills_extraction.scripts.select_ground_truth_postings --limit 40
```

Output: one `posting_id` per line. Use `--fixture` to point at another JSON array; `--id-key` if the ID field has a different name.

---

## Eval harness — taxonomy coverage

- **Formula:** Taxonomy coverage = (number of skills resolved in steps 1–5) / (total skills resolved). Target ≥ 95%.
- **How to compute:** Run `resolve_taxonomy_batch(all_skill_labels)` on the eval set, then `resolution_stats(results)`. Coverage = `(total - stats[6]) / total`.
- **Per-step diagnostics:** Step 1 hit rate = GenAI prevalence; ratio of step 3 vs 4 = normalization vs embedding; step 6 rate = unmapped (aim < 5%).

---

## Checklist (Fabian's scope)

- [x] GenAI Extension Layer config (`genai_extension.json`) and step 1 resolution
- [x] ESCO store loader (JSON, in-memory)
- [x] Step 2 (exact) and step 3 (normalized) in `resolve_taxonomy()`
- [x] Step 4 (embedding similarity, threshold from env)
- [x] Step 5 (O*NET) — load from onet_skills.txt, normalized name lookup
- [x] `resolve_taxonomy_batch()` with dedupe and same-order results
- [x] `resolution_stats()` for per-step counts and coverage
- [x] `resolution_report()` for coverage + GenAI count + avg confidence (steps 1–5)
- [x] Posting selection script (optional)
- [x] Eval harness notes and commands in this .md

---

Once the ground-truth set exists, we can run the full eval (coverage + precision/recall) off a single, well-defined dataset.

Made small ground truth set in agents/eval/extraction_ground_truth.json

Wrote small agents/eval/extraction_eval.py to start evaluation of ground truth.

---

## Appendix A — Week-04 runbook reconciliation (2026-03-19)

This section **appends** to the doc above; it does not replace Angel’s seed commands or the resolver notes. Treat the short block under **“Taxonomy finished” / “Work to do next”** (early in this file) as **historical**: the resolver is implemented in `agents/skills_extraction/extractors/taxonomy.py`; the checklist further down remains the live status.

### Runbook requirement → implementation

| Runbook item | Status | Where / notes |
|--------------|--------|----------------|
| ESCO digital skills store (queryable) | Done | `taxonomy/esco_digital_skills.json` (+ seed via `scripts/seed_esco.py`) |
| GenAI Extension — 10 skills, parent cluster URI | Done | `taxonomy/genai_extension.json`; Step 1 maps parents via `_build_parent_label_to_uri` (`broader_concept_*`, then `preferred_label` fill-ins, then `_PARENT_LABEL_ALIASES`) |
| 6-step order (GenAI before ESCO) | Done | `resolve_taxonomy()`; GenAI always wins if the label matches a canonical GenAI name (normalized) |
| Exact / normalized ESCO match | Done | Steps 2–3 |
| Embedding cosine ≥ threshold (default 0.92) | Done | Step 4; `SKILL_TAXONOMY_SIMILARITY_THRESHOLD`; Azure embeddings env vars |
| O*NET match | Done | Step 5: normalized **skill name** → `urn:onet:skill:{Element ID}` (see “Interpretation gaps” below) |
| raw_skill fallback | Done | Step 6: `esco_uri=None`, `confidence=0` |
| `resolve_taxonomy_batch` + shared embeddings | Done | Dedupes labels; one batched embed call per chunk for Step 4; ESCO matrix built once |
| Per-step hit rates | Done | `resolution_stats(results)` → `{1:…6:…}` |
| Avg confidence, GenAI count, coverage | Done | `resolution_report(results)` → `taxonomy_coverage`, `genai_extension_matches`, `raw_skill_fallback`, `avg_resolution_confidence`, `counts_by_step` |

**GenAI parent labels vs ESCO wording:** Some parents match an ESCO concept’s own `preferred_label` (e.g. “Machine learning” → URI of the official `machine learning` knowledge node). `_build_parent_label_to_uri` indexes those in addition to `broader_concept_labels`. Where the runbook name still differs from any label in the JSON (e.g. “Information retrieval”), `_PARENT_LABEL_ALIASES` maps to an ESCO string that exists. If you add GenAI skills or change parents, update `genai_extension.json` and aliases as needed. When using `ESCO_SEED_APPLY_FILTER=1` with `scripts/seed_esco.py`, `merge_missing_genai_parent_concepts` re-adds filtered-out parent concepts by `preferred_label`.

### Interpretation gaps (runbook text vs code)

1. **Step 3 “stemmed”:** Implementation uses NFKC, lowercase, collapsed whitespace (`_normalize_label`) — **no Porter/word stemming**. If eval shows systematic misses (e.g. “programming” vs “program”), consider a follow-up: optional stemmer or synonym table (document in `prompt_iteration_log.md` if you change behavior).

2. **Step 5 “O*NET occupation code”:** The resolver only sees a **skill label string**, not a job’s O*NET/SOC occupation code. Step 5 is implemented as **O*NET Skills** tab file: normalized **Element Name** → synthetic URI `urn:onet:skill:{Element ID}`. True occupation-code routing would require passing SOC code into the resolver (future integration).

3. **GenAI vs ESCO collision:** If a label matched both (same string), **Step 1 (GenAI) wins**; output has `is_genai_extension=True` and `esco_uri` = **parent cluster** URI, not the leaf ESCO skill.

### Commands (`resolution_report`)

```bash
pytest agents/tests/test_taxonomy_resolver.py -v
```

```python
from agents.skills_extraction.extractors.taxonomy import (
    resolve_taxonomy_batch,
    resolution_report,
)

labels = [...]  # e.g. from Pair C extraction output
results = resolve_taxonomy_batch(labels)
print(resolution_report(results))
```

### Exercise 4.5 — remaining checklist (process, not code)

- [ ] Run taxonomy coverage on **real** extracted skills from Pair C output; target ≥ 95% resolved (steps 1–5).
- [ ] Sweep `SKILL_TAXONOMY_SIMILARITY_THRESHOLD` (e.g. 0.92 vs 0.85); record precision/coverage tradeoff in `agents/eval/prompt_iteration_log.md`.
- [ ] Confirm end-to-end: `extract_skills` → `resolve_taxonomy_batch` → `SkillRecord.esco_uri` / `is_genai_extension` (`agents/skills_extraction/extractors/skills.py`).
- [ ] Coordinate interface with Pair C (label field, batching expectations).

### Reference paths (repo)

- `agents/skills_extraction/extractors/taxonomy.py` — resolver, stats, report
- `agents/skills_extraction/taxonomy/genai_extension.json` — 10 GenAI skills
- `agents/common/types/extraction_types.py` — `TaxonomyResult`, `SkillRecord`
- `docs/planning/ARCHITECTURE_DEEP.md`, `docs/planning/ARCHITECTURAL_DECISIONS.md` — Decision #36, six-step order
- `agents/eval/prompt_iteration_log.md` — Exercise 4.5 metrics log
- `agents/eval/extraction_ground_truth.json` — golden hand-labeled set (growing); use with `extraction_eval.py` when the harness is wired for precision/recall
- `scripts/seed_esco.py` — ESCO JSON/DB seed; `ESCO_SEED_APPLY_FILTER` + GenAI parent merge

---

## Handoff readiness (taxonomy + seed)

- **Live implementation** is summarized in **Appendix A** and the **Checklist** above; treat the first ~75 lines as **historical** setup notes unless you are re-seeding from CSV.
- **Verify before merge:** `pytest agents/tests/test_taxonomy_resolver.py -v` from repo root (mocks embeddings; no Azure required).
- **Next owner (Exercise 4.5 / Pair C):** taxonomy coverage on real extractions, threshold sweep, log in `prompt_iteration_log.md`; ground truth in `extraction_ground_truth.json`.