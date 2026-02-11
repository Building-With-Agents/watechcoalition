# DB Anonymization (Local Docker MSSQL)

> **Note:** New developers should use `npm run db:seed:anonymized` with existing fixtures in `prisma/mock-data/`. This doc describes anonymizing a live Docker DB (e.g. after BACPAC import). That workflow is for maintainers refreshing fixtures — see [REFRESH_ANONYMIZED_FIXTURES.md](REFRESH_ANONYMIZED_FIXTURES.md).

This repo includes a script to **anonymize PII** in the local Docker SQL Server database (typically imported from `prod-backup-20251117.bacpac`).

## Safety

- Defaults to **dry-run** (no writes).
- To actually update data you must:
  - pass `--apply`
  - and set `ANONYMIZE_CONFIRM=YES`
- The script **refuses to run** unless the SQL Server target is **local** (`localhost` / `127.0.0.1` / `(local)`).

## Connection env vars

The script uses one of:

- `DATABASE_URL` (Prisma-style from this repo’s docs), e.g.:
  - `sqlserver://localhost:1433;database=talent_finder;user=SA;password=...;encrypt=false;trustServerCertificate=true`
- `MSSQL_CONNECTION_STRING` (URL-style), e.g.:
  - `mssql://SA:...@localhost:1433/talent_finder`

If your values live in `.env.docker`, you can use:

```powershell
$env:DOTENV_CONFIG_PATH=".env.docker"
node scripts/anonymize-docker-db.mjs --dry-run
```

## Commands

### Dry-run (recommended first)

```powershell
node scripts/anonymize-docker-db.mjs --dry-run
```

Or via npm:

```powershell
npm run db:anonymize:dry
```

### Apply (writes to DB)

```powershell
$env:ANONYMIZE_CONFIRM="YES"
node scripts/anonymize-docker-db.mjs --apply
```

Or via npm:

```powershell
npm run db:anonymize:apply
```

## Preserving login emails (admin + allowlist)

The script preserves emails for users in `cfa_admin` and additionally supports an allowlist:

```powershell
$env:ANONYMIZE_EMAIL_ALLOWLIST="admin1@yourdomain.com,admin2@yourdomain.com"
node scripts/anonymize-docker-db.mjs --dry-run
```

## What gets anonymized (initial set)

- `users`: `first_name`, `last_name`, `phoneCountryCode`, `phone`, `zip`, `photo_url`, and `email` (except admin/allowlist)
- `jobseekers`: `linkedin_url`, `portfolio_url`, `video_url`, `intro_headline`
- `jobseekers_private_data`: `ssn` set to NULL
- `companies`: core contact fields and marketing text fields
- `edu_providers`: contact fields
- `edu_addresses`: street + zip
- `CareerPrepAssessment`: `streetAddress`

