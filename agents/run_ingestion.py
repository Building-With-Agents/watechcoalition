"""
Run the Ingestion Agent with JSearch and log the output.

Use this to test the ingestion agent against the JSearch API and see
the IngestBatch event (counts and sample records).

Prerequisites:
  - JSEARCH_API_KEY set in .env or environment
  - Optional: PYTHON_DATABASE_URL to stage records to raw_ingested_jobs

Usage (from repo root):
  python agents/run_ingestion.py
  python agents/run_ingestion.py --location "El Paso, TX" --limit 5

From agents directory:
  python run_ingestion.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Repo root on path for "from agents.*"
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")
except ImportError:
    pass

import structlog

from agents.common.event_envelope import EventEnvelope
from agents.ingestion.agent import IngestionAgent
from agents.ingestion.sources.jsearch_adapter import JSEARCH_BASE_URL

# Output file for ingestion agent result (agents/ingestion_agent_output.json)
_INGESTION_OUTPUT_FILE = Path(__file__).resolve().parent / "ingestion_agent_output.json"

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger()


# Default region: El Paso / Borderplex (can override via CLI)
DEFAULT_REGION = {
    "region_id": "el-paso",
    "display_name": "El Paso / Borderplex",
    "query_location": "El Paso, TX",
    "radius_miles": 50,
    "states": ["TX"],
    "countries": ["US"],
    "sources": ["jsearch"],
    "role_categories": ["Technology", "Healthcare"],
    "keywords": ["software", "engineer", "data"],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ingestion Agent (JSearch) and print output")
    parser.add_argument(
        "--location",
        default="El Paso, TX",
        help="Query location for JSearch (e.g. 'El Paso, TX')",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Approximate max number of jobs to fetch (controls pages)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Log full event payload as JSON (default: structured summary)",
    )
    args = parser.parse_args()

    # So the adapter respects --limit (uses BATCH_SIZE)
    os.environ["BATCH_SIZE"] = str(max(1, args.limit))

    region = {
        **DEFAULT_REGION,
        "query_location": args.location,
    }

    # Show where we fetch data from (JSearch API via RapidAPI)
    log.info(
        "ingestion_data_source",
        fetch_url=JSEARCH_BASE_URL,
        provider="RapidAPI (https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)",
    )

    agent = IngestionAgent()
    log.info("ingestion_health_check", **agent.health_check())

    event = EventEnvelope(
        correlation_id="run-ingestion-cli",
        agent_id="cli",
        payload={"region_config": region, "source": "jsearch"},
    )

    log.info("ingestion_start", source="jsearch", location=args.location, limit=args.limit)
    out = agent.process(event)

    if out is None:
        log.error("ingestion_agent_returned_none")
        sys.exit(1)

    # Write full ingestion agent output to file
    output_data = json.loads(json.dumps(out.model_dump(mode="json"), default=str))
    _INGESTION_OUTPUT_FILE.write_text(
        json.dumps(output_data, indent=2, default=str),
        encoding="utf-8",
    )
    log.info("ingestion_output_written", path=str(_INGESTION_OUTPUT_FILE))

    if args.json:
        payload_serializable = json.loads(
            json.dumps(out.model_dump(mode="json"), default=str)
        )
        log.info("ingestion_event", payload=payload_serializable)
        return

    p = out.payload
    event_type = p.get("event_type", "")
    log.info(
        "ingestion_event_summary",
        event_type=event_type,
        correlation_id=out.correlation_id,
        batch_id=p.get("batch_id"),
        source=p.get("source"),
        region_id=p.get("region_id"),
        total_fetched=p.get("total_fetched"),
        staged_count=p.get("staged_count"),
        dedup_count=p.get("dedup_count"),
        error_count=p.get("error_count"),
    )
    if event_type == "SourceFailure":
        log.error(
            "ingestion_source_failure",
            source=p.get("source"),
            error=p.get("error"),
        )
        sys.exit(1)

    records = p.get("records") or []
    sample = [
        {
            "title": rec.get("title", "?"),
            "company": rec.get("company", "?"),
            "external_id": rec.get("external_id", "?"),
        }
        for rec in records[:5]
    ]
    log.info(
        "ingestion_records",
        record_count=len(records),
        sample_records=sample,
        more_count=max(0, len(records) - 5) if len(records) > 5 else 0,
    )


if __name__ == "__main__":
    main()
