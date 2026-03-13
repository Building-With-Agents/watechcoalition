# ADR-005: Scheduling mechanism for daily ingestion run

**Owner:** Juan  
**Date:** 2026-03-12  
**Status:** Accepted

The project uses **APScheduler only** for the ingestion run. Task Scheduler is no longer supported or recommended.

---

## What I Tested

- **Trigger reliability (5-cycle drift):** Ran 5 cycles with APScheduler at a 2-minute interval. Recorded actual vs expected fire times using `scheduler_last_run.json` and `last_5_runs` drift data.
- **Crash recovery:** Killed the APScheduler process mid-cycle; confirmed the next run only happens after restarting the scheduler.
- **Overlap handling:** Simulated a 3-minute job on a 2-minute interval; APScheduler skipped the next fire until the current run finished.
- **Configurability:** Changed the schedule via `INGESTION_INTERVAL_MINUTES`; worked without a code deploy.

---

## What I Found

- **Drift:** APScheduler: 5/5 fires within ~0.08 s of expected (slightly early). Effectively on time for a 2-minute interval.
- **Crash recovery:** After killing the process, the next run only happened after restarting the scheduler (recovery depends on process restart, e.g. Docker or systemd).
- **Overlap:** With a 3-min job and 2-min interval, APScheduler skipped the next fire until the current run finished (max_instances=1).
- **Configurability:** Schedule change via env var; no code changes required.

---

## Recommendation

**APScheduler** for the daily ingestion run.

**Justification:** Single process, schedule in code/env, and simpler for Docker. Drift was minimal in the 5-cycle test. We accept that crash recovery depends on something else restarting the process (e.g. orchestrator or Docker restart policy).

---

## Tradeoffs Acknowledged

- **APScheduler:** Crash recovery depends on something else restarting the process (e.g. Docker restart policy, systemd). In Docker there is no system cron unless we add it. Overlap is avoided by design (max_instances=1).

---

## Data / Evidence

| Test                      | Result / Notes                                   |
|---------------------------|--------------------------------------------------|
| 5-cycle drift             | 5/5 on time; max drift ~0.08 s (slightly early). |
| Crash mid-cycle           | Next run only after restart.                     |
| 3-min job, 2-min interval | Next fire skipped until current run finished.    |
| Schedule change           | Env var; no code deploy.                         |

### Drift table (from `python -m agents.orchestration.last_run_state --drift-table`)

**apscheduler** (last 5 runs)

| Cycle | Expected                         | Actual                           | Drift (s) |
| ----- | -------------------------------- | -------------------------------- | --------- |
| 1     | 2026-03-12T14:10:37.519914+00:00 | 2026-03-12T14:10:37.519914+00:00 | 0.0       |
| 2     | 2026-03-12T14:12:37.519914+00:00 | 2026-03-12T14:12:37.444609+00:00 | -0.075    |
| 3     | 2026-03-12T14:14:37.519914+00:00 | 2026-03-12T14:14:37.450005+00:00 | -0.07     |
| 4     | 2026-03-12T14:16:37.519914+00:00 | 2026-03-12T14:16:37.438777+00:00 | -0.081    |
| 5     | 2026-03-12T14:18:37.519914+00:00 | 2026-03-12T14:18:37.445834+00:00 | -0.074    |

---

## How to run (runbook)

Run everything from **watechcoalition** repo root. Use the project venv (e.g. `.\venv\Scripts\python.exe` or activate venv first).

### Run APScheduler (2-min interval, 5 cycles)

1. From repo root:
   ```bash
   python -m agents.orchestration.scheduler
   ```
   Or with venv Python:
   ```bash
   .\venv\Scripts\python.exe -m agents.orchestration.scheduler
   ```
2. Leave it running **at least 10 minutes** (5 fires × 2 min). First fire at start, then +2, +4, +6, +8 min.
3. In the console you'll see JSON lines: `scheduler_run_start` and `scheduler_run_finish` for each fire. Note the timestamps (or use `agents/data/scheduler_last_run.json`).
4. Stop with **Ctrl+C**.

### Run pipeline once (no scheduler)

```bash
python -m agents.orchestration.run_ingestion
```

### Query last run state / drift table

```bash
python -m agents.orchestration.last_run_state
python -m agents.orchestration.last_run_state --drift-table
```

### Tests

```bash
pytest agents/tests/ agents/orchestration/tests/ -v
```

### Quick command reference

| Goal | Command |
|------|--------|
| Run APScheduler (2-min, keep running) | `python -m agents.orchestration.scheduler` |
| Run pipeline once (no scheduler) | `python -m agents.orchestration.run_ingestion` |
| Query last run start/finish | `python -m agents.orchestration.last_run_state` |
| Run all tests | `pytest agents/tests/ agents/orchestration/tests/ -v` |

---

*This document feeds the ingestion-agent-design result cell.*
