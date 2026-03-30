"""Tests for full pipeline run over Redis Streams.

When REDIS_URL is set, runs the pipeline script and asserts report and metrics shape.
When REDIS_URL is not set, tests are skipped with a clear reason.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = REPO_ROOT / "agents" / "eval"
JSON_REPORT = EVAL_DIR / "full_pipeline_redis_metrics.json"
HTML_REPORT = EVAL_DIR / "full_pipeline_redis_metrics.html"


def _redis_url() -> str | None:
    return os.environ.get("REDIS_URL")


@pytest.mark.skipif(
    not _redis_url(),
    reason="REDIS_URL is not set; set it to run full pipeline over Redis (e.g. redis://localhost:6379/0)",
)
def test_full_pipeline_redis_run_and_report() -> None:
    """Run the Redis pipeline script; assert reports exist and JSON has expected shape."""
    cmd = [
        sys.executable,
        "-m",
        "agents.scripts.run_full_pipeline_redis",
        "--redis-url",
        _redis_url() or "",
    ]
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert result.returncode in (0, 1), (
        f"Script should exit 0 or 1; got {result.returncode}. stdout: {result.stdout} stderr: {result.stderr}"
    )
    assert JSON_REPORT.exists(), (
        f"Expected {JSON_REPORT} to exist. stdout: {result.stdout} stderr: {result.stderr}"
    )
    assert HTML_REPORT.exists(), (
        f"Expected {HTML_REPORT} to exist. stdout: {result.stdout} stderr: {result.stderr}"
    )

    with open(JSON_REPORT, encoding="utf-8") as f:
        data = json.load(f)
    assert "correlation_id" in data
    assert "stages" in data
    assert isinstance(data["stages"], list)
    assert "e2e_latency_ms" in data
    assert "success" in data
    for stage in data["stages"]:
        assert "stage" in stage
        assert "latency_ms" in stage
        assert "success" in stage
