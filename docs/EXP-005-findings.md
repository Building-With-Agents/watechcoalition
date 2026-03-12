# EXP-005 Findings: Scheduling mechanism for daily ingestion run

**Owner:** Juan  
**Date:** [fill in]  
**Output:** One-page findings → ADR-005

---

## What I Tested

- **Trigger reliability:** 5 cycles with APScheduler (2-minute interval) and 5 cycles with Windows Task Scheduler (2-minute interval). Recorded actual fire time vs expected fire time to measure drift.
- **Crash recovery:** Killed the APScheduler process mid-cycle (during a pipeline run). Killed the Task Scheduler–launched process mid-cycle. Checked whether the next cycle fired (APScheduler: only after process restart; Task Scheduler: at next scheduled time in a new process).
- **Overlap handling:** Simulated a 3-minute job on a 2-minute interval for both schedulers. Recorded whether the next fire was skipped, delayed, or ran in parallel (APScheduler default max_instances=1 skips until current run finishes).
- **Configurability:** Changed schedule via `INGESTION_INTERVAL_MINUTES` (APScheduler) and via Task Scheduler trigger edit (Task Scheduler). Confirmed no code deploy was required.

*[Paste or summarize your experiment notes here if you have more detail.]*

---

## What I Found

- **Drift:** [e.g. APScheduler: 5/5 fires within X seconds of expected; Task Scheduler: 5/5 within Y seconds. Or note any late/missed fires.]
- **Crash recovery:** [e.g. After killing APScheduler process, no run until restart. After killing Task Scheduler process, next run occurred at the next 2-minute mark in a new process.]
- **Overlap:** [e.g. With 3-min job and 2-min interval, APScheduler skipped the next fire; Task Scheduler started a second process at 2 min (two processes running) or your observed behavior.]
- **Configurability:** [e.g. Both allowed schedule change without code change; env var for APScheduler, Task Scheduler GUI or schtasks for OS.]

*[Replace with your actual findings.]*

---

## Recommendation

**[Choose one: APScheduler | Windows Task Scheduler]** for the daily ingestion run.

**Justification:** [1–3 sentences. e.g. “Task Scheduler recommended: next cycle fires even after a crash without restarting a long-lived process; drift was minimal; operational cost of configuring the task is acceptable for a daily run.” Or: “APScheduler recommended: single process, schedule in code/env, simpler for Docker; we accept that crash recovery depends on process restart (e.g. orchestrator or systemd).”]

---

## Tradeoffs Acknowledged

- **If APScheduler:** Crash recovery depends on something else restarting the process (e.g. Docker restart policy, systemd). In Docker there is no system cron unless we add it.
- **If Task Scheduler:** Each run is a new process (good for crash isolation); schedule change requires editing the task or redeploying the script path; Windows-only (Linux would use cron).

*[Add any other tradeoffs you observed.]*

---

## Data / Evidence

| Scheduler        | Test              | Result / Notes |
|------------------|-------------------|----------------|
| APScheduler      | 5-cycle drift     | [e.g. 5/5 on time; max drift 3s] |
| Task Scheduler   | 5-cycle drift     | [e.g. 5/5 on time; max drift 1s] |
| APScheduler      | Crash mid-cycle   | [e.g. Next run only after restart] |
| Task Scheduler   | Crash mid-cycle   | [e.g. Next run at next 2-min mark] |
| APScheduler      | 3-min job, 2-min interval | [e.g. Next fire skipped] |
| Task Scheduler   | 3-min job, 2-min interval | [e.g. Second process started at 2 min] |
| Both             | Schedule change   | [e.g. Env var vs task edit; no code deploy] |

*[Replace table rows with your recorded outcomes.]*

---

*After filling in the bracketed sections and your notes, this document can feed ADR-005 and the ingestion-agent-design result cell.*
