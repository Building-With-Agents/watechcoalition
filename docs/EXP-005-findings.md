# EXP-005 Findings: Scheduling mechanism for daily ingestion run

**Owner:** Juan  
**Date:** 2026-03-12  
**Output:** One-page findings → ADR-005

---

## What I Tested

- **Trigger reliability (5-cycle drift):** I ran 5 cycles with APScheduler at a 2-minute interval and 5 cycles with Windows Task Scheduler at 2 minutes. I recorded actual vs expected fire times using `scheduler_last_run.json` and the `last_5_runs` drift data so I could measure drift.
- **Crash recovery:** I killed the APScheduler process mid-cycle (during a pipeline run) and the Task Scheduler–launched process mid-cycle, and checked whether the next cycle fired (APScheduler only after restart; Task Scheduler at the next scheduled time in a new process).
- **Overlap handling:** I simulated a 3-minute job on a 2-minute interval for both schedulers and recorded whether the next fire was skipped, delayed, or ran in parallel (APScheduler skips until the current run finishes; Task Scheduler starts a second process).
- **Configurability:** I changed the schedule via `INGESTION_INTERVAL_MINUTES` for APScheduler and via the Task Scheduler trigger for the OS task; both worked without a code deploy.

---

## What I Found

- **Drift:** APScheduler: 5/5 fires within ~0.08 s of expected (slightly early). Task Scheduler: 5/5 within ~0.09 s (slightly late). Both were effectively on time for a 2-minute interval.
- **Crash recovery:** After killing the APScheduler process, the next run only happened after I restarted the scheduler. After killing the Task Scheduler–launched process, the next run happened at the next 2-minute mark in a new process.
- **Overlap:** With a 3-min job and 2-min interval, APScheduler skipped the next fire until the current run finished. Task Scheduler started a second process at the 2-minute mark (two processes running).
- **Configurability:** Both allowed changing the schedule without code changes (env var for APScheduler; Task Scheduler GUI or schtasks for the OS task).

---

## Recommendation

**APScheduler** for the daily ingestion run.

**Justification:** Single process, schedule in code/env, and simpler for Docker. Drift was minimal in the 5-cycle test. We accept that crash recovery depends on something else restarting the process (e.g. orchestrator or Docker restart policy).

---

## Tradeoffs Acknowledged

- **If APScheduler:** Crash recovery depends on something else restarting the process (e.g. Docker restart policy, systemd). In Docker there is no system cron unless we add it.
- **If Task Scheduler:** Each run is a new process (good for crash isolation); schedule change requires editing the task or redeploying the script path; Windows-only (Linux would use cron).

---

## Data / Evidence

| Scheduler        | Test                      | Result / Notes |
|------------------|---------------------------|----------------|
| APScheduler      | 5-cycle drift             | 5/5 on time; max drift ~0.08 s (slightly early). |
| Task Scheduler   | 5-cycle drift             | 5/5 on time; max drift ~0.09 s (slightly late). |
| APScheduler      | Crash mid-cycle           | Next run only after restart. |
| Task Scheduler   | Crash mid-cycle           | Next run at next 2-min mark in new process. |
| APScheduler      | 3-min job, 2-min interval | Next fire skipped until current run finished. |
| Task Scheduler   | 3-min job, 2-min interval | Second process started at 2 min (overlap). |
| Both             | Schedule change           | Env var vs task edit; no code deploy. |

### Drift table (from `python -m agents.orchestration.last_run_state --drift-table`)

**apscheduler** (last 5 runs)

| Cycle | Expected | Actual | Drift (s) |
|-------|----------|--------|-----------|
| 1 | 2026-03-12T14:10:37.519914+00:00 | 2026-03-12T14:10:37.519914+00:00 | 0.0 |
| 2 | 2026-03-12T14:12:37.519914+00:00 | 2026-03-12T14:12:37.444609+00:00 | -0.075 |
| 3 | 2026-03-12T14:14:37.519914+00:00 | 2026-03-12T14:14:37.450005+00:00 | -0.07 |
| 4 | 2026-03-12T14:16:37.519914+00:00 | 2026-03-12T14:16:37.438777+00:00 | -0.081 |
| 5 | 2026-03-12T14:18:37.519914+00:00 | 2026-03-12T14:18:37.445834+00:00 | -0.074 |

**task_scheduler** (last 5 runs)

| Cycle | Expected | Actual | Drift (s) |
|-------|----------|--------|-----------|
| 1 | 2026-03-12T14:10:01.928451+00:00 | 2026-03-12T14:10:01.928451+00:00 | 0.0 |
| 2 | 2026-03-12T14:12:01.928451+00:00 | 2026-03-12T14:12:01.933026+00:00 | 0.005 |
| 3 | 2026-03-12T14:14:01.928451+00:00 | 2026-03-12T14:14:01.979856+00:00 | 0.051 |
| 4 | 2026-03-12T14:16:01.928451+00:00 | 2026-03-12T14:16:02.002428+00:00 | 0.074 |
| 5 | 2026-03-12T14:18:01.928451+00:00 | 2026-03-12T14:18:02.016675+00:00 | 0.088 |

---

*This document feeds ADR-005 and the ingestion-agent-design result cell.*
