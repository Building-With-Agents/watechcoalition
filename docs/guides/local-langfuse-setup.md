# Local Langfuse Setup Guide

Self-hosted Langfuse v3 for LLM observability, trace inspection, and dataset annotation.

## Prerequisites

- Docker Desktop running
- Python venv activated with `pip install -r agents/requirements.txt` (includes `langfuse>=2.0`)
- Local PostgreSQL Docker container running (for agent pipeline data)

## 1. Start Langfuse Docker Services

```bash
docker compose up langfuse-db langfuse-clickhouse langfuse-minio langfuse-redis langfuse-worker langfuse -d
```

This starts 6 containers:
- `langfuse-db` (postgres:16-alpine on port 5433) -- metadata store
- `langfuse-clickhouse` (clickhouse-server) -- trace storage
- `langfuse-minio` (minio) -- blob storage for events
- `langfuse-redis` (redis:7-alpine) -- queue for worker
- `langfuse-worker` (langfuse-worker:3) -- background processing
- `langfuse-server` (langfuse:3 on port 3000) -- web UI and API

Wait ~30 seconds for all services to initialize.

## 2. First-Time Account Setup

The docker-compose auto-provisions:
- **Organization**: Computing For All
- **Project**: job-intelligence-engine
- **User**: glarson@localhost.dev / LocalDev123!
- **API Keys**: `sk-lf-local-dev-secret` / `pk-lf-local-dev-public`

Sign in at http://localhost:3000 with the credentials above.

## 3. Configure .env

The `.env` file should already have the local Langfuse keys:

```bash
LANGFUSE_SECRET_KEY=sk-lf-local-dev-secret
LANGFUSE_PUBLIC_KEY=pk-lf-local-dev-public
LANGFUSE_BASE_URL=http://localhost:3000
LANGFUSE_HOST=http://localhost:3000
```

To switch to cloud Langfuse, uncomment the cloud keys and comment out the local ones.

## 4. Choose LLM Provider

For mock mode (no API calls, uses ground truth data):
```bash
LLM_PROVIDER=mock
```

For real Azure OpenAI:
```bash
LLM_PROVIDER=azure_openai
```

## 5. Seed the Database (if needed)

If your local PostgreSQL is empty, seed it:

```bash
python scripts/pg-seed-data/seed_agent_data.py
```

## 6. Run the Pipeline with Mock Traces

```bash
python agents/scripts/run_processing_loop.py --max-iterations 2 --batch-size 5
```

This will:
- Process pending raw records through Normalization, Skills Extraction, and Enrichment
- Generate Langfuse traces for each LLM call (mocked from ground truth data)
- Log taxonomy resolution metrics, enrichment counts, and normalization quality

## 7. View Traces in Langfuse

Open http://localhost:3000 and navigate to **Tracing**. You should see:

- `processing-loop/skills-extraction` -- skills extraction LLM calls
- `processing-loop/tasks-extraction` -- task extraction LLM calls
- `processing-loop/responsibilities-extraction` -- responsibility extraction LLM calls
- `processing-loop/normalization` -- normalization agent spans

Each trace includes:
- **Input**: the prompt sent to the LLM
- **Output**: the extracted JSON response
- **Token counts**: simulated input/output tokens
- **Cost**: simulated USD cost

## 8. Upload Ground Truth Dataset

Upload the 30 labeled ground truth records as a Langfuse dataset:

```bash
python agents/scripts/upload_langfuse_dataset.py
```

View the dataset in Langfuse UI under **Datasets > extraction-ground-truth-v1**.

### Round-Trip Export

To export changes made in Langfuse back to JSON:

```bash
python agents/scripts/export_langfuse_dataset.py
```

## 9. Switching Between Mock and Real LLM

Toggle `LLM_PROVIDER` in `.env`:

| Mode | Value | API Calls | Cost |
|------|-------|-----------|------|
| Mock | `mock` | None | Free |
| Azure OpenAI | `azure_openai` | Real | Per-token pricing |
| Anthropic | `anthropic` | Real | Per-token pricing |

## Troubleshooting

### Port 3000 in use
The Next.js app also uses port 3000. Set `LANGFUSE_PORT=3001` in `.env` and update `LANGFUSE_BASE_URL` accordingly.

### Langfuse not starting
Check logs: `docker compose logs langfuse` and `docker compose logs langfuse-worker`

### No traces appearing
- Verify `LANGFUSE_SECRET_KEY` and `LANGFUSE_PUBLIC_KEY` match the auto-provisioned keys
- Verify `LANGFUSE_BASE_URL` points to `http://localhost:3000`
- Check that the pipeline script ran without errors

### Reset Langfuse data
```bash
docker compose down langfuse langfuse-worker langfuse-db langfuse-clickhouse langfuse-minio langfuse-redis
docker volume rm watechcoalition_langfuse_db_data watechcoalition_langfuse_clickhouse_data watechcoalition_langfuse_clickhouse_logs watechcoalition_langfuse_minio_data
docker compose up langfuse-db langfuse-clickhouse langfuse-minio langfuse-redis langfuse-worker langfuse -d
```
