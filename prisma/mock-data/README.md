# Anonymized Mock Data (Prisma Seed)

This folder is intended to hold **git-tracked** anonymized JSON fixtures that interns can use to populate a local DB.

## Intern setup flow

```text
prisma db push
prisma generate
node prisma/seed-anonymized.mjs
```

## Maintainer flow (generate fixtures)

1. Import + anonymize your local Docker MSSQL DB (see `scripts/anonymize-docker-db.mjs`)
2. Export fixtures:

```text
node scripts/export-anonymized-fixtures.mjs --outDir prisma/mock-data
```

