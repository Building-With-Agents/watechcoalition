-- Enable pgvector extension for embedding similarity search
-- Required by Skills Extraction Agent (taxonomy cascade step 3: cosine similarity >= 0.92)
-- and Week 9 near-dedup work
-- This script auto-runs on first PostgreSQL container creation via Docker entrypoint
CREATE EXTENSION IF NOT EXISTS vector;
