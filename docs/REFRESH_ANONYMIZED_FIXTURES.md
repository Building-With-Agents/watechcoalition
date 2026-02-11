# Refreshing Anonymized Fixtures (Maintainers Only)

This workflow is for **maintainers** who need to update the pre-anonymized JSON fixtures in `prisma/mock-data/` from production data. New developers should **not** run this—they use the existing fixtures via `npm run db:seed:anonymized`.

## Overview

1. Import production BACPAC into local Docker MSSQL
2. Anonymize PII in the database
3. Export anonymized data to `prisma/mock-data/`
4. Review and commit the updated fixtures

## Prerequisites

- Docker running (SQL Server container)
- `.env.docker` and `.env.local` configured
- SqlPackage.exe (for BACPAC import) — see [DOCKER_SQL_SERVER_SETUP.md](DOCKER_SQL_SERVER_SETUP.md)
- Access to `prod-backup-20251117.bacpac` (or equivalent production backup)

## Step 1: Import BACPAC

Follow [DOCKER_SQL_SERVER_SETUP.md](DOCKER_SQL_SERVER_SETUP.md) for detailed instructions.

**Windows:**

```powershell
.\scripts\start-sql-server.ps1
.\scripts\import-bacpac.ps1
```

**Linux / macOS:**

```bash
docker compose --env-file .env.docker up -d
# Wait for SQL to be healthy, then import using SqlPackage or dotnet tool
# Example: dotnet tool install -g Microsoft.SqlPackage
# sqlpackage /Action:Import /SourceFile:prod-backup-20251117.bacpac /TargetConnectionString:"Server=localhost,1433;Database=talent_finder;User Id=sa;Password=YOUR_PASSWORD;Encrypt=false;TrustServerCertificate=true"
```

## Step 2: Anonymize the Database

Anonymize PII in-place. See [DB_ANONYMIZATION.md](DB_ANONYMIZATION.md) for details.

**Dry-run first (recommended):**

```bash
npm run db:anonymize:dry
```

**Apply changes:**

```bash
# Windows PowerShell
$env:ANONYMIZE_CONFIRM="YES"; npm run db:anonymize:apply

# Linux / macOS
ANONYMIZE_CONFIRM=YES npm run db:anonymize:apply
```

## Step 3: Export to Fixtures

```bash
npm run db:fixtures:export
```

This writes JSON files to `prisma/mock-data/` (or the `--outDir` you specify).

## Step 4: Review and Commit

1. Review the generated JSON in `prisma/mock-data/`
2. Ensure no PII has leaked (spot-check users, companies, etc.)
3. Commit the updated fixtures:

```bash
git add prisma/mock-data/*.json
git commit -m "chore: refresh anonymized fixtures from production"
```

---

## Safety Notes

- The anonymization script **refuses to run** unless the database is local (localhost / 127.0.0.1)
- Always run `db:anonymize:dry` before `db:anonymize:apply`
- Do not commit production BACPAC files or `.env.docker` (they contain secrets)
