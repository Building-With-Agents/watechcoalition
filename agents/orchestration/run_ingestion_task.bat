@echo off
REM Run the ingestion trigger once (same entrypoint as APScheduler).
REM For use by Windows Task Scheduler. Set working dir to repo root and run
REM one pipeline run. Use venv Python if present so dependencies resolve.

set SCRIPT_DIR=%~dp0
REM Repo root = two levels up from agents/orchestration
set REPO_ROOT=%SCRIPT_DIR%..\..
cd /d "%REPO_ROOT%"

if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=python
)

set SCHEDULER_TYPE=task_scheduler
"%PYTHON%" -m agents.orchestration.run_ingestion
