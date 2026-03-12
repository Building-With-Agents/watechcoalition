# Orchestration (EXP-005 scheduling)

To run scheduler tests: from repo root, `pytest agents/tests/ agents/orchestration/tests/ -v` (or `pytest agents/ -v` to run all agents tests).

## Single pipeline run (ingestion trigger)

Runs the full pipeline once and exits. Same entrypoint used by APScheduler.

From repo root (watechcoalition):

```bash
python -m agents.orchestration.run_ingestion
```

## APScheduler (in-process, recurring)

Runs the pipeline on an interval. Process stays alive and fires every N minutes. Logs `scheduler_run_start` and `scheduler_run_finish` for each fire (for drift and last-run observability).

From repo root (ensure the project venv is activated or use its Python so `apscheduler` and `structlog` are available):

```bash
python -m agents.orchestration.scheduler
```

Stop with Ctrl+C. The scheduler will shut down and exit.

### Environment variables

| Variable | Meaning | Default |
|----------|---------|---------|
| `INGESTION_INTERVAL_MINUTES` | Interval in minutes between runs. | `2` |
| `INGESTION_CRON_EXPRESSION` | Cron expression (e.g. `*/2 * * * *` for every 2 minutes). If set, overrides the interval. | not set |

Examples:

- Every 2 minutes (default): no env needed, or `INGESTION_INTERVAL_MINUTES=2`
- Every 5 minutes: `INGESTION_INTERVAL_MINUTES=5`
- Cron every 2 minutes: `INGESTION_CRON_EXPRESSION="*/2 * * * *"`

Schedule is configurable without code changes: set the env var before starting the process.

## Last run observability

Each pipeline run (when invoked by APScheduler) writes `last_run_start` and `last_run_finish` (ISO timestamps) to a JSON file.

Default path: `agents/data/scheduler_last_run.json`. Override with `SCHEDULER_STATE_PATH` (absolute path).

File shape (the `apscheduler` section is updated on each run; `task_scheduler` may appear in the file for backward compatibility but is not written in normal operation):

```json
{
  "apscheduler": {
    "last_run_start": "...",
    "last_run_finish": "...",
    "last_run_duration_seconds": 0.02,
    "recent_durations_seconds": [0.02, 0.019, ...],
    "average_duration_seconds": 0.019,
    "last_5_runs": [
      { "expected_fire_at": "...", "actual_fire_at": "...", "drift_seconds": 0.0 },
      ...
    ]
  }
}
```

To read last run state (from repo root):

```bash
python -m agents.orchestration.last_run_state
```

### 5-cycle drift table (for EXP-005 findings)

To print a markdown table (Cycle | Expected | Actual | Drift (s)) for pasting into `docs/EXP-005-findings.md`:

```bash
python -m agents.orchestration.last_run_state --drift-table
```

Use `--drift-table apscheduler` to show only APScheduler. Run at least 5 cycles so `last_5_runs` is full and the table has 5 rows.

For the one-page findings (What I Tested, What I Found, Recommendation, Data/Evidence), see `docs/EXP-005-findings.md`.
