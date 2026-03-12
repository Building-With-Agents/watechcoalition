# EXP-005 Runbook — How to run and check off the task checklist

Run everything from **watechcoalition** repo root. Use the project venv (e.g. `.\venv\Scripts\python.exe` or activate venv first).

---

## Checklist items that are already done (code/artifacts)

| # | Item | How it's done |
|---|------|----------------|
| 1 | Implement ingestion trigger using APScheduler | `agents/orchestration/scheduler.py` — run with command below. |
| 2 | Implement same trigger using Task Scheduler | `agents/orchestration/run_ingestion_task.bat` + README (schtasks/GUI). |
| 3 | Set 2-minute interval | Default in scheduler; Task Scheduler task created with `/mo 2`. |
| 7 | Configurability via env / no code deploy | `INGESTION_INTERVAL_MINUTES` and `INGESTION_CRON_EXPRESSION`; Task Scheduler: edit trigger. |
| 8 | Create test_scheduler.py | `agents/orchestration/tests/test_scheduler.py` exists. |
| 9 | All new tests pass | Run command in "Tests" section below. |
| 10 | One-page findings doc | `docs/EXP-005-findings.md` — fill in with your experiment data. |

---

## How to run and check off the rest

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
3. In the console you’ll see JSON lines: `scheduler_run_start` and `scheduler_run_finish` for each fire. Note the timestamps (or use `agents/data/scheduler_last_run.json` — APScheduler updates the `apscheduler` key only).
4. **Check off:** "Run 5 cycles … and record schedule accuracy" for APScheduler — record expected vs actual fire times and compute drift; put results in `docs/EXP-005-findings.md` Data/Evidence table.
5. Stop with **Ctrl+C**.

### Run Task Scheduler (2-min interval, 5 cycles)

1. Create the task (elevated Command Prompt; fix the path to your repo):
   ```cmd
   schtasks /create /tn "WATechIngestionTrigger" /tr "C:\Users\juanr_zas\Desktop\wAIfinder\watechcoalition\agents\orchestration\run_ingestion_task.bat" /sc minute /mo 2 /ru "%USERNAME%"
   ```
2. Note start time. Wait **8–10 minutes** so 5 runs occur (e.g. 10:00, 10:02, 10:04, 10:06, 10:08).
3. Record actual run times (Task Scheduler → task → History, or `scheduler_last_run.json` — Task Scheduler updates the `task_scheduler` key only). Run `python -m agents.orchestration.last_run_state` to see both schedulers’ last run in one JSON for comparison.
4. **Check off:** "Run 5 cycles …" for Task Scheduler — fill drift in findings.
5. Optional, delete task after: `schtasks /delete /tn "WATechIngestionTrigger" /f`

### Crash test (check off "Crash test: kill … mid-cycle")

- **APScheduler:** Start the scheduler, wait for one run to begin, then **kill the process** (Ctrl+C or Task Manager). Confirm: next run does **not** happen until you start the scheduler again.
- **Task Scheduler:** Create the task, let one run start, **kill that Python process** (Task Manager). Confirm: at the **next** 2-minute mark, Task Scheduler starts a **new** process and the run happens.

Record outcomes in the findings doc.

### Long-run test / overlap (check off "Long-run test: 3-min job, 2-min interval")

- **APScheduler:** Temporarily make the job take 3 minutes (e.g. add `time.sleep(180)` at the start of `_scheduled_job` in `scheduler.py`, or a 3-minute sleep in `run_ingestion.main`). Run scheduler with 2-min interval. Observe: the next fire is **skipped** until the 3-min job finishes (max_instances=1). Remove the sleep after.
- **Task Scheduler:** Same 3-min job (e.g. add sleep in `run_ingestion.py` and run via the batch). At 2 min, Task Scheduler starts a **second** process (two runs overlapping). Document that in findings.

### Configurability test (check off "Configurability test")

- **APScheduler:** Stop scheduler. Set `INGESTION_INTERVAL_MINUTES=5`, start scheduler again. Confirm logs show `interval_minutes: 5`. No code change.
- **Task Scheduler:** Edit the task → Triggers → change "Repeat task every" to 5 minutes. Run once and confirm; no code deploy.

### Tests (check off "Ensure all new tests pass")

From repo root:

```bash
pytest agents/tests/ agents/orchestration/tests/ -v
```

Or from repo root with venv:

```bash
.\venv\Scripts\python.exe -m pytest agents/tests/ agents/orchestration/tests/ -v
```

All 25 tests (including scheduler tests) should pass.

### Findings doc (check off "Write one-page findings doc")

1. Open `docs/EXP-005-findings.md`.
2. Fill **What I Tested** with what you actually ran.
3. Fill **What I Found** with your drift, crash, overlap, and configurability results.
4. Fill **Data/Evidence** table with your numbers and outcomes.
5. Pick **Recommendation**: APScheduler or Task Scheduler, with short justification.
6. Complete **Tradeoffs Acknowledged**.

---

## Quick command reference

| Goal | Command |
|------|--------|
| Run APScheduler (2-min, keep running) | `python -m agents.orchestration.scheduler` |
| Run pipeline once (no scheduler) | `python -m agents.orchestration.run_ingestion` |
| Query last run start/finish (both schedulers) | `python -m agents.orchestration.last_run_state` (output has `apscheduler` and `task_scheduler` keys) |
| Run all tests | `pytest agents/tests/ agents/orchestration/tests/ -v` |
| Create Task Scheduler task (2 min) | `schtasks /create /tn "WATechIngestionTrigger" /tr "<full path to run_ingestion_task.bat>" /sc minute /mo 2 /ru "%USERNAME%"` |
| Delete task | `schtasks /delete /tn "WATechIngestionTrigger" /f` |
