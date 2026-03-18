Command to run seed_esco that will get skill records from ESCO v1.2.1 English CSV skills_en.csv and digitalSkillsCollection_en.csv
```
python scripts/seed_esco.py
```
- Skills extracted is originally 1284 but are filtered down to 390 using a seed_esco.filter_records(..) for week 4

Add this flag to uplaod skills into database
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

- **ESCO digital skills store:** CSVs in `agents/skills_extraction/taxonomy/` (`digitalSkillsCollection_en.csv`, `skills_en.csv`), parsed into `esco_digital_skills.json` (390 records after `filter_records()`), plus `esco_source_metadata.json`.
- **Seed script:** `scripts/seed_esco.py` — `normalize_text()`, `build_record()`, `filter_records()`, optional `--seed-db` for PostgreSQL. Commands above are the source of truth for running it.
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

- **GenAI Extension Layer:** `agents/skills_extraction/taxonomy/genai_extension.json` — 10 skills → ESCO parent cluster label. Step 1 resolves by normalized exact match; parent label → URI is resolved from the ESCO store's `broader_concept_labels`/`broader_concept_uris`.
- **ESCO store:** Loaded from `agents/skills_extraction/taxonomy/esco_digital_skills.json` (in-memory). Steps 2 (exact) and 3 (normalized) use `preferred_label`, `alt_labels`, `hidden_labels` and their normalized variants.
- **Step 4 (embedding):** Azure OpenAI Embeddings API (text-embedding-3-small). No local model — HTTP calls via `AZURE_OPENAI_EMBEDDING_*` env vars. ESCO texts are sent in chunks of 100 to respect API payload limits; cache is built once and reused. Threshold via `SKILL_TAXONOMY_SIMILARITY_THRESHOLD` (default `0.92`). If the API is unavailable, step 4 is skipped and labels fall through to step 5/6; cosine similarity is computed with NumPy on the returned vectors.
- **Step 5 (O*NET):** O*NET skill match: load from `taxonomy/onet_skills.txt` (tab-delimited, O*NET 25.0 Skills). Normalized name lookup; returns `urn:onet:skill:{Element ID}` and Element Name. File optional: if missing, step 5 is skipped.
- **Batch:** `resolve_taxonomy_batch(labels)` deduplicates by exact label, runs Steps 1–3 for all unique labels, then **one batched** embedding request (chunked by 100) for labels that need Step 4, then Step 5 (O*NET) for any still unresolved, then Step 6. Results are returned in the same order as input. No N+1 API calls.
- **Resolution stats:** `resolution_stats(results)` returns `{1: n1, 2: n2, ...}` (counts per step). Taxonomy coverage = (steps 1–5 total) / len(results); target ≥ 95%.

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

- `AZURE_OPENAI_EMBEDDING_ENDPOINT` — e.g. `https://resumejobmatch.openai.azure.com/`
- `AZURE_OPENAI_EMBEDDING_API_KEY` — API key (provided by Gary)
- `AZURE_OPENAI_EMBEDDING_API_VERSION` — e.g. `2024-02-01`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` — e.g. `embeddings-te3small`

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
- [x] Posting selection script (optional)
- [x] Eval harness notes and commands in this .md

---

## Next steps for Angel

**20–30 hand-verified job postings**  
Create a small ground-truth set so the eval harness has something concrete to measure against:
- Use the posting-selection script (or any 20–30 real postings that span roles and skills).
- For each posting, hand-verify which extracted skills map to which ESCO (or O\*NET) codes/labels.
- Store these as the "expected" outcomes; the harness can then compute precision/recall and step-wise accuracy against this set.

Once the ground-truth set exists, we can run the full eval (coverage + precision/recall) off a single, well-defined dataset.

Made small ground truth set in agents/eval/extraction_ground_truth.json

Wrote small agents/eval/extraction_eval.py to start evaluation of ground truth.