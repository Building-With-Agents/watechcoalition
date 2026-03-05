# PostgreSQL Docker Setup Guide

This guide explains how to set up PostgreSQL with pgvector in a Docker container for the watechcoalition platform. Use [ONBOARDING.md](../ONBOARDING.md) for the full environment setup; after the container is running, seed the database with `python scripts/pg-seed-data/seed_pg_database.py`.

> **PostgreSQL is the primary database** for all development. The Python agent pipeline uses it exclusively via SQLAlchemy + psycopg2, with pgvector for embedding similarity search.

## Prerequisites

- Docker Desktop installed and running — see [docs/INSTALL_DOCKER.md](INSTALL_DOCKER.md)

## Quick Start

1. **Configure Environment Variables**
   - Copy `.env.docker.example` to `.env.docker`
   - Edit `.env.docker` and set your PostgreSQL values:
     - `POSTGRES_USER` — Superuser name (default: `postgres`)
     - `POSTGRES_PASSWORD` — Strong password
     - `POSTGRES_DB` — Database name (default: `talent_finder`)
     - `POSTGRES_PORT` — Port mapping (default: `5432`)

2. **Start PostgreSQL Container**

   **All platforms:**
   ```bash
   docker compose --env-file .env.docker up postgres -d
   ```

   Wait for the container to be healthy:
   ```bash
   docker ps --filter "name=postgres-server"
   ```

   You should see `(healthy)` in the STATUS column.

3. **Seed the Database**

   ```bash
   # Activate Python venv (see ONBOARDING.md section 7 if not set up yet)
   agents\.venv\Scripts\Activate.ps1          # Windows PowerShell
   # source agents/.venv/bin/activate         # macOS / Linux

   # Install dependencies (if not done yet)
   pip install -r agents/requirements.txt

   # Seed PostgreSQL (~56,000 rows across 40 tables)
   python scripts/pg-seed-data/seed_pg_database.py
   ```

   See [scripts/pg-seed-data/README.md](../scripts/pg-seed-data/README.md) for details.

## Detailed Steps

### Step 1: Environment Configuration

Create a `.env.docker` file in the repository root with the following PostgreSQL variables:

```env
# PostgreSQL Docker Configuration (Python agent pipeline)

# PostgreSQL superuser name (default: postgres)
POSTGRES_USER=postgres

# PostgreSQL password — use a strong password
POSTGRES_PASSWORD=YourPostgresP4ssw0rd

# Database name (default: talent_finder)
POSTGRES_DB=talent_finder

# Port mapping for PostgreSQL (default: 5432)
POSTGRES_PORT=5432
```

**Note:** PostgreSQL password requirements are simpler than SQL Server — any non-empty string works, but use a strong password for good practice.

### Step 2: Start the Container

```bash
docker compose --env-file .env.docker up postgres -d
```

This starts the PostgreSQL container in the background. The pgvector extension is automatically enabled on first container creation via the init script in `scripts/postgres-init/01-enable-pgvector.sql`.

### Step 3: Verify PostgreSQL is Running

```bash
docker ps --filter "name=postgres-server"
```

You should see the container with status `(healthy)`. You can also connect directly:

```bash
docker exec -it postgres-server psql -U postgres -d talent_finder -c "SELECT version();"
```

Or use pgAdmin, DBeaver, or any PostgreSQL client.

## Connection Strings

After setup, set `PYTHON_DATABASE_URL` in your `.env` file:

```env
PYTHON_DATABASE_URL=postgresql+psycopg2://postgres:YourPostgresP4ssw0rd@localhost:5432/talent_finder
```

- Replace `YourPostgresP4ssw0rd` with your `POSTGRES_PASSWORD` from `.env.docker`
- Replace `5432` with your `POSTGRES_PORT` if you changed it
- Replace `talent_finder` with your `POSTGRES_DB` if you changed it

> **Note:** `DATABASE_URL` (Prisma's `sqlserver://` format) is a separate variable used only by the Next.js app. Python agents use `PYTHON_DATABASE_URL` exclusively.

## Docker Compose Configuration

The `docker-compose.yml` includes the following PostgreSQL service:

- **Image:** `pgvector/pgvector:pg16` (PostgreSQL 16 with pgvector extension)
- **Container name:** `postgres-server`
- **Port:** Mapped from container 5432 to host (configurable via `POSTGRES_PORT`)
- **Volumes:**
  - `postgres_data` — Persistent storage for database files
  - `scripts/postgres-init/` — Init scripts (pgvector extension setup)
- **Health Check:** `pg_isready` — verifies PostgreSQL is accepting connections
- **Restart Policy:** `unless-stopped`

## pgvector Extension

The [pgvector](https://github.com/pgvector/pgvector) extension is required for:
- Skill taxonomy matching (cosine similarity >= 0.92 in Skills Extraction Agent)
- Near-dedup work (Week 9)

It is **automatically enabled** on first container creation via `scripts/postgres-init/01-enable-pgvector.sql`. You can verify:

```bash
docker exec postgres-server psql -U postgres -d talent_finder -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Container won't start | Check Docker is running: `docker ps`. Check logs: `docker logs postgres-server` |
| `PYTHON_DATABASE_URL` connection fails | Ensure container is running (`docker ps --filter "name=postgres-server"`), port matches `.env.docker`, password is correct |
| `ERROR: Set PYTHON_DATABASE_URL` | Add `PYTHON_DATABASE_URL=postgresql+psycopg2://postgres:YourPassword@localhost:5432/talent_finder` to your `.env` file |
| `Waiting for PostgreSQL...` loops forever | Ensure the postgres container is running: `docker compose --env-file .env.docker up postgres -d` |
| `ERROR executing schema DDL` | The database may have conflicting objects. Try: `docker compose --env-file .env.docker down -v` then start fresh |
| Port 5432 already in use | Change `POSTGRES_PORT` in `.env.docker` (e.g., to `15432`) and update `PYTHON_DATABASE_URL` accordingly |
| pgvector extension missing | Check init script ran: `docker logs postgres-server 2>&1 \| grep vector`. If not, recreate container: `docker compose --env-file .env.docker down -v && docker compose --env-file .env.docker up postgres -d` |

### Verify Port Is Not in Use

**Windows:**
```powershell
netstat -an | findstr :5432
```

**Linux / macOS:**
```bash
lsof -i :5432
# or: ss -tlnp | grep 5432
```

### Check Container Health

```bash
docker inspect postgres-server --format='{{.State.Health.Status}}'
```

## Data Persistence

Database data is stored in a Docker volume named `postgres_data`. This means:

- Data persists across container restarts
- Data persists even if the container is removed (unless you use `docker compose down -v`)
- To start fresh, remove the volume:

  ```bash
  docker compose --env-file .env.docker down -v
  docker compose --env-file .env.docker up postgres -d
  python scripts/pg-seed-data/seed_pg_database.py
  ```

## Stopping and Cleaning Up

**Stop the container:**
```bash
docker compose --env-file .env.docker stop postgres
```

**Stop and remove container:**
```bash
docker compose --env-file .env.docker down postgres
```

**Stop and remove container + volumes (deletes database):**
```bash
docker compose --env-file .env.docker down -v
```

## Security Notes

- The `.env.docker` file contains credentials — do not commit it to version control (it is in `.gitignore`)
- Use strong, unique passwords
- The PostgreSQL container is for local development only — do not expose to the internet
- Consider using Docker secrets for production deployments
