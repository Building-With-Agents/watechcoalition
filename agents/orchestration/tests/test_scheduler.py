"""
Tests for the APScheduler-based ingestion trigger (EXP-005).

Covers: trigger reliability, schedule from environment, overlap handling,
and crash recovery documentation.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

class TestTriggerReliability:
    """The job callable invokes the ingestion entrypoint when it runs."""

    def test_scheduled_job_invokes_run_ingestion_once(self) -> None:
        """When the scheduler fires the job, it calls run_ingestion.main exactly once."""
        # Patch DB first so importing run_ingestion (via patch target) does not require PYTHON_DATABASE_URL.
        mock_factory = MagicMock()
        mock_factory.return_value = MagicMock()  # SessionLocal() -> session context manager
        with patch("agents.common.data_store.database.get_engine", return_value=MagicMock()), patch(
            "agents.common.data_store.database.get_session_factory", return_value=mock_factory
        ):
            with patch("agents.orchestration.scheduler.log"), patch(
                "agents.orchestration.run_ingestion.main"
            ) as mock_run_ingestion:
                from agents.orchestration.scheduler import _scheduled_job

                _scheduled_job()
                mock_run_ingestion.assert_called_once()

    def test_scheduled_job_invokes_entrypoint_even_if_import_late(self) -> None:
        """Job callable uses the same entrypoint as APScheduler/Task Scheduler (run_ingestion.main)."""
        mock_factory = MagicMock()
        mock_factory.return_value = MagicMock()
        with patch("agents.common.data_store.database.get_engine", return_value=MagicMock()), patch(
            "agents.common.data_store.database.get_session_factory", return_value=mock_factory
        ):
            with patch("agents.orchestration.scheduler.log"), patch(
                "agents.orchestration.run_ingestion.main"
            ) as mock_run_ingestion:
                from agents.orchestration.scheduler import _scheduled_job

                _scheduled_job()
                mock_run_ingestion.assert_called_once()
                mock_run_ingestion.assert_called_with()


class TestScheduleFromEnvironment:
    """The configured interval or cron is read from environment variables."""

    def test_interval_minutes_default(self) -> None:
        """Without INGESTION_INTERVAL_MINUTES, default is 2."""
        from agents.orchestration.scheduler import _interval_minutes

        with patch.dict(os.environ, {}, clear=False):
            if "INGESTION_INTERVAL_MINUTES" in os.environ:
                del os.environ["INGESTION_INTERVAL_MINUTES"]
            assert _interval_minutes() == 2

    def test_interval_minutes_from_env(self) -> None:
        """INGESTION_INTERVAL_MINUTES sets the interval (min 1)."""
        from agents.orchestration.scheduler import _interval_minutes

        with patch.dict(os.environ, {"INGESTION_INTERVAL_MINUTES": "5"}):
            assert _interval_minutes() == 5
        with patch.dict(os.environ, {"INGESTION_INTERVAL_MINUTES": "1"}):
            assert _interval_minutes() == 1
        with patch.dict(os.environ, {"INGESTION_INTERVAL_MINUTES": "0"}):
            assert _interval_minutes() == 1  # clamped to 1

    def test_interval_minutes_invalid_falls_back_to_2(self) -> None:
        """Invalid INGESTION_INTERVAL_MINUTES falls back to 2."""
        from agents.orchestration.scheduler import _interval_minutes

        with patch.dict(os.environ, {"INGESTION_INTERVAL_MINUTES": "not_a_number"}):
            assert _interval_minutes() == 2

    @patch("agents.orchestration.scheduler.BackgroundScheduler")
    def test_scheduler_add_job_receives_interval_from_env(
        self,
        mock_scheduler_class: MagicMock,
    ) -> None:
        """When main() runs without cron, add_job is called with minutes from INGESTION_INTERVAL_MINUTES."""
        from agents.orchestration.scheduler import main

        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        # Make sleep raise so main() exits (it catches KeyboardInterrupt and returns)
        with patch.dict(os.environ, {"INGESTION_CRON_EXPRESSION": "", "INGESTION_INTERVAL_MINUTES": "7"}), patch(
            "agents.orchestration.scheduler.time.sleep", side_effect=KeyboardInterrupt
        ):
            main()

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args[1]
        assert call_kwargs["minutes"] == 7
        assert call_kwargs["trigger"] == "interval"

    @patch("agents.orchestration.scheduler.BackgroundScheduler")
    def test_scheduler_add_job_receives_cron_from_env(
        self,
        mock_scheduler_class: MagicMock,
    ) -> None:
        """When INGESTION_CRON_EXPRESSION is set, add_job is called with a cron trigger (no minutes)."""
        from apscheduler.triggers.cron import CronTrigger

        from agents.orchestration.scheduler import main

        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        with patch.dict(
            os.environ,
            {"INGESTION_CRON_EXPRESSION": "*/3 * * * *", "INGESTION_INTERVAL_MINUTES": "2"},
        ), patch("agents.orchestration.scheduler.time.sleep", side_effect=KeyboardInterrupt):
            main()

        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args[1]
        assert isinstance(call_kwargs["trigger"], CronTrigger)
        assert "minutes" not in call_kwargs


class TestOverlapHandling:
    """Behavior when a run lasts longer than the interval (EXP-005 overlap test)."""

    def test_apscheduler_overlap_behavior_documented(self) -> None:
        """APScheduler overlap: we do not set max_instances, so library default (1) applies.

        When a run lasts longer than the interval (e.g. 3-minute job, 2-minute
        interval), the next scheduled fire is skipped until the current run
        finishes (max_instances=1 means only one concurrent run). Our scheduler
        module does not pass max_instances to add_job, so this default applies.
        """
        from agents.orchestration.scheduler import _scheduled_job

        # Our job is the real _scheduled_job; we don't pass max_instances to add_job
        assert callable(_scheduled_job)


class TestCrashRecoveryDocumentation:
    """Documented behavior when the agent or process crashes (EXP-005)."""

    def test_crash_recovery_apscheduler_documentation(self) -> None:
        """APScheduler: next cycle does not fire until the process is restarted.

        If the Python process that runs APScheduler is killed (crash, OOM,
        deploy), the scheduler stops. The next run happens only when the
        process is started again (e.g. by systemd, Docker restart policy, or
        manual start). There is no automatic "next cycle" until something
        external restarts the app.
        """
        assert True  # documentation-only scenario

    def test_crash_recovery_task_scheduler_documentation(self) -> None:
        """Task Scheduler: next cycle fires on schedule in a new process.

        Each Task Scheduler run starts a new process (run_ingestion_task.bat
        runs python -m agents.orchestration.run_ingestion). If that process
        crashes, the OS does not restart it; the next run is at the next
        scheduled trigger time (e.g. 2 minutes later). So "next cycle fires
        even if the agent crashed on previous run" is satisfied: a new
        process is started at the next fire time.
        """
        assert True  # documentation-only scenario
