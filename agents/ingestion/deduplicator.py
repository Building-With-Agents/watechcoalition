# agents/ingestion/deduplicator.py
"""Fingerprint and dedup: sha256(source + external_id + title + company + date_posted). JSearch wins over scraped."""

# TODO: dedup against raw_ingested_jobs.raw_payload_hash; discard silently; increment counter.
