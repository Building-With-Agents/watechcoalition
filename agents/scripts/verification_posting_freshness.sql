-- Read-only verification for dbo.posting_freshness (Issue #184 / Step 10).
-- Run against a dev database, e.g.:
--   psql "$PYTHON_DATABASE_URL" -f agents/scripts/verification_posting_freshness.sql
-- (Convert URL to libpq form or use your SQL client.)

-- 1) Row count
SELECT count(*) AS posting_freshness_row_count FROM dbo.posting_freshness;

-- 2) Sample latest computed_at (up to 5 rows)
SELECT posting_id, first_seen, last_seen, duration_days, computed_at
FROM dbo.posting_freshness
ORDER BY computed_at DESC NULLS LAST
LIMIT 5;

-- 3) NOT NULL guard on required columns (should return zero bad rows)
SELECT count(*) AS null_violations
FROM dbo.posting_freshness
WHERE posting_id IS NULL
   OR first_seen IS NULL
   OR last_seen IS NULL
   OR duration_days IS NULL
   OR is_repost IS NULL
   OR repost_count IS NULL
   OR fill_proxy IS NULL
   OR computed_at IS NULL;

-- 4) Repost and fill_proxy distribution
SELECT is_repost, fill_proxy, count(*) AS n
FROM dbo.posting_freshness
GROUP BY is_repost, fill_proxy
ORDER BY is_repost, fill_proxy;
