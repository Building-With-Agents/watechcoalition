# Environment Setup (First-Time Clone)

This guide walks through setting up the Tech Talent Showcase app after cloning the repository. It supports **Windows**, **Linux**, and **macOS**.

## Prerequisites

- **Node.js** 18.17 or later ([nodejs.org](https://nodejs.org/) or use [nvm](https://github.com/nvm-sh/nvm))
- **Docker** (for local SQL Server) — see [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) for installation instructions
- **Git**

## 1. Clone and Install Dependencies

```bash
git clone https://github.com/Building-With-Agents/watechcoalition.git
cd watechcoalition
npm ci
```

## 2. Environment Configuration

### 2.1 Application environment (.env)

Copy the example file and fill in required values:

```bash
# All platforms
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Description |
|----------|-------------|
| `AUTH_SECRET` | Generate with `openssl rand -base64 32` |
| `DATABASE_URL` | See step 4 — you'll set this after starting SQL |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource URL |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_API_VERSION` | e.g. `2025-01-01-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Chat deployment name |
| `AZURE_OPENAI_EMBEDDING_ENDPOINT` | Same or separate Azure OpenAI endpoint |
| `AZURE_OPENAI_EMBEDDING_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_EMBEDDING_API_VERSION` | e.g. `2024-02-01` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` | Embeddings deployment name |

### 2.2 Docker SQL environment (.env.docker)

**Windows:** Run the interactive setup script (recommended):

```powershell
.\scripts\setup-env-docker.ps1
```

**Linux / macOS:** Copy the example and edit manually:

```bash
cp .env.docker.example .env.docker
```

Edit `.env.docker` and set:

- `MSSQL_SA_PASSWORD` — Strong password (min 8 chars, uppercase, lowercase, number, special char)
- `MSSQL_DATABASE` — Default: `talent_finder`
- `MSSQL_PORT` — Default: `1433`

## 3. Start SQL Server (Docker)

This project uses SQL Server `mcr.microsoft.com/mssql/server:2025-latest` in [docker-compose.yml](docker-compose.yml).
If you also run a local SQL Server instance on your machine, set `MSSQL_PORT` in `.env.docker` to a non-default host port (for example `11433`) so Prisma targets Docker, not the local instance.

**Windows:**

```powershell
.\scripts\start-sql-server.ps1
```

**Linux / macOS:**

```bash
docker compose --env-file .env.docker up -d
```

Wait for the container to be healthy. To verify:

```bash
docker ps --filter "name=mssql-server"
```

## 4. Create the database (all platforms)

**You must create the database before pushing the Prisma schema (step 5).**  
Replace `YOUR_SA_PASSWORD` with your `MSSQL_SA_PASSWORD` and `talent_finder` with your `MSSQL_DATABASE` if different.

**Windows (PowerShell):**
```powershell
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "CREATE DATABASE talent_finder"
```

**Linux / macOS:**
```bash
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "CREATE DATABASE talent_finder"
```

If the database already exists, you can skip this step.

## 5. Set DATABASE_URL in .env

After SQL Server is running and the database is created, set `DATABASE_URL` in `.env` to match your `.env.docker` values:

```env
DATABASE_URL="sqlserver://localhost:1433;database=talent_finder;user=SA;password=YOUR_SA_PASSWORD;encrypt=false;trustServerCertificate=true"
```

Replace `YOUR_SA_PASSWORD` with your `MSSQL_SA_PASSWORD` from `.env.docker`, and adjust `1433` if you changed `MSSQL_PORT`.
If Docker is mapped to `11433`, your URL must use `localhost:11433`.

## 6. Database Schema and Seed (Anonymized Fixtures)

The repo includes **pre-anonymized JSON fixtures** in `prisma/mock-data/`. Populate the database from these (no BACPAC import or anonymization step):

```bash
npx prisma db push
npx prisma generate
npm run db:seed:anonymized
```

Seeding behavior notes:

- Seed runs in dependency-safe order (parents before children) to satisfy FK constraints.
- If fixture references are orphaned, the seed script auto-repairs those FK fields to deterministic fallback parent IDs before insert.
- FK violations are not skipped at insert time; unresolved references after repair fail fast with a clear error.

Tip: if `prisma db push` errors and your machine has local SQL Server installed, verify you are connected to Docker SQL first:

```sql
SELECT @@SERVERNAME, @@VERSION;
```

`@@SERVERNAME` should be the container hostname, not your Windows host name (for example `DESKTOP-PC`).

Need to refresh fixtures from production? See [docs/REFRESH_ANONYMIZED_FIXTURES.md](docs/REFRESH_ANONYMIZED_FIXTURES.md) (maintainers only).

## 7. Optional: Azure Functions (Copilot Studio Backend)

If you need the local Python Functions endpoint for Copilot Studio:

1. Add required Azure Functions/Azurite vars to `.env` (from `.env.example` or your team-provided values)
2. Start Functions + Azurite:

**Windows:**

```powershell
.\scripts\start-functions.ps1
```

**Linux / macOS:**

```bash
docker compose -p watechcoalition -f docker-compose.functions.yml --env-file .env up -d --build
```

Test the endpoint:

**Windows (PowerShell):**

```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:7071/api/copilot" -ContentType "application/json" -Body '{"prompt":"hi"}'
```

**Linux / macOS:**

```bash
curl -X POST http://localhost:7071/api/copilot -H "Content-Type: application/json" -d '{"prompt":"hi"}'
```

## 7. Run the App

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## 8. Optional: Generate Skill Embeddings

If you need vector search (skill autocomplete), visit `/admin/dashboard/generate-embeddings` as an admin and click **Generate**.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `DATABASE_URL` connection fails | Ensure SQL container is running (`docker ps`), port matches `.env.docker`, password is correct |
| `Cannot find data type vector` during `prisma db push` | Usually means Prisma connected to the wrong SQL instance. Verify `DATABASE_URL` port and check `SELECT @@SERVERNAME, @@VERSION` |
| Password complexity error | SQL Server requires: 8+ chars, upper, lower, number, special char |
| Port already in use | Change `MSSQL_PORT` in `.env.docker` (e.g. to 11433) |
| Prisma errors after schema change | Run `npx prisma generate` |
| Docker not found | Install Docker — see [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) |

## Further Documentation

- [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) — Docker installation (Windows, macOS, Linux)
- [docs/DOCKER_SQL_SERVER_SETUP.md](docs/DOCKER_SQL_SERVER_SETUP.md) — Detailed SQL Server Docker setup (incl. optional BACPAC import)
- [docs/REFRESH_ANONYMIZED_FIXTURES.md](docs/REFRESH_ANONYMIZED_FIXTURES.md) — Maintainer workflow to refresh seed data
- [setup-MSSQL.md](setup-MSSQL.md) — Native MSSQL install (alternative to Docker)
- [prisma-workflow.md](prisma-workflow.md) — DB schema workflow
- [API-routes.md](API-routes.md) — API reference
