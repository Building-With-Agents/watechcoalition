"""
EXP-007 Day 1c: Crash test — resume from point of failure without re-running Ingestion.

Procedure:
1. Run Ingestion once to get the IngestBatch event (last successful step).
2. Call resume API for each runner with that event (normalization only).
3. Assert both return NormalizationComplete; Ingestion is not invoked during resume.

Run from repo root: python agents/exp007/crash_test.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Path bootstrap
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import structlog  # noqa: E402

from agents.common.event_envelope import EventEnvelope  # noqa: E402
from agents.exp007.langgraph_runner import run_from_after_ingestion_langgraph  # noqa: E402
from agents.exp007.pure_python_runner import run_from_after_ingestion_pure_python  # noqa: E402
from agents.ingestion.agent import IngestionAgent  # noqa: E402

log = structlog.get_logger()


def main() -> int:
    fixtures_dir = Path(__file__).resolve().parent.parent / "data" / "fixtures"
    fallback = fixtures_dir / "fallback_scrape_sample.json"
    if not fallback.exists():
        log.error("crash_test_fixture_not_found", path=str(fallback))
        return 1

    postings = json.loads(fallback.read_text(encoding="utf-8"))
    posting = postings[0]
    cid = str(posting.get("posting_id", "1"))

    # Step 1: Run Ingestion only to get the event we would pass to Normalization
    ingestion_agent = IngestionAgent()
    initial = EventEnvelope(
        correlation_id=cid,
        agent_id="pipeline-runner",
        payload=posting,
    )
    ingestion_output = ingestion_agent.process(initial)
    event_type_after_ingestion = ingestion_output.payload.get("event_type")
    if event_type_after_ingestion != "IngestBatch":
        log.error(
            "crash_test_unexpected_event",
            expected="IngestBatch",
            got=event_type_after_ingestion,
        )
        return 1

    # Step 2: Resume from that event (normalization only) — no Ingestion re-run
    state_langgraph = run_from_after_ingestion_langgraph(ingestion_output)
    state_pure = run_from_after_ingestion_pure_python(ingestion_output)

    # Step 3: Assert both produced NormalizationComplete
    out_lg = state_langgraph.get("current_event", {}).get("payload", {}).get("event_type")
    out_pp = state_pure.get("current_event", {}).get("payload", {}).get("event_type")

    if out_lg != "NormalizationComplete" or out_pp != "NormalizationComplete":
        log.error(
            "crash_test_resume_failed",
            langgraph=out_lg,
            pure_python=out_pp,
        )
        return 1

    log.info(
        "crash_test_passed",
        note="Both runners resumed from after Ingestion without re-running it.",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
