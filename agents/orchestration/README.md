# Orchestration (EXP-005 scheduling)

To run scheduler tests: from repo root, `pytest agents/tests/ agents/orchestration/tests/ -v` (or `pytest agents/ -v` to run all agents tests).

## Single pipeline run (ingestion trigger)

Runs the full pipeline once and exits. Same entrypoint used by APScheduler and Task Scheduler.

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

Each pipeline run (from the scheduler or from Task Scheduler) writes `last_run_start` and `last_run_finish` (ISO timestamps) to a JSON file so you can query when the ingestion trigger last ran.

Default path: `agents/data/scheduler_last_run.json`. Override with `SCHEDULER_STATE_PATH` (absolute path).

To read the last run timestamps from the command line (from repo root):

```bash
python -m agents.orchestration.last_run_state
```

Output is JSON, e.g. `{"last_run_start": "2026-03-11T12:00:00+00:00", "last_run_finish": "..."}`.

## Windows Task Scheduler (same trigger, external process)

A batch script runs the same ingestion entrypoint as APScheduler so you can compare in-process vs OS scheduler (EXP-005).

**Script:** `agents/orchestration/run_ingestion_task.bat`

- Sets working directory to the watechcoalition repo root (two levels up from the script).
- Uses `venv\Scripts\python.exe` if present, otherwise `python` from PATH.
- Runs exactly one pipeline run: `python -m agents.orchestration.run_ingestion`.

You can run it manually from a shell (from any directory) or schedule it with Task Scheduler.

### Create a task that runs every 2 minutes (schtasks)

Open Command Prompt or PowerShell **as Administrator**. Replace `C:\path\to\watechcoalition` with your actual repo path.

```cmd
schtasks /create /tn "WATechIngestionTrigger" /tr "C:\path\to\watechcoalition\agents\orchestration\run_ingestion_task.bat" /sc minute /mo 2 /ru "%USERNAME%"
```

- `/tn` task name (change if you like).
- `/tr` full path to the batch file.
- `/sc minute /mo 2` run every 2 minutes.
- `/ru "%USERNAME%"` run as the current user (so Python and venv are the same as your dev environment). Use `SYSTEM` or another user if you prefer.

The task starts at creation time and then runs every 2 minutes. To run the task once immediately for testing:

```cmd
schtasks /run /tn "WATechIngestionTrigger"
```

### Create or edit the task (Task Scheduler GUI)

1. Open **Task Scheduler** (taskschd.msc).
2. **Create Task** (or **Create Basic Task**): set name e.g. `WATechIngestionTrigger`.
3. **Triggers:** New → “Begin the task”: **On a schedule** → **Daily** (or **One time** then set repeat). Check **Repeat task every** → choose **2 minutes** for a 2-minute interval. Set duration **Indefinitely** (or as needed).
4. **Actions:** New → **Start a program** → Program: full path to `run_ingestion_task.bat` (e.g. `C:\Users\You\Desktop\wAIfinder\watechcoalition\agents\orchestration\run_ingestion_task.bat`). “Start in” can be left empty (the script changes to repo root).
5. **Conditions / Settings:** Uncheck “Start the task only if the computer is on AC power” if you want it to run on battery.

### Change the interval (no code deploy)

- **schtasks:** Delete and recreate with a different `/mo` value (e.g. `/mo 5` for every 5 minutes), or use **Task Scheduler GUI** to edit.
- **GUI:** Task Scheduler → double-click the task → **Triggers** tab → **Edit** → change “Repeat task every” to the desired minutes (e.g. 5) → OK. No code change or redeploy required.
