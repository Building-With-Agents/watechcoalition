# Job Intelligence Engine (agents)

Python pipeline scaffold for the eight-agent Job Intelligence Engine. See [CLAUDE.md](../CLAUDE.md) and [agents/docs/architecture/AGENTS_SCAFFOLD.md](docs/architecture/AGENTS_SCAFFOLD.md) for the full structure.

## Python environment

- **Virtualenv:** Create and use a venv **inside `agents/`**. From the **project root** run:
  - `cd agents && python3 -m venv .venv && cd ..`
  - **Linux / macOS:** `source agents/.venv/bin/activate`
  - **Windows (PowerShell):** `.\agents\.venv\Scripts\Activate.ps1`
- Always activate the venv from the project root before running any Python commands so `python` resolves to the venv and imports like `agents.ingestion` work.
- If `python3` points to the wrong interpreter (e.g. Homebrew), run `deactivate`, remove `agents/.venv`, recreate it, and activate again.

## DATABASE_URL (Python / SQLAlchemy + pyodbc)

**Use `mssql+pyodbc://` in `agents/.env`.** The `sqlserver://` format in the root `.env` is for Prisma/Next.js only and does **not** work with SQLAlchemy.

Example in `agents/.env`:

```env
DATABASE_URL="mssql+pyodbc://SA:YOUR_SA_PASSWORD@127.0.0.1:1433/talent_finder?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
```

Use `127.0.0.1` instead of `localhost` if you see connection errors. Copy `agents/.env.example` to `agents/.env` and fill in values.

## Commands (from project root, with venv activated)

- **Connectivity test:** `python -m agents.connectivity_test` → expect `job_postings row count: <N>`
- **Streamlit dashboard:** `streamlit run agents/dashboard/streamlit_app.py`
- **Agent tests:** `cd agents && pytest tests/`

Agents use `agents/.env` and SQLAlchemy+pyodbc; Next.js uses the root `.env` and Prisma. Both can run in the same repo.
