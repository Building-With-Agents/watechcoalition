# Set up local MSSQL using Docker (recommended)

This repo is set up to run SQL Server locally via Docker Compose (see `docker-compose.yml`).
These steps work on Windows/macOS/Linux as long as you have Docker Desktop / Docker Engine installed.

**Docker Image**: The setup uses the official Microsoft SQL Server 2025 Docker image (`mcr.microsoft.com/mssql/server:2025-latest`) running in Developer Edition mode. This provides a full-featured SQL Server instance suitable for local development.

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
DATABASE_URL="sqlserver://localhost:1433;database=WaTechDB;user=SA;password=YourComplex!P4ssw0rd;encrypt=false;trustServerCertificate=true"

# Generate this secret by running the following command: openssl rand -base64 32
AUTH_SECRET=<your generated base64 auth secret>
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

## Create the database (WaTechDB)

Create the DB inside the container:

```bash
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "%MSSQL_SA_PASSWORD%" -C -Q "CREATE DATABASE WaTechDB"
```

Notes:
- On **PowerShell**, environment variable expansion is different. If `%MSSQL_SA_PASSWORD%` doesn’t expand for you, paste the password literally (or run via `cmd.exe`).
- If the DB already exists, you can skip this step.

## Set up Prisma schema + seed

Generate Prisma client and apply the schema:

```bash
npx prisma generate
npx prisma db push
```

Seed from the anonymized JSON fixtures in `prisma/mock-data/` (recommended for local dev):

```bash
npm run db:seed:anonymized
```

Alternative (generates synthetic/faker data; does NOT use `prisma/mock-data/`):

```bash
npm run seed
```
