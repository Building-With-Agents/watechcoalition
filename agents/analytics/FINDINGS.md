# Analytics Agent — Week 7 Findings

## What I Built
- Step 1: Minimum data guard — pipeline skips if fewer than 50 new postings
- Step 6: sector_summary_weekly — weekly job counts and salary percentiles grouped by NAICS sector
- Step 7: geo_demand_weekly — weekly job counts by Borderplex subregion, wired into pipeline after step 6
- compute_salary_percentiles() — reusable helper returning p25/p50/p75/p95 per group, published for Pair C (issue #188)
- SectorSummaryWeekly + GeoDemandWeekly SQLAlchemy models with migrations

## Verification Results
- 16/16 tests passing across test_geo_demand.py, test_minimum_data_guard.py, test_salary_percentiles.py, test_sector_weekly.py
- compute_salary_percentiles() confirmed consumed by Pair C via cherry-pick (commit 2d2edafc)

## Design Decisions
- Used PostgreSQL percentile_disc for salary percentiles — exact rather than interpolated
- Data guard uses watermark to avoid reprocessing the same week
- Salary basis: midpoint of min/max when both present, else max, else min

## Challenges
- Merged Gary's development infrastructure fixes (skills extraction fix, Langfuse tracing, label→skill_name rename) and resolved linting errors across multiple files
- Local Docker postgres environment issues — postgres-server missing POSTGRES_PASSWORD env var

## Carries Forward
- Step 7 geo_demand_weekly persistence bug — aggregator computes results correctly but session.add_all() is not called, so rows are never written to the database. One-line fix for Week 8.
- temporal_trend and top_roles columns on geo_demand_weekly not yet implemented