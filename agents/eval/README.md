# Extraction eval (skills + tools vs ground truth)

## Legacy CLI (stub only, lightweight)

No `agents.skills_extraction` import chain — safe for environments without full agent deps beyond JSON + core helpers:

```bash
python -m agents.eval.extraction_eval
```

Uses `extraction_ground_truth.json` next to this README.

## New CLI (stub or full pipeline)

Writes **JSON snapshots** under `agents/eval/runs/` and **Markdown prompt backlog** under `agents/eval/prompt_backlog/` (Mountain Time, `America/Denver`). Does **not** modify `prompt_iteration_log.md`.

```bash
python -m agents.eval.run_extraction_eval --mode stub --label baseline
python -m agents.eval.run_extraction_eval --mode pipeline --label llm-sample --limit 5
python -m agents.eval.run_extraction_eval --mode stub --no-artifacts
```

- **stub** — keyword heuristic (parity with legacy metrics).
- **pipeline** — Pass 1 tools (`extract_tools`) + Pass 2 LLM skills (`extract_skills`); requires Azure/OpenAI env vars (see `agents/common/llm_client.py` and `EXTRACTION_*`).

## Streamlit comparison UI (separate from pipeline dashboard)

```bash
streamlit run agents/eval/streamlit_eval_app.py
```

Compare ground truth (path field) against **one** or **two** runs. Each run can be **Run now** (stub/pipeline) or **Load snapshot** (saved JSON or upload). Two-run layout shows aggregate **deltas**.

## Artifacts

| Path | Purpose |
|------|---------|
| `runs/*.json` | Machine-readable `ExtractionEvalSnapshot` |
| `prompt_backlog/*.md` | Human-readable run + metrics + prompt exemplar for pasting into `prompt_iteration_log.md` |

Copy backlog sections into [`prompt_iteration_log.md`](prompt_iteration_log.md) manually when iterating prompts.

## Optional gitignore

Teams may add `runs/*.json` and `prompt_backlog/*.md` to a local ignore file if they do not want commits; defaults in-repo keep `.gitkeep` / README only under those dirs.
