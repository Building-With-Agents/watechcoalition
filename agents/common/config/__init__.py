# agents.common.config — env-based config (BATCH_SIZE, thresholds, cron, etc.).

import os

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
SPAM_FLAG_THRESHOLD = float(os.getenv("SPAM_FLAG_THRESHOLD", "0.7"))
SPAM_REJECT_THRESHOLD = float(os.getenv("SPAM_REJECT_THRESHOLD", "0.9"))
SKILL_CONFIDENCE_THRESHOLD = float(os.getenv("SKILL_CONFIDENCE_THRESHOLD", "0.75"))
INGESTION_SCHEDULE = os.getenv("INGESTION_SCHEDULE", "0 2 * * *")
