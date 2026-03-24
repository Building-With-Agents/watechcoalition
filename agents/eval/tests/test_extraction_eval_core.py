"""Tests for extraction eval core metrics, snapshots, and Mountain Time formatting."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from agents.eval.extraction_eval_core import (
    compute_metrics,
    extract_from_text_testing,
    normalize_tool_label_for_eval,
    now_mountain_iso,
    run_eval_dataset,
)
from agents.eval.snapshot_schema import (
    SNAPSHOT_SCHEMA_VERSION,
    AggregateMetrics,
    ExtractionEvalSnapshot,
    PerJobSnapshot,
    PromptExemplar,
    load_snapshot,
)


def test_compute_metrics_basic() -> None:
    pred = {"python", "java"}
    true = {"python", "sql"}
    p, r = compute_metrics(pred, true)
    assert p == 0.5
    assert r == 0.5


def test_compute_metrics_empty_pred() -> None:
    p, r = compute_metrics(set(), {"a"})
    assert p == 0.0
    assert r == 0.0


def test_stub_extractor_keyword() -> None:
    out = extract_from_text_testing("We need Python and AWS docker experience")
    assert "Python" in out["skills"]
    assert "AWS" in out["tools"]


def test_normalize_tool_label_for_eval_collapses_known_variants() -> None:
    assert normalize_tool_label_for_eval("Microsoft Excel") == "excel"
    assert normalize_tool_label_for_eval("Splunk (ES)") == "splunk"
    assert normalize_tool_label_for_eval("Fortinet Firewalls") == "fortinet"


def test_run_eval_dataset_stub_tiny() -> None:
    data = [
        {
            "ground_truth_id": "t1",
            "title": "Python Engineer",
            "description": "Python and sql required",
            "requirements": "",
            "responsibilities": "",
            "skills": [{"skill_name": "Python"}],
            "tools": [{"tool_name": "Python"}],
        }
    ]
    result = run_eval_dataset(
        data,
        mode="stub",
        ground_truth_path="/tmp/gt.json",
        run_label="test",
        write_artifacts=False,
    )
    assert result.snapshot.record_count == 1
    assert result.snapshot.extractor_mode == "stub"
    assert result.snapshot.aggregates.llm_applicable is False
    assert result.snapshot.aggregates.matched_skills >= 0


def test_snapshot_round_trip(tmp_path: Path) -> None:
    snap = ExtractionEvalSnapshot(
        mt_timestamp_iso="2026-01-01T12:00:00-07:00",
        ground_truth_path="/x/gt.json",
        record_count=1,
        extractor_mode="stub",
        aggregates=AggregateMetrics(
            total_gt_skills=1,
            total_pred_skills=1,
            matched_skills=1,
            precision_skills=1.0,
            recall_skills=1.0,
            total_gt_tools=0,
            total_pred_tools=0,
            matched_tools=0,
            precision_tools=0.0,
            recall_tools=0.0,
            llm_applicable=False,
        ),
        per_job=[
            PerJobSnapshot(
                job_key="t1",
                title="T",
                gt_skills=["python"],
                pred_skills=["python"],
            )
        ],
        prompt_exemplar=PromptExemplar(
            skills_prompt_version="v1",
            system_prompt="sys",
            user_prompt="user",
        ),
    )
    p = tmp_path / "s.json"
    p.write_text(json.dumps(snap.model_dump(mode="json")), encoding="utf-8")
    loaded = load_snapshot(p)
    assert loaded.schema_version == SNAPSHOT_SCHEMA_VERSION
    assert loaded.per_job[0].job_key == "t1"
    assert loaded.prompt_exemplar is not None
    assert loaded.prompt_exemplar.system_prompt == "sys"


def test_now_mountain_iso_contains_offset() -> None:
    s = now_mountain_iso()
    assert "T" in s


def test_now_mountain_iso_fixed_clock() -> None:
    fixed = datetime(2024, 7, 15, 6, 30, 0, tzinfo=ZoneInfo("America/Denver"))
    with patch("agents.eval.extraction_eval_core.datetime") as mock_dt:
        mock_dt.now.return_value = fixed
        out = now_mountain_iso()
    mock_dt.now.assert_called_once()
    assert out == fixed.isoformat(timespec="seconds")
