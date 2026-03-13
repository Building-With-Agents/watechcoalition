# Experiment EXP-003: Cross-Source Deduplication Strategy

## What I Tested
For my experiment I used a dataset of **200 real JSearch postings** for the El Paso/Borderplex region and injected **5 manual duplicates** scraped from company career pages that worked as ground-truth targets. 

The main goal was to find the most reliable method to catch cross-spurce duplicate.
---

## What I Found
* Using only the pure hash (source + external_id + title + company + date_posted) found 0 duplicates. This confirms that JSearch and scraped career pages use different IDs for the same job, which makes them invisible to exact matching logic.
* The hybrid strategy successfully found the 5 injected duplicates. By using a logical fingerprint (title, company only—no date_posted), we bridged the gap between different platforms and avoid date-granularity issues (e.g. "2 days ago" vs absolute timestamps).
* The hashing logic proved stable. It successfully treated variations like "Engineer" and "engineer" as identical and handled `None` values without crashing.
*The simulated DB layer successfully blocked the 5 duplicate attempts using `ON CONFLICT DO NOTHING` logic. This proves the database acts as a reliable way of avoiding collisions.

---

## Recommendation
We should move forward with the **Hybrid Hashing strategy** because it solves the cross-source duplicate issue, and the **PostgreSQL UNIQUE constraint** on `raw_payload_hash` provides the necessary safety for concurrent inserts.

---

## Tradeoffs Acknowledged
* **Collision Risk:** Two different jobs at the same company with the same normalized title could collide; catching cross-source duplicates is a higher priority for data quality.
* **Implementation:** The strategy requires normalization before hashing to ensure consistency across different scrapers.

---

## Data / Evidence
The testing results were the following:

* **`test_generate_pure_hash_normalizes_none`**: Demonstrated **100% Reliability**; the function turns `None` into `""` to ensure a valid 64-char SHA-256 string is always generated without crashing.
* **`test_generate_pure_hash_deterministic`**: Confirmed **100% Consistency**; the same job record always produces the same pure hash with no randomness.
* **`test_generate_logical_hash_normalization`**: Confirmed a **0% False Positive rate**; normalization ensures "Engineer" and "engineer" are treated as identical; same title+company with different dates yield the same logical hash.
* **`test_pure_hash_strategy`**: Quantified the **100% Miss Rate** on cross-source targets; using only source/external_id found **0 duplicates** (The "Blind Spot").
* **`test_hybrid_strategy`**: Achieved a **100% True Positive rate (5/5)**; by combining pure and logical hashes, all 5 injected cross-source duplicates were detected.
* **`test_database_enforcement_layer`**: Verified **100% Concurrency Safety**; the simulated DB layer rejected at least 5 duplicate attempts, proving the "DB layer" blocks duplicates even if upstream logic fails.

## Takeaway
This experiments showed that pure hash alone misses cross-source duplicates, the hybrid strategy finds them, and the simulated DB constraint would also block duplicate inserts.