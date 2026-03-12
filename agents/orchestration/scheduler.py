"""
APScheduler-based ingestion trigger for EXP-005.

Runs the pipeline (same entrypoint as run_ingestion) on a configurable interval.
Process stays alive and fires every N minutes. Logs each run start and finish
for drift measurement and last-run observability.

Run from repo root:

    python -m agents.orchestration.scheduler

Environment variables:

    INGESTION_INTERVAL_MINUTES  Interval in minutes (default: 2). Ignored if
                                INGESTION_CRON_EXPRESSION is set.
    INGESTION_CRON_EXPRESSION   Optional cron expression (e.g. "*/2 * * * *"
                                for every 2 minutes). Overrides interval.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure repo root is on path when run as __main__ from any cwd.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import structlog  # noqa: E402
from apscheduler.schedulers.background import BackgroundScheduler  # noqa: E402

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


def _scheduled_job() -> None:
    """Run the pipeline once. Log run start and finish for observability."""
    run_start = datetime.now(datetime.UTC)
    log.info(
        "scheduler_run_start",
        run_start=run_start.isoformat(),
    )
    try:
        os.environ["SCHEDULER_TYPE"] = "apscheduler"
        from agents.orchestration.run_ingestion import main as run_ingestion_main  # noqa: E402
        run_ingestion_main()
    except SystemExit as e:
        if e.code != 0:
            log.warning(
                "scheduler_run_exit_nonzero",
                code=e.code,
                run_start=run_start.isoformat(),
            )
    except Exception as exc:
        log.error(
            "scheduler_run_error",
            error=str(exc),
            run_start=run_start.isoformat(),
        )
    run_finish = datetime.now(datetime.UTC)
    log.info(
        "scheduler_run_finish",
        run_start=run_start.isoformat(),
        run_finish=run_finish.isoformat(),
    )


def _interval_minutes() -> int:
    raw = os.environ.get("INGESTION_INTERVAL_MINUTES", "2").strip()
    try:
        n = int(raw)
        return max(1, n)
    except ValueError:
        return 2


def main() -> None:
    """Start the scheduler and block the main thread."""
    cron_expr = os.environ.get("INGESTION_CRON_EXPRESSION", "").strip()
    interval_min = _interval_minutes()

    scheduler = BackgroundScheduler()

    if cron_expr:
        from apscheduler.triggers.cron import CronTrigger  # noqa: E402
        scheduler.add_job(
            _scheduled_job,
            trigger=CronTrigger.from_crontab(cron_expr),
            id="ingestion_trigger",
            name="ingestion_trigger",
        )
        log.info(
            "scheduler_started",
            trigger="cron",
            cron_expression=cron_expr,
        )
    else:
        scheduler.add_job(
            _scheduled_job,
            trigger="interval",
            minutes=interval_min,
            id="ingestion_trigger",
            name="ingestion_trigger",
        )
        log.info(
            "scheduler_started",
            trigger="interval",
            interval_minutes=interval_min,
        )

    scheduler.start()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        log.info("scheduler_stopping")
        scheduler.shutdown(wait=True)

if __name__ == "__main__":
    main()
