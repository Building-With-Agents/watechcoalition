"""Generate charts from EXP-004 transport comparison CSV for readability."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import structlog

matplotlib.use("Agg")

log = structlog.get_logger()


def _default_csv_path() -> Path:
    return Path(os.getenv("EXP004_COMPARISON_CSV", "agents/data/output/exp004_comparison.csv"))


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse_float(value: str | None) -> float | None:
    if value is None or value.strip() in ("", "N/A"):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_int(value: str | None) -> int | None:
    if value is None or value.strip() in ("", "N/A"):
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    v = value.strip().lower()
    return v in ("true", "1", "yes", "y")


def _transport_label(row: dict[str, str]) -> str:
    t = row.get("transport", "?")
    b = row.get("backend", "")
    return f"{t}\n({b})" if b else t


def _bar_label(
    ax: plt.Axes,
    bar: object,
    value: float | int | None,
    *,
    fmt: str = ".0f",
    text_override: str | None = None,
    fontsize: int = 8,
) -> None:
    """Place a label on top of a bar: exact value or 'N/A'. Use text_override for e.g. 'Passed'/'Failed'."""
    if not hasattr(bar, "get_x"):
        return
    x = bar.get_x() + bar.get_width() / 2
    y = bar.get_height()
    if text_override is not None:
        label = text_override
    elif value is None:
        label = "N/A"
    else:
        label = f"{value:{fmt}}"
    ax.text(x, y, label, ha="center", va="bottom", fontsize=fontsize)


def generate_charts(csv_path: Path | None = None) -> list[Path]:
    """Read EXP-004 comparison CSV and save chart PNGs in the same directory. Returns paths saved."""
    path = csv_path or _default_csv_path()
    if not path.exists():
        return []

    rows = _read_csv_rows(path)
    if not rows:
        return []

    out_dir = path.parent
    labels = [_transport_label(r) for r in rows]
    saved: list[Path] = []

    # --- Throughput (events consumed per second) ---
    e2e = [_parse_float(r.get("throughput_e2e_events_per_sec")) for r in rows]
    if any(x is not None for x in e2e):
        fig, ax = plt.subplots(figsize=(8, 4))
        values = [x if x is not None else 0 for x in e2e]
        colors = ["#2ecc71", "#3498db", "#9b59b6"]
        bars = ax.bar(labels, values, color=colors[: len(labels)])
        ax.set_ylabel("Events per second")
        ax.set_title("Throughput")
        ax.tick_params(axis="x", labelsize=8)
        for bar, v in zip(bars, e2e, strict=False):
            _bar_label(ax, bar, v, fmt=",.0f")
        plt.tight_layout()
        p = out_dir / "exp004_throughput.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        saved.append(p)

    # --- Latency (p50, p95, p99) ---
    p50 = [_parse_float(r.get("latency_p50_ms")) for r in rows]
    p95 = [_parse_float(r.get("latency_p95_ms")) for r in rows]
    p99 = [_parse_float(r.get("latency_p99_ms")) for r in rows]
    if any(x is not None for x in p50 + p95 + p99):
        fig, ax = plt.subplots(figsize=(8, 4))
        xi = range(len(labels))
        w = 0.25
        bars_p50 = ax.bar([i - w for i in xi], [v if v is not None else 0 for v in p50], width=w, label="p50", color="#2ecc71")
        bars_p95 = ax.bar(xi, [v if v is not None else 0 for v in p95], width=w, label="p95", color="#3498db")
        bars_p99 = ax.bar([i + w for i in xi], [v if v is not None else 0 for v in p99], width=w, label="p99", color="#9b59b6")
        for bar, v in zip(bars_p50, p50, strict=False):
            _bar_label(ax, bar, v, fmt=".2f")
        for bar, v in zip(bars_p95, p95, strict=False):
            _bar_label(ax, bar, v, fmt=".2f")
        for bar, v in zip(bars_p99, p99, strict=False):
            _bar_label(ax, bar, v, fmt=".2f")
        ax.set_xticks(list(xi))
        ax.set_xticklabels(labels, fontsize=8)
        ax.set_ylabel("Latency (ms)")
        ax.set_title("Latency")
        ax.legend()
        plt.tight_layout()
        p = out_dir / "exp004_latency.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        saved.append(p)

    # --- Observability: peak queue depth and peak in-flight (during run, not after drain) ---
    queue_depths: list[int | None] = [_parse_int(r.get("queue_depth")) for r in rows]
    max_in_flight_list: list[int | None] = []
    for r in rows:
        v = _parse_int(r.get("max_in_flight")) or _parse_int(r.get("in_flight"))
        max_in_flight_list.append(v)
    fig, ax = plt.subplots(figsize=(8, 4))
    xi = range(len(labels))
    w = 0.35
    off = 0.2
    bars_qd = ax.bar([i - off for i in xi], [x if x is not None else 0 for x in queue_depths], width=w, label="Queue depth (peak)", color="#3498db")
    bars_mif = ax.bar([i + off for i in xi], [x if x is not None else 0 for x in max_in_flight_list], width=w, label="In flight (peak)", color="#9b59b6")
    ax.set_xticks(list(xi))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Count")
    ax.set_title("Queue depth and In flight (peak during run)")
    ax.legend()
    for bar, v in zip(bars_qd, queue_depths, strict=False):
        _bar_label(ax, bar, v)
    for bar, v in zip(bars_mif, max_in_flight_list, strict=False):
        _bar_label(ax, bar, v)
    plt.tight_layout()
    p = out_dir / "exp004_observability.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    saved.append(p)

    # --- Replay count and Replay completeness (replay_count / expected_count × 100) ---
    replay_count = [_parse_int(r.get("replay_count")) for r in rows]
    replay_pct = [_parse_float(r.get("replay_completeness_pct")) for r in rows]
    if any(x is not None for x in replay_count + replay_pct):
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        counts = [x if x is not None else 0 for x in replay_count]
        bars1 = ax1.bar(labels, counts, color="#3498db")
        ax1.set_ylabel("Count")
        ax1.set_title("Replay count")
        ax1.tick_params(axis="x", labelsize=8)
        for bar, v in zip(bars1, replay_count, strict=False):
            _bar_label(ax1, bar, v)
        pcts = [x if x is not None else 0 for x in replay_pct]
        bars2 = ax2.bar(labels, pcts, color="#9b59b6")
        ax2.set_ylabel("Percent")
        ax2.set_title("Replay completeness (replay_count / expected_count × 100)")
        ax2.tick_params(axis="x", labelsize=8)
        ax2.set_ylim(0, 105)
        for bar, v in zip(bars2, replay_pct, strict=False):
            _bar_label(ax2, bar, v, fmt=".1f")
        plt.tight_layout()
        p = out_dir / "exp004_replay.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        saved.append(p)

    # --- Correlation ID propagation ---
    corr_key = "correlation_id_propagation_passed"
    if rows and corr_key not in rows[0]:
        corr_key = "correctness_passed"
    passed = [_parse_bool(r.get(corr_key)) for r in rows]
    vals = [1 if x else 0 for x in passed]
    fig, ax = plt.subplots(figsize=(8, 4))
    colors_corr = ["#2ecc71" if x else "#e74c3c" for x in passed]
    bars = ax.bar(labels, vals, color=colors_corr)
    ax.set_ylabel("Passed (1) / Failed (0)")
    ax.set_title("Correlation ID propagation")
    ax.set_ylim(0, 1.2)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Failed", "Passed"])
    ax.tick_params(axis="x", labelsize=8)
    for bar, p in zip(bars, passed, strict=False):
        _bar_label(ax, bar, 1 if p else 0, text_override="Passed" if p else "Failed")
    plt.tight_layout()
    p = out_dir / "exp004_correlation_id.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    saved.append(p)

    return saved


def main() -> int:
    csv_path = _default_csv_path()
    paths = generate_charts(csv_path)
    if not paths:
        log.warning("no_csv_or_empty", csv_path=str(csv_path), hint="Run run_comparison_and_report first.")
        return 1
    log.info("charts_saved", paths=[str(p) for p in paths])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
