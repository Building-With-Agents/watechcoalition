# Set up local MSSQL using Docker (recommended)

This repo is set up to run SQL Server locally via Docker Compose (see `docker-compose.yml`).
These steps work on Windows/macOS/Linux as long as you have Docker Desktop / Docker Engine installed.

**Docker Image**: The setup uses SQL Server 2025 latest (`mcr.microsoft.com/mssql/server:2025-latest`) running in Developer Edition mode.
If you also run local SQL Server on your host, use a non-default Docker host port (for example `MSSQL_PORT=11433`) so Prisma points to Docker.

For a full step-by-step (Windows, Linux, macOS), see [ONBOARDING.md](ONBOARDING.md) and [docs/DOCKER_SQL_SERVER_SETUP.md](docs/DOCKER_SQL_SERVER_SETUP.md).

Your .env file should look similar to this:

```env
# Docker SQL Server container (used by docker-compose.yml)
# IMPORTANT: SQL Server enforces strong passwords for SA.
MSSQL_SA_PASSWORD=YourComplex!P4ssw0rd
MSSQL_PORT=1433

# App/Prisma connection info
MSSQL_USER=SA
MSSQL_PASSWORD=YourComplex!P4ssw0rd
MSSQL_HOST=localhost
MSSQL_DATABASE=WaTechDB

# Connection String for MSSQL (if using libraries that accept connection strings)
MSSQL_CONNECTION_STRING=mssql://SA:YourComplex!P4ssw0rd@localhost:1433/WaTechDB
# Root .env: Prisma/Next.js use this format
DATABASE_URL="sqlserver://localhost:1433;database=WaTechDB;user=SA;password=YourComplex!P4ssw0rd;encrypt=false;trustServerCertificate=true"

# Generate this secret by running the following command: openssl rand -base64 32
AUTH_SECRET=<your generated base64 auth secret>
```

**Python (agents pipeline):** Use `agents/.env` with `mssql+pyodbc://` format; `sqlserver://` does not work with SQLAlchemy. See [agents/README.md](agents/README.md) and [ONBOARDING.md](ONBOARDING.md) section 5.1.

```env
# In agents/.env (example)
# DATABASE_URL="mssql+pyodbc://SA:YOUR_PASSWORD@127.0.0.1:1433/WaTechDB?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
```

Don't forget to generate your Base64 Auth Secret and save!

## Start SQL Server (Docker Compose)

From the repo root:

```bash
docker compose up -d sqlserver
```

Wait until the container is healthy:

```bash
docker compose ps
```

You should see `mssql-server` with a `healthy` status.

## Create the database

**`prisma db push` does not create the database**—it only applies the schema to an existing database. Create the database first; use the same name as in your `DATABASE_URL` (e.g. `talent_finder` or `WaTechDB`). PowerShell: use single quotes for the password if it contains `!`.

```bash
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "CREATE DATABASE talent_finder"
```

Notes:
- On **PowerShell**, environment variable expansion is different. If `%MSSQL_SA_PASSWORD%` doesn’t expand for you, paste the password literally (or run via `cmd.exe`).
- If the DB already exists, you can skip this step.

## Vector support (SQL Server 2025)

The schema uses the native `vector` type for embeddings. If `prisma db push` fails with **"Cannot find data type vector"**, the database compatibility level is likely below 2025 (e.g. after a BACPAC restore). Set it to 170 (SQL Server 2025).

First, list databases to get the exact name (use single quotes for the password in PowerShell if it contains `!`):

```powershell
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "SELECT name, compatibility_level FROM sys.databases"
```

Then run (replace `YourDatabaseName` with the name from the list, e.g. `talent_finder`):

```powershell
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "ALTER DATABASE YourDatabaseName SET COMPATIBILITY_LEVEL = 170"
```

If you still get **"Cannot find data type vector"**, enable preview features for the database (required in some 2025 preview images):

```powershell
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -d talent_finder -Q "ALTER DATABASE SCOPED CONFIGURATION SET PREVIEW_FEATURES = ON"
```

If vector is still unavailable, confirm the runtime build:

```powershell
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "SELECT @@VERSION"
```

Then verify the current 2025 tags on MCR and switch tags if needed: <https://mcr.microsoft.com/v2/mssql/server/tags/list>.

Then run `npx prisma db push`.

## Set up Prisma schema + seed

Generate Prisma client and apply the schema:

```bash
npx prisma db push
npx prisma generate
```

Seed from the anonymized JSON fixtures in `prisma/mock-data/` (recommended for local dev):

To seed the database with anonymized fixtures (recommended):

```bash
npm run db:seed:anonymized
```

Alternative (generates synthetic/faker data; does NOT use `prisma/mock-data/`):

```bash
npm run seed
```
