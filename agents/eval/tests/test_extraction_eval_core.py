"""Tests for extraction eval core metrics, snapshots, and Mountain Time formatting."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from agents.common.types import ContextSignal
from agents.common.types.extraction_types import SpanRecord
from agents.eval.extraction_eval_core import (
    EVAL_DIMENSIONS,
    canonical_context_label,
    canonicalize_context_signal_type_for_eval,
    compute_metrics,
    extract_from_text_testing,
    f1_from_precision_recall,
    ground_truth_context_labels,
    ground_truth_responsibility_labels,
    ground_truth_task_labels,
    normalize_tool_label_for_eval,
    now_mountain_iso,
    prediction_context_labels_from_signals,
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
    p, r, f1 = compute_metrics(pred, true)
    assert p == 0.5
    assert r == 0.5
    assert f1 == 0.5


def test_compute_metrics_empty_pred() -> None:
    p, r, f1 = compute_metrics(set(), {"a"})
    assert p == 0.0
    assert r == 0.0
    assert f1 == 0.0


def test_compute_metrics_perfect_overlap_f1_one() -> None:
    pred = {"a", "b"}
    true = {"a", "b"}
    p, r, f1 = compute_metrics(pred, true)
    assert p == 1.0
    assert r == 1.0
    assert f1 == 1.0


def test_f1_from_precision_recall_edge_cases() -> None:
    assert f1_from_precision_recall(0.0, 0.0) == 0.0
    assert f1_from_precision_recall(0.5, 0.5) == 0.5


def test_ground_truth_task_labels_from_task_description() -> None:
    job = {
        "tasks": [
            {"task_description": "Ship the roadmap"},
            {"task_description": ""},
            {"not_task": "x"},
        ]
    }
    assert ground_truth_task_labels(job) == {"ship the roadmap"}


def test_ground_truth_responsibility_labels_from_labeled_responsibilities() -> None:
    job = {
        "labeled_responsibilities": [
            {"responsibility_description": "Own the data platform"},
            {"responsibility_description": None},
        ]
    }
    assert ground_truth_responsibility_labels(job) == {"own the data platform"}


def test_eval_dimensions_taxonomy_coverage_only_on_skills() -> None:
    by_key = {d.key: d.taxonomy_coverage for d in EVAL_DIMENSIONS}
    assert by_key["skills"] is True
    assert by_key["tools"] is False
    assert by_key["tasks"] is False
    assert by_key["responsibilities"] is False
    assert by_key["context"] is False


def test_canonicalize_context_signal_type_ai_usage_alias() -> None:
    assert canonicalize_context_signal_type_for_eval("ai_usage") == "ai_adoption_signal"
    assert canonicalize_context_signal_type_for_eval("growth_stage") == "growth_stage"


def test_canonical_context_label_uses_alias_and_value() -> None:
    assert canonical_context_label("ai_usage", "Foo  bar") == "ai_adoption_signal|foo bar"


def test_prediction_context_labels_from_signals() -> None:
    span = SpanRecord(text="remote", field_source="description", start_char=0, end_char=6)
    sig = ContextSignal(
        signal_type="remote_policy",
        value="Remote",
        confidence=0.9,
        source_span=span,
    )
    assert prediction_context_labels_from_signals([sig]) == {"remote_policy|remote"}


def test_ground_truth_context_labels_canonicalizes_signal_type() -> None:
    job = {
        "context": [
            {"signal_type": "ai_usage", "value": "x"},
            {"signal_type": "growth_stage", "value": "startup"},
        ]
    }
    assert ground_truth_context_labels(job) == {
        "ai_adoption_signal|x",
        "growth_stage|startup",
    }


def test_stub_extractor_keyword() -> None:
    out = extract_from_text_testing("We need Python and AWS docker experience")
    assert "Python" in out["skills"]
    assert "AWS" in out["tools"]
    assert out["tasks"] == []
    assert out["responsibilities"] == []
    assert out["context"] == []


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


def test_run_eval_dataset_stub_five_dimensions_gt_and_aggregates() -> None:
    """Stub has no preds for tasks/responsibilities/context; GT still drives counts and P/R/F1."""
    data = [
        {
            "ground_truth_id": "multi",
            "title": "Engineer",
            "description": "Python aws",
            "requirements": "",
            "responsibilities": "",
            "skills": [{"skill_name": "Python"}],
            "tools": [{"tool_name": "AWS"}],
            "tasks": [{"task_description": "Build APIs"}],
            "labeled_responsibilities": [{"responsibility_description": "Own reliability"}],
            "context": [{"signal_type": "ai_usage", "value": "Uses LLMs"}],
        }
    ]
    result = run_eval_dataset(
        data,
        mode="stub",
        ground_truth_path="/tmp/gt.json",
        run_label="multi-dim",
        write_artifacts=False,
    )
    ag = result.snapshot.aggregates
    pj = result.snapshot.per_job[0]

    assert ag.total_gt_tasks == 1
    assert ag.total_pred_tasks == 0
    assert ag.matched_tasks == 0
    assert ag.precision_tasks == 0.0
    assert ag.recall_tasks == 0.0
    assert ag.f1_tasks == 0.0

    assert ag.total_gt_responsibilities == 1
    assert ag.total_pred_responsibilities == 0
    assert ag.f1_responsibilities == 0.0

    assert ag.total_gt_context == 1
    assert ag.total_pred_context == 0
    assert ag.f1_context == 0.0

    assert pj.gt_tasks == ["build apis"]
    assert pj.pred_tasks == []
    assert pj.gt_responsibilities == ["own reliability"]
    assert pj.pred_responsibilities == []
    assert pj.gt_context == ["ai_adoption_signal|uses llms"]
    assert pj.pred_context == []

    assert ag.skills_esco_coverage is None
    assert ag.skills_pred_record_count is None


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
