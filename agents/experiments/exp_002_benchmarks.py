from __future__ import annotations

"""
EXP-002 — PostgreSQL baseline benchmarks for the Job Intelligence Engine.

This standalone script measures:
    1. Insert throughput into `raw_ingested_jobs`.
    2. Dedup SELECT latency (median and p99) on `raw_payload_hash`.
    3. Unicode round-trip fidelity for text fields.
    4. Concurrent access behavior under moderate write load.

Results are written to `agents/data/output/exp_002_findings.json` and logged
via structlog. The script is safe to run multiple times and cleans up all
benchmark rows after each test.

Run with:

    PYTHONPATH=. python3 agents/experiments/exp_002_benchmarks.py
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import create_engine, delete, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from agents.common.data_store.models import Base, RawIngestedJob

log = structlog.get_logger()


def _create_engine() -> Engine:
    """
    Construct a SQLAlchemy engine using the PYTHON_DATABASE_URL environment variable.

    The URL is expected to be a PostgreSQL connection string with psycopg2, e.g.:
        postgresql+psycopg2://user:password@host:5432/dbname
    """
    database_url = os.getenv("PYTHON_DATABASE_URL")
    if not database_url:
        raise RuntimeError("PYTHON_DATABASE_URL is not set")

    log.info(
        "exp002_engine_create",
        url_scheme=database_url.split("://", 1)[0],
    )
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    return engine


ENGINE: Engine = _create_engine()
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)

BENCHMARK_SOURCE = "exp_002_benchmark"


def benchmark_insert_throughput(num_rows: int = 1000) -> float:
    """
    Measure bulk insert throughput for raw_ingested_jobs.

    Inserts `num_rows` rows in a single batch and returns rows/second.
    All rows are cleaned up after the measurement.
    """
    ingestion_run_id = "exp_002_insert"

    start = time.perf_counter()
    try:
        with SessionLocal() as session:
            jobs: list[RawIngestedJob] = []
            for i in range(num_rows):
                jobs.append(
                    RawIngestedJob(
                        source=BENCHMARK_SOURCE,
                        external_id=f"exp_insert_{i}",
                        raw_payload_hash=f"exp_insert_hash_{i}",
                        ingestion_run_id=ingestion_run_id,
                        raw_text="benchmark insert throughput",
                        raw_metadata_json={},
                    )
                )
            session.bulk_save_objects(jobs)
            session.commit()
    finally:
        elapsed = max(time.perf_counter() - start, 1e-9)

    rows_per_sec = num_rows / elapsed
    log.info(
        "exp002_insert_throughput",
        rows=num_rows,
        seconds=elapsed,
        rows_per_sec=rows_per_sec,
    )

    # Cleanup benchmark rows for this run.
    with SessionLocal() as session:
        session.execute(
            delete(RawIngestedJob).where(RawIngestedJob.ingestion_run_id == ingestion_run_id)
        )
        session.commit()

    return rows_per_sec


def benchmark_dedup_latency(num_rows: int = 1000) -> tuple[float, float]:
    """
    Measure SELECT latency for dedup checks on raw_payload_hash.

    Inserts `num_rows` rows, then performs one SELECT per row, timing each
    using time.perf_counter(). Returns (median_ms, p99_ms). Cleans up rows
    after measurement.
    """
    ingestion_run_id = "exp_002_dedup"

    with SessionLocal() as session:
        jobs: list[RawIngestedJob] = []
        for i in range(num_rows):
            jobs.append(
                RawIngestedJob(
                    source=BENCHMARK_SOURCE,
                    external_id=f"exp_dedup_{i}",
                    raw_payload_hash=f"exp_dedup_hash_{i}",
                    ingestion_run_id=ingestion_run_id,
                    raw_text="benchmark dedup latency",
                    raw_metadata_json={},
                )
            )
        session.bulk_save_objects(jobs)
        session.commit()

    latencies_ms: list[float] = []
    try:
        with SessionLocal() as session:
            hashes = (
                session.execute(
                    select(RawIngestedJob.raw_payload_hash).where(
                        RawIngestedJob.ingestion_run_id == ingestion_run_id
                    )
                )
                .scalars()
                .all()
            )

            for h in hashes:
                start = time.perf_counter()
                _ = (
                    session.execute(
                        select(RawIngestedJob.id).where(RawIngestedJob.raw_payload_hash == h)
                    )
                    .scalars()
                    .first()
                )
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                latencies_ms.append(elapsed_ms)
    finally:
        with SessionLocal() as session:
            session.execute(
                delete(RawIngestedJob).where(RawIngestedJob.ingestion_run_id == ingestion_run_id)
            )
            session.commit()

    if not latencies_ms:
        return 0.0, 0.0

    latencies_sorted = sorted(latencies_ms)
    mid = len(latencies_sorted) // 2
    if len(latencies_sorted) % 2 == 0:
        median_ms = (latencies_sorted[mid - 1] + latencies_sorted[mid]) / 2.0
    else:
        median_ms = latencies_sorted[mid]

    p99_index = max(int(len(latencies_sorted) * 0.99) - 1, 0)
    p99_ms = latencies_sorted[p99_index]

    log.info(
        "exp002_dedup_latency",
        rows=num_rows,
        median_ms=median_ms,
        p99_ms=p99_ms,
    )

    return median_ms, p99_ms


def benchmark_unicode_roundtrip() -> str:
    """
    Verify that Unicode text round-trips correctly through PostgreSQL.

    Inserts a small set of rows with Unicode content in text fields, reads them
    back, and compares values byte-for-byte. Returns "pass" or "fail".
    """
    ingestion_run_id = "exp_002_unicode"

    samples = [
        {"title": "シニアデータエンジニア", "company": "株式会社AIソリューション", "location": "東京"},
        {"title": "مهندس بيانات", "company": "شركة التقنية الحديثة", "location": "دبي"},
        {"title": "Senior Engineer 🚀", "company": "Emoji Corp 😄", "location": "Seattle 🌧️"},
    ]

    with SessionLocal() as session:
        jobs: list[RawIngestedJob] = []
        for idx, s in enumerate(samples):
            jobs.append(
                RawIngestedJob(
                    source=BENCHMARK_SOURCE,
                    external_id=f"exp_unicode_{idx}",
                    raw_payload_hash=f"exp_unicode_hash_{idx}",
                    ingestion_run_id=ingestion_run_id,
                    raw_text="unicode roundtrip benchmark",
                    raw_metadata_json={
                        "title": s["title"],
                        "company": s["company"],
                        "location": s["location"],
                    },
                )
            )
        session.bulk_save_objects(jobs)
        session.commit()

    try:
        with SessionLocal() as session:
            rows = (
                session.execute(
                    select(RawIngestedJob).where(
                        RawIngestedJob.ingestion_run_id == ingestion_run_id
                    )
                )
                .scalars()
                .all()
            )
    finally:
        with SessionLocal() as session:
            session.execute(
                delete(RawIngestedJob).where(RawIngestedJob.ingestion_run_id == ingestion_run_id)
            )
            session.commit()

    status = "pass"
    if len(rows) != len(samples):
        status = "fail"
    else:
        for row, expected in zip(rows, samples):
            meta = row.raw_metadata_json or {}
            if (
                meta.get("title") != expected["title"]
                or meta.get("company") != expected["company"]
                or meta.get("location") != expected["location"]
            ):
                status = "fail"
                break

    log.info("exp002_unicode_roundtrip", status=status)
    return status


def _concurrent_worker(
    ingestion_run_id: str,
    per_thread: int,
    thread_id: int,
    error_flags: list[str],
) -> None:
    """
    Worker function for concurrent insert benchmark.

    Each worker inserts `per_thread` rows with unique raw_payload_hash values.
    Any exception is recorded in the shared error_flags list.
    """
    try:
        with SessionLocal() as session:
            jobs: list[RawIngestedJob] = []
            for i in range(per_thread):
                jobs.append(
                    RawIngestedJob(
                        source=BENCHMARK_SOURCE,
                        external_id=f"exp_concurrent_{thread_id}_{i}",
                        raw_payload_hash=f"exp_concurrent_hash_{thread_id}_{i}",
                        ingestion_run_id=ingestion_run_id,
                        raw_text="concurrent access benchmark",
                        raw_metadata_json={},
                    )
                )
            session.bulk_save_objects(jobs)
            session.commit()
    except Exception as exc:
        log.error(
            "exp002_concurrent_worker_error",
            thread_id=thread_id,
            error=str(exc),
        )
        error_flags.append(str(exc))


def benchmark_concurrent_access(num_threads: int = 5, per_thread: int = 100) -> str:
    """
    Exercise concurrent inserts into raw_ingested_jobs using multiple threads.

    Spawns `num_threads` threads, each inserting `per_thread` rows. Returns
    "pass" if there are no worker errors and no duplicate raw_payload_hash
    values; otherwise returns "fail". Benchmark rows are cleaned up afterward.
    """
    ingestion_run_id = "exp_002_concurrent"
    errors: list[str] = []
    threads: list[threading.Thread] = []

    for thread_id in range(num_threads):
        t = threading.Thread(
            target=_concurrent_worker,
            args=(ingestion_run_id, per_thread, thread_id, errors),
            daemon=True,
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    status = "pass" if not errors else "fail"
    total_rows_expected = num_threads * per_thread

    try:
        with SessionLocal() as session:
            hashes = (
                session.execute(
                    select(RawIngestedJob.raw_payload_hash).where(
                        RawIngestedJob.ingestion_run_id == ingestion_run_id
                    )
                )
                .scalars()
                .all()
            )
            if len(hashes) != total_rows_expected or len(hashes) != len(set(hashes)):
                status = "fail"
    finally:
        with SessionLocal() as session:
            session.execute(
                delete(RawIngestedJob).where(RawIngestedJob.ingestion_run_id == ingestion_run_id)
            )
            session.commit()

    log.info(
        "exp002_concurrent_access",
        status=status,
        threads=num_threads,
        rows_per_thread=per_thread,
        total_rows_expected=total_rows_expected,
    )
    return status


def main() -> None:
    """
    Run all EXP-002 benchmarks and persist findings to exp_002_findings.json.
    """
    findings: dict[str, Any] = {}

    try:
        insert_rps = benchmark_insert_throughput()
        median_ms, p99_ms = benchmark_dedup_latency()
        unicode_status = benchmark_unicode_roundtrip()
        concurrent_status = benchmark_concurrent_access()
    except SQLAlchemyError as exc:
        log.error("exp002_benchmarks_database_failure", error=str(exc))
        raise
    except Exception as exc:
        log.error("exp002_benchmarks_unexpected_failure", error=str(exc))
        raise

    findings["insert_throughput_rows_per_sec"] = insert_rps
    findings["dedup_median_ms"] = median_ms
    findings["dedup_p99_ms"] = p99_ms
    findings["unicode_roundtrip"] = unicode_status
    findings["concurrent_access"] = concurrent_status

    output_dir = Path(__file__).resolve().parents[1] / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "exp_002_findings.json"
    output_path.write_text(json.dumps(findings, indent=2), encoding="utf-8")

    log.info(
        "exp002_benchmarks_complete",
        output_path=str(output_path),
        findings=findings,
    )


if __name__ == "__main__":
    main()

