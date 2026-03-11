"""
Ingestion trigger — single pipeline run for EXP-005 (scheduling).

Runs the full pipeline once (same logic as pipeline_runner.main) and exits.
This module is the single entrypoint that both APScheduler and Task Scheduler
will invoke. Run from repo root:

    python -m agents.orchestration.run_ingestion

Optionally reads INGESTION_INTERVAL_MINUTES from the environment for use by
the scheduler; this script does not use it (runs once and exits).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure repo root is on path when run as __main__ from any cwd.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.orchestration.last_run_state import (  # noqa: E402
    write_last_run_finish,
    write_last_run_start,
)
from agents.pipeline_runner import main as pipeline_main  # noqa: E402


def main() -> None:
    """Run the pipeline once (ingestion through orchestration) and exit."""
    _ = os.environ.get("INGESTION_INTERVAL_MINUTES")  # for scheduler use later
    write_last_run_start()
    try:
        pipeline_main()
    finally:
        write_last_run_finish()


if __name__ == "__main__":
    main()
