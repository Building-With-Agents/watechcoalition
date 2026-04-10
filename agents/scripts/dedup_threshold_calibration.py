# ruff: noqa: T201
"""Generate fuzzy dedup threshold-calibration outputs from labeled pair cases.

Usage (repo root, with Azure embedding env vars in the repo-root ``.env``)::

    ./agents/.venv/bin/python -m agents.scripts.dedup_threshold_calibration
    ./agents/.venv/bin/python -m agents.scripts.dedup_threshold_calibration \
      --thresholds 0.88,0.90,0.92,0.94,0.96
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from agents.common.env import load_repo_root_dotenv  # noqa: E402
from agents.enrichment.dedup.calibration import (  # noqa: E402
    DEFAULT_CALIBRATION_AUDIT_AGENT,
    generate_calibration_report,
    load_calibration_cases,
    parse_thresholds,
    render_findings_markdown,
)
from agents.enrichment.dedup.config import dedup_cosine_threshold  # noqa: E402

load_repo_root_dotenv()

_DEFAULT_CASES_PATH = _REPO_ROOT / "agents" / "eval" / "dedup_threshold_calibration_cases.json"
_DEFAULT_REPORT_PATH = _REPO_ROOT / "agents" / "data" / "reports" / "dedup_threshold_calibration.json"
_DEFAULT_FINDINGS_PATH = _REPO_ROOT / "agents" / "docs" / "week 6" / "FINDINGS-fuzzy-dedup-bryan-emilio.md"


def _repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(_REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate fuzzy dedup threshold calibration report")
    parser.add_argument(
        "--cases",
        default=str(_DEFAULT_CASES_PATH),
        help="Input JSON file with labeled pair cases",
    )
    parser.add_argument(
        "--report-output",
        default=str(_DEFAULT_REPORT_PATH),
        help="Output JSON report path",
    )
    parser.add_argument(
        "--findings-output",
        default=str(_DEFAULT_FINDINGS_PATH),
        help="Output Markdown findings path",
    )
    parser.add_argument(
        "--thresholds",
        default=",".join(f"{value:.2f}" for value in (0.88, 0.90, 0.92, 0.94, 0.96)),
        help="Comma-separated cosine thresholds to evaluate",
    )
    parser.add_argument(
        "--audit-agent-name",
        default=DEFAULT_CALIBRATION_AUDIT_AGENT,
        help="agent_name written to llm_audit_log by the shared embedding helper",
    )
    args = parser.parse_args()

    cases_path = Path(args.cases)
    report_path = Path(args.report_output)
    findings_path = Path(args.findings_output)

    cases = load_calibration_cases(cases_path)
    default_threshold = dedup_cosine_threshold()
    thresholds = parse_thresholds(args.thresholds, default_threshold=default_threshold)
    report = generate_calibration_report(
        cases,
        source_path=_repo_relative(cases_path),
        thresholds=thresholds,
        default_threshold=default_threshold,
        audit_agent_name=args.audit_agent_name,
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")

    findings_path.parent.mkdir(parents=True, exist_ok=True)
    findings_path.write_text(render_findings_markdown(report), encoding="utf-8")

    default_summary = report.summary_for_threshold(report.default_threshold)
    print(f"Wrote JSON report: {report_path.resolve()}")
    print(f"Wrote findings doc: {findings_path.resolve()}")
    print(
        "Default threshold "
        f"{report.default_threshold:.2f}: TP={default_summary.true_positive}, "
        f"FP={default_summary.false_positive}, TN={default_summary.true_negative}, "
        f"FN={default_summary.false_negative}, "
        f"FPR={default_summary.false_positive_rate:.3f}, "
        f"FNR={default_summary.false_negative_rate:.3f}"
    )


if __name__ == "__main__":
    main()
