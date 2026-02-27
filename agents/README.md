# Job Intelligence Engine — Agents

Python 3.11+ agent pipeline. Install and run from the **repository root** (parent of `agents/`).

## Install dependencies

If `pip` is not on your PATH, use the module form:

```bash
# From repo root
cd agents
python3 -m pip install -r requirements.txt
```

Or from anywhere (path to agents folder):

```bash
python3 -m pip install -r agents/requirements.txt
```

## Run tests

```bash
# From repo root (so the agents package is importable)
cd agents && python3 -m pytest . -v
# Or with PYTHONPATH from repo root:
PYTHONPATH=. python3 -m pytest agents/ -v
```

## Run dashboard

```bash
streamlit run agents/dashboard/streamlit_app.py
```

## Run pipeline (when implemented)

```bash
python3 -m agents.orchestration.scheduler
```
