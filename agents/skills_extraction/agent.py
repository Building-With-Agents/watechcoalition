"""
Skills Extraction Agent (Work Intelligence Agent) — Week 5 six-dimension extraction.

Pass 1: ``extract_context`` (regex, zero LLM tokens), ``extract_tools`` (pattern catalog).
Pass 2: ``extract_tasks`` (Haiku-tier deployment), ``extract_responsibilities`` (Sonnet-tier
deployment), ``extract_skills`` (skills deployment). Pass 1 context signals are injected
into task and responsibility prompts.

Current execution model:
- ``SKILLS_EXTRACTION_PARALLEL=1`` (default): tasks, responsibilities, and skills run
  concurrently within each job via ``asyncio.gather``, and multiple jobs run concurrently
  within a batch up to ``SKILLS_EXTRACTION_CONCURRENCY`` (default: ``5``).
- Tune ``SKILLS_EXTRACTION_CONCURRENCY`` down (for example ``3``) if the deployment starts
  rate limiting aggressively, or up (for example ``8``) if Azure capacity allows it.
- ``SKILLS_EXTRACTION_PARALLEL=0``: fall back to the legacy synchronous per-dimension flow.
- If ``process()`` is called from a thread that already has a running event loop, the agent
  logs a warning and falls back to the serial path to preserve the synchronous caller contract.
  Async hosts (FastAPI, async tests, etc.) should call ``process_async()`` instead to always
  get the full parallel speedup without the event-loop detection fallback.
- ``SKILLS_EXTRACTION_CHUNK_SIZE``, ``SKILLS_EXTRACTION_CHUNK_COOLDOWN``, and
  ``SKILLS_EXTRACTION_DELAY`` are deprecated and only applied in serial fallback mode.

Input modes (in order):
1. Inline normalized records on the event payload
2. Batch load from ``dbo.normalized_jobs`` by ``batch_id`` / ``ingestion_run_id``
3. Legacy ``posting_id`` fixture fallback for walking-skeleton tests
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from collections.abc import Sequence
from contextlib import nullcontext, suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.llm_adapter import get_tracer

log = structlog.get_logger()

from agents.common.data_store import check_db_connection, session_scope
from agents.common.data_store.models import ExtractedIntelligence, NormalizedJob
from agents.common.event_envelope import EventEnvelope
from agents.common.types import ExtractionMetadata, JobRecord, ToolRecord
from agents.skills_extraction.extractors import (
    extract_context,
    extract_responsibilities,
    extract_responsibilities_async,
    extract_tasks,
    extract_tasks_async,
    extract_tools,
)
from agents.skills_extraction.extractors.skills import (
    apply_taxonomy_to_skills,
    extract_skills_no_taxonomy,
    extract_skills_no_taxonomy_async,
)
from agents.skills_extraction.extractors.taxonomy import resolve_taxonomy_batch
from agents.skills_extraction.prompts import SKILLS_PROMPT_VERSION
from agents.skills_extraction.validator import validate_extraction_result

_FIXTURE_PATH = (
    Path(__file__).parent.parent / "data" / "fixtures" / "fixture_skills_extracted.json"
)
EXTRACTION_PASS1_LABEL = "pattern-context-tools-v1"
EXTRACTION_VERSION = f"week5-six-dim-{SKILLS_PROMPT_VERSION}"
FIXTURE_EXTRACTION_MODEL = "fixture-week2-skills"
_DEFAULT_SKILLS_EXTRACTION_CONCURRENCY = 5
# Deprecated serial-only throttles. Keep env compatibility for callers that still run the
# legacy serial path by setting SKILLS_EXTRACTION_PARALLEL=0 or by hitting loop fallback mode.
_DEFAULT_CHUNK_SIZE = 5
_DEFAULT_CHUNK_COOLDOWN = 30.0
_DEFAULT_INTER_LLM_DELAY = 1.0
_DEPRECATED_SERIAL_THROTTLE_ENV_KEYS = (
    "SKILLS_EXTRACTION_CHUNK_SIZE",
    "SKILLS_EXTRACTION_CHUNK_COOLDOWN",
    "SKILLS_EXTRACTION_DELAY",
)
_DEPRECATED_SERIAL_THROTTLE_WARNING_LOCK = threading.Lock()
_DEPRECATED_SERIAL_THROTTLE_WARNING_EMITTED = False
_EXTRACTION_STORE_SAVE_LOCK = threading.Lock()


def _llm_deployment_name() -> str:
    """Azure deployment used for Pass 2 (for dbo.extracted_intelligence.extraction_model)."""
    return (
        os.getenv("EXTRACTION_DEPLOYMENT_SKILLS")
        or os.getenv("EXTRACTION_MODEL_SKILLS")
        or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        or "azure-openai"
    )


def _parallel_enabled() -> bool:
    """Return True when intra-job async extraction is enabled."""
    value = os.getenv("SKILLS_EXTRACTION_PARALLEL", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _env_int(name: str, default: int, *, minimum: int | None = None) -> int:
    """Parse an integer env var with logging and sane fallback behavior."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        log.warning(
            "skills_extraction_invalid_env_int",
            env_var=name,
            raw_value=raw,
            fallback=default,
        )
        return default
    if minimum is not None and value < minimum:
        log.warning(
            "skills_extraction_env_int_below_min",
            env_var=name,
            raw_value=raw,
            minimum=minimum,
            fallback=default,
        )
        return default
    return value


def _env_float(name: str, default: float, *, minimum: float | None = None) -> float:
    """Parse a float env var with logging and sane fallback behavior."""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        log.warning(
            "skills_extraction_invalid_env_float",
            env_var=name,
            raw_value=raw,
            fallback=default,
        )
        return default
    if minimum is not None and value < minimum:
        log.warning(
            "skills_extraction_env_float_below_min",
            env_var=name,
            raw_value=raw,
            minimum=minimum,
            fallback=default,
        )
        return default
    return value


def _parallel_concurrency() -> int:
    """Return the configured max concurrent jobs for inter-job extraction."""
    return _env_int(
        "SKILLS_EXTRACTION_CONCURRENCY",
        _DEFAULT_SKILLS_EXTRACTION_CONCURRENCY,
        minimum=1,
    )


def _serial_chunk_size() -> int:
    """Deprecated serial-only chunk size used when parallel mode is unavailable."""
    return _env_int("SKILLS_EXTRACTION_CHUNK_SIZE", _DEFAULT_CHUNK_SIZE, minimum=0)


def _serial_chunk_cooldown() -> float:
    """Deprecated serial-only chunk cooldown used when parallel mode is unavailable."""
    return _env_float(
        "SKILLS_EXTRACTION_CHUNK_COOLDOWN",
        _DEFAULT_CHUNK_COOLDOWN,
        minimum=0.0,
    )


def _serial_inter_job_delay() -> float:
    """Deprecated serial-only per-job delay used when parallel mode is unavailable."""
    return _env_float(
        "SKILLS_EXTRACTION_DELAY",
        _DEFAULT_INTER_LLM_DELAY,
        minimum=0.0,
    )


def _warn_parallel_deprecated_serial_throttles() -> None:
    """Warn once when deprecated serial-only throttle env vars are set in parallel mode."""
    configured = [
        name
        for name in _DEPRECATED_SERIAL_THROTTLE_ENV_KEYS
        if os.getenv(name) not in (None, "")
    ]
    if not configured:
        return

    global _DEPRECATED_SERIAL_THROTTLE_WARNING_EMITTED
    with _DEPRECATED_SERIAL_THROTTLE_WARNING_LOCK:
        if _DEPRECATED_SERIAL_THROTTLE_WARNING_EMITTED:
            return
        _DEPRECATED_SERIAL_THROTTLE_WARNING_EMITTED = True

    log.warning(
        "skills_extraction_parallel_ignores_serial_throttles",
        ignored_env_vars=configured,
    )


def _persisted_extraction_model_llm() -> str:
    """Stable label: Pass 1 strategy + Pass 2 deployment + prompt version."""
    return (
        f"pass1={EXTRACTION_PASS1_LABEL};"
        f"pass2={_llm_deployment_name()};"
        f"prompt={SKILLS_PROMPT_VERSION}"
    )


@dataclass(frozen=True)
class ExtractionWorkItem:
    """One normalized job record ready for Pass 1 / Pass 2 processing."""

    job_id: int | str | None
    posting_id: int | None
    normalized_job_id: int | None
    title: str
    company: str
    job_record: JobRecord


@dataclass(frozen=True)
class ExtractionResult:
    """One extraction result emitted by the Work Intelligence / skills extraction agent."""

    work_item: ExtractionWorkItem
    skills: list[dict[str, Any]]
    tools: list[ToolRecord]
    seniority: str | None
    extraction_status: str
    tasks: list[dict[str, Any]] = field(default_factory=list)
    responsibilities: list[dict[str, Any]] = field(default_factory=list)
    context: list[dict[str, Any]] = field(default_factory=list)
    extraction_tokens_used: int = 0
    extraction_cost_usd: float = 0.0
    alert_skills_extraction: bool = False
    extraction_warnings: tuple[str, ...] = field(default_factory=tuple)
    extraction_metadata: dict[str, Any] | None = None
    persisted_extraction_version: str = EXTRACTION_VERSION
    persisted_extraction_model: str = FIXTURE_EXTRACTION_MODEL


@dataclass(frozen=True)
class PendingExtraction:
    """One in-memory extraction result prior to taxonomy application and persistence."""

    item: ExtractionWorkItem
    tools: list[ToolRecord]
    skills_list: list[Any]
    meta: dict[str, Any]
    wall_clock_ms: int = 0


class WorkItemLoader(Protocol):
    """Loads normalized work items for the agent from events or storage."""

    def load(self, event: EventEnvelope) -> list[ExtractionWorkItem]:
        """Resolve extraction work items for the given event."""


class ExtractionStore(Protocol):
    """Persists extraction results for downstream retrieval."""

    def save(self, results: Sequence[ExtractionResult]) -> None:
        """Persist extracted intelligence records."""


class EventOrDatabaseWorkItemLoader:
    """Resolve normalized records from inline payloads first, then the DB."""

    def load(self, event: EventEnvelope) -> list[ExtractionWorkItem]:
        payload = event.payload
        batch_id = _string_value(payload.get("batch_id"))

        inline_records = (
            payload.get("normalized_jobs")
            or payload.get("jobs")
            or payload.get("job_records")
        )
        if isinstance(inline_records, list):
            items = [
                item
                for record in inline_records
                if isinstance(record, dict)
                for item in [self._from_mapping(record, batch_id=batch_id)]
                if item is not None
            ]
            if items:
                return items

        inline_item = self._from_mapping(payload, batch_id=batch_id)
        if inline_item is not None:
            return [inline_item]

        if batch_id and check_db_connection():
            return self._from_database(batch_id)

        # FIFO: load normalized records not yet extracted (processing loop mode)
        if check_db_connection():
            batch_size = int(os.environ.get("NORM_BATCH_SIZE", "50"))
            return self._from_database_unextracted(batch_size)

        return []

    def _from_database(self, batch_id: str) -> list[ExtractionWorkItem]:
        """Load normalized jobs by ingestion_run_id for real batch execution."""
        with session_scope() as session:
            rows = (
                session.query(NormalizedJob)
                .filter(NormalizedJob.ingestion_run_id == batch_id)
                .order_by(NormalizedJob.id)
                .all()
            )

        return [self._from_normalized_row(row) for row in rows]

    def _from_database_unextracted(self, limit: int = 50) -> list[ExtractionWorkItem]:
        """FIFO: load normalized jobs that don't yet have extraction results."""
        with session_scope() as session:
            rows = (
                session.query(NormalizedJob)
                .outerjoin(
                    ExtractedIntelligence,
                    NormalizedJob.id == ExtractedIntelligence.normalized_job_id,
                )
                .filter(ExtractedIntelligence.id == None)  # noqa: E711
                .order_by(NormalizedJob.id.asc())
                .limit(limit)
                .all()
            )
        return [self._from_normalized_row(row) for row in rows]

    def _from_normalized_row(self, row: NormalizedJob) -> ExtractionWorkItem:
        """Convert a NormalizedJob ORM row into a work item."""
        job_record = JobRecord(
            raw_job_id=row.raw_job_id or 0,
            ingestion_run_id=row.ingestion_run_id,
            region_id=row.region_id or "",
            source=row.source,
            external_id=row.external_id,
            title=row.title,
            company=row.company,
            description=row.description,
            requirements=row.requirements,
            responsibilities=row.responsibilities,
            job_url=row.job_url,
            city=row.city,
            state_province=row.state_province,
            country=row.country,
            work_arrangement=row.work_arrangement,
            is_remote=row.is_remote,
            date_posted=row.date_posted,
            salary_raw=row.salary_raw,
            salary_min=row.salary_min,
            salary_max=row.salary_max,
            salary_currency=row.salary_currency,
            salary_period=row.salary_period,
            employment_type=row.employment_type,
            experience_level=row.experience_level,
            occupation_code=row.occupation_code,
            mapper_used=row.mapper_used or "",
        )
        return ExtractionWorkItem(
            job_id=row.id,
            posting_id=None,
            normalized_job_id=row.id,
            title=row.title,
            company=row.company,
            job_record=job_record,
        )

    def _from_mapping(
        self,
        mapping: dict[str, Any],
        *,
        batch_id: str | None,
    ) -> ExtractionWorkItem | None:
        """Convert an inline payload or normalized_jobs entry into a work item."""
        title = _string_value(mapping.get("title"))
        company = _string_value(mapping.get("company"))
        if not title or not company:
            return None

        posting_id = _int_value(mapping.get("posting_id"))
        normalized_job_id = _int_value(mapping.get("normalized_job_id"))
        if normalized_job_id is None and posting_id is None:
            normalized_job_id = _int_value(mapping.get("id"))

        external_id = str(
            mapping.get("external_id")
            or posting_id
            or normalized_job_id
            or title.casefold().replace(" ", "-")
        )
        description = _string_value(mapping.get("description")) or _string_value(mapping.get("raw_text"))
        requirements = _string_value(mapping.get("requirements"))
        responsibilities = _string_value(mapping.get("responsibilities"))

        job_record = JobRecord(
            raw_job_id=_int_value(mapping.get("raw_job_id")) or 0,
            ingestion_run_id=_string_value(mapping.get("ingestion_run_id")) or batch_id or "",
            region_id=_string_value(mapping.get("region_id")) or "",
            source=_string_value(mapping.get("source")) or "normalization-event",
            external_id=external_id,
            title=title,
            company=company,
            description=description,
            requirements=requirements,
            responsibilities=responsibilities,
            job_url=_string_value(mapping.get("job_url")) or _string_value(mapping.get("url")),
            employment_type=_string_value(mapping.get("employment_type")),
        )

        return ExtractionWorkItem(
            job_id=posting_id or normalized_job_id or external_id,
            posting_id=posting_id,
            normalized_job_id=normalized_job_id,
            title=title,
            company=company,
            job_record=job_record,
        )


class SQLAlchemyExtractionStore:
    """Persist extracted intelligence rows using the canonical ORM models."""

    def save(self, results: Sequence[ExtractionResult]) -> None:
        if not results:
            log.warning("extraction_store_save_skip_empty_results")
            return
        if not check_db_connection():
            log.error("extraction_store_save_skip_no_db", result_count=len(results))
            return

        acquired = _EXTRACTION_STORE_SAVE_LOCK.acquire(blocking=False)
        if not acquired:
            log.warning(
                "extraction_store_save_waiting_for_lock",
                result_count=len(results),
            )
            _EXTRACTION_STORE_SAVE_LOCK.acquire()

        try:
            saved = 0
            skipped_no_id = 0
            with session_scope() as session:
                for result in results:
                    normalized_job_id = result.work_item.normalized_job_id
                    if normalized_job_id is None:
                        skipped_no_id += 1
                        log.warning(
                            "extraction_store_skip_no_normalized_job_id",
                            job_id=result.work_item.job_id,
                            title=result.work_item.title[:80] if result.work_item.title else "",
                        )
                        continue

                    existing_rows = (
                        session.query(ExtractedIntelligence)
                        .filter(ExtractedIntelligence.normalized_job_id == normalized_job_id)
                        .order_by(ExtractedIntelligence.id)
                        .all()
                    )
                    row = existing_rows[0] if existing_rows else ExtractedIntelligence(
                        normalized_job_id=normalized_job_id,
                        extraction_version=EXTRACTION_VERSION,
                        extraction_model=FIXTURE_EXTRACTION_MODEL,
                    )
                    if not existing_rows:
                        session.add(row)
                    for duplicate in existing_rows[1:]:
                        session.delete(duplicate)

                    row.extraction_version = result.persisted_extraction_version
                    row.extraction_model = result.persisted_extraction_model
                    row.extraction_tokens_used = getattr(result, "extraction_tokens_used", 0) or 0
                    row.extraction_cost_usd = getattr(result, "extraction_cost_usd", 0.0) or 0.0
                    row.skills = result.skills
                    row.tools = [tool.model_dump() for tool in result.tools]
                    row.tasks = list(getattr(result, "tasks", []) or [])
                    row.responsibilities = list(getattr(result, "responsibilities", []) or [])
                    row.context = list(getattr(result, "context", []) or [])
                    validated = validate_extraction_result(
                        result.skills, [tool.model_dump() for tool in result.tools]
                    )
                    row.extraction_warnings = list(
                        dict.fromkeys([*list(result.extraction_warnings), *validated])
                    )
                    row.overall_confidence = _overall_extraction_confidence(result)
                    # Degraded = partial LLM failure (e.g. tasks) but skills OK — not a hard failure.
                    row.extraction_failed = result.extraction_status == "failed"
                    em = result.extraction_metadata
                    row.extraction_metadata = em if isinstance(em, dict) else None
                    saved += 1

            log.info(
                "extraction_store_save_complete",
                saved=saved,
                skipped_no_normalized_job_id=skipped_no_id,
                total=len(results),
            )
        finally:
            _EXTRACTION_STORE_SAVE_LOCK.release()


class SkillsExtractionAgent(BaseAgent):
    """
    Skills Extraction Agent — Week 5 six-dimension (context, tools, tasks,
    responsibilities, skills).

    Normalized text present: Pass 1 context + tools, then Pass 2 LLM dimensions;
    persists to dbo.extracted_intelligence when ``normalized_job_id`` is set;
    emits ``SkillsExtracted``.
    No normalized text: falls back to Week 2 fixture by ``posting_id`` when available.
    """

    @property
    def agent_id(self) -> str:
        return "skills-extraction-agent"

    def __init__(
        self,
        *,
        work_item_loader: WorkItemLoader | None = None,
        extraction_store: ExtractionStore | None = None,
    ) -> None:
        self._fixture: dict[int, dict] = {}
        self._work_item_loader = work_item_loader or EventOrDatabaseWorkItemLoader()
        self._extraction_store = extraction_store or SQLAlchemyExtractionStore()

    def health_check(self) -> dict:
        """Report readiness for both fixture fallback and DB-backed batch mode."""
        fixture_ok = self._load_fixture()
        db_ok = check_db_connection()

        if fixture_ok and db_ok:
            status = "ok"
        elif fixture_ok or db_ok:
            status = "degraded"
        else:
            status = "down"

        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {
                "fixture_loaded": fixture_ok,
                "db_reachable": db_ok,
            },
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept a NormalizationComplete event and emit a SkillsExtracted event.

        Pass 1 (tools) always runs. Pass 2 (skills) runs when normalized job text
        exists; otherwise fixture fallback by posting_id when configured.
        """
        self._load_fixture()

        work_items = self._work_item_loader.load(event)
        if not work_items:
            return self._legacy_fixture_response(event)

        # Cap work items per run (0 = no limit; set SKILLS_EXTRACTION_MAX_JOBS to override)
        try:
            max_jobs = int(os.environ.get("SKILLS_EXTRACTION_MAX_JOBS", "0"))
        except (TypeError, ValueError):
            max_jobs = 0
        if max_jobs > 0 and len(work_items) > max_jobs:
            work_items = work_items[:max_jobs]

        parallel_enabled = _parallel_enabled()
        concurrency = _parallel_concurrency() if parallel_enabled else 1
        if parallel_enabled:
            _warn_parallel_deprecated_serial_throttles()
            log.info(
                "skills_extraction_parallel_start",
                total_jobs=len(work_items),
                concurrency=concurrency,
                parallel_enabled=True,
            )
        else:
            log.info(
                "skills_extraction_serial_start",
                total_jobs=len(work_items),
                parallel_enabled=False,
                chunk_size=_serial_chunk_size(),
                chunk_cooldown_seconds=_serial_chunk_cooldown(),
                inter_job_delay_seconds=_serial_inter_job_delay(),
            )

        batch_start = time.perf_counter()
        if parallel_enabled:
            pending = self._extract_batch_parallel_bridge(
                work_items,
                concurrency=concurrency,
                correlation_id=event.correlation_id,
            )
        else:
            pending = self._extract_batch_serial(
                work_items,
                correlation_id=event.correlation_id,
            )
        batch_wall_clock_ms = int((time.perf_counter() - batch_start) * 1000)

        # Phase 2: Batch taxonomy resolution — single API call for all labels
        all_labels: list[str] = []
        seen_labels: set[str] = set()
        for pending_result in pending:
            for s in pending_result.skills_list:
                if s.skill_name not in seen_labels:
                    seen_labels.add(s.skill_name)
                    all_labels.append(s.skill_name)

        taxonomy_map: dict[str, Any] = {}
        if all_labels:
            import structlog as _structlog
            _log = _structlog.get_logger()
            _log.info(
                "taxonomy_batch_resolve",
                unique_labels=len(all_labels),
                total_jobs=len(pending),
            )
            taxonomy_results = resolve_taxonomy_batch(all_labels)
            taxonomy_map = dict(zip(all_labels, taxonomy_results, strict=True))

        # Phase 3: Apply taxonomy + build results
        results = []
        for pending_result in pending:
            item = pending_result.item
            tools = pending_result.tools
            skills_list = pending_result.skills_list
            meta = pending_result.meta
            if skills_list:
                skills_list = apply_taxonomy_to_skills(skills_list, taxonomy_map)
            results.append(self._build_extraction_result(item, tools, skills_list, meta))

        self._extraction_store.save(results)
        self._log_batch_complete(
            pending,
            parallel_enabled=parallel_enabled,
            concurrency=concurrency,
            batch_wall_clock_ms=batch_wall_clock_ms,
        )

        payload = self._build_payload(event, results)
        total_job_ms = sum(r.wall_clock_ms for r in pending)
        payload["avg_per_job_ms"] = int(total_job_ms / len(pending)) if pending else 0
        payload["extraction_duration_ms"] = batch_wall_clock_ms
        payload["parallel_enabled"] = parallel_enabled
        payload["concurrency"] = concurrency if parallel_enabled else 1

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )

    async def process_async(self, event: EventEnvelope) -> EventEnvelope:
        """Async-native entrypoint that always uses the parallel path.

        Use this instead of ``process()`` when calling from an async host (e.g.
        FastAPI, an async test runner, or another async agent). Unlike
        ``process()``, this method never falls back to serial execution because
        it awaits ``_extract_batch_parallel`` directly rather than going through
        ``_extract_batch_parallel_bridge``.
        """
        self._load_fixture()

        work_items = self._work_item_loader.load(event)
        if not work_items:
            return self._legacy_fixture_response(event)

        try:
            max_jobs = int(os.environ.get("SKILLS_EXTRACTION_MAX_JOBS", "0"))
        except (TypeError, ValueError):
            max_jobs = 0
        if max_jobs > 0 and len(work_items) > max_jobs:
            work_items = work_items[:max_jobs]

        concurrency = _parallel_concurrency()
        _warn_parallel_deprecated_serial_throttles()
        log.info(
            "skills_extraction_parallel_start",
            total_jobs=len(work_items),
            concurrency=concurrency,
            parallel_enabled=True,
            entrypoint="process_async",
        )

        batch_start = time.perf_counter()
        pending = await self._extract_batch_parallel(
            work_items,
            concurrency=concurrency,
            correlation_id=event.correlation_id,
        )
        batch_wall_clock_ms = int((time.perf_counter() - batch_start) * 1000)

        all_labels: list[str] = []
        seen_labels: set[str] = set()
        for pending_result in pending:
            for s in pending_result.skills_list:
                if s.skill_name not in seen_labels:
                    seen_labels.add(s.skill_name)
                    all_labels.append(s.skill_name)

        taxonomy_map: dict[str, Any] = {}
        if all_labels:
            log.info("taxonomy_batch_resolve", unique_labels=len(all_labels), total_jobs=len(pending))
            taxonomy_results = resolve_taxonomy_batch(all_labels)
            taxonomy_map = dict(zip(all_labels, taxonomy_results, strict=True))

        results = []
        for pending_result in pending:
            item = pending_result.item
            tools = pending_result.tools
            skills_list = pending_result.skills_list
            meta = pending_result.meta
            if skills_list:
                skills_list = apply_taxonomy_to_skills(skills_list, taxonomy_map)
            results.append(self._build_extraction_result(item, tools, skills_list, meta))

        self._extraction_store.save(results)
        self._log_batch_complete(
            pending,
            parallel_enabled=True,
            concurrency=concurrency,
            batch_wall_clock_ms=batch_wall_clock_ms,
        )

        payload = self._build_payload(event, results)
        total_job_ms = sum(r.wall_clock_ms for r in pending)
        payload["avg_per_job_ms"] = int(total_job_ms / len(pending)) if pending else 0
        payload["extraction_duration_ms"] = batch_wall_clock_ms
        payload["parallel_enabled"] = True
        payload["concurrency"] = concurrency

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )

    def _job_span_context(
        self,
        item: ExtractionWorkItem,
        *,
        execution_mode: str,
        correlation_id: str | None,
        index: int,
        total: int,
    ) -> Any:
        """Create an optional per-job trace span when a tracer is registered."""
        tracer = get_tracer()
        if not tracer or not hasattr(tracer, "start_span"):
            return nullcontext()

        return tracer.start_span(
            f"job/{item.title[:60]}",
            correlation_id=correlation_id
            or str(item.job_id or item.normalized_job_id or item.posting_id or "unknown-job"),
            input=json.dumps(
                {
                    "job_id": item.job_id,
                    "title": item.title,
                    "company": item.company,
                }
            ),
            metadata={
                "job_id": item.job_id,
                "normalized_job_id": item.normalized_job_id,
                "execution_mode": execution_mode,
                "idx": index,
                "total": total,
            },
        )

    def _extract_batch_parallel_bridge(
        self,
        work_items: Sequence[ExtractionWorkItem],
        *,
        concurrency: int,
        correlation_id: str | None = None,
    ) -> list[PendingExtraction]:
        """Run the async batch helper from the sync agent entrypoint."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self._extract_batch_parallel(
                    work_items,
                    concurrency=concurrency,
                    correlation_id=correlation_id,
                )
            )

        log.warning(
            "skills_extraction_parallel_fallback_serial",
            reason="event_loop_running",
            total_jobs=len(work_items),
            concurrency=concurrency,
        )
        return self._extract_batch_serial(work_items, correlation_id=correlation_id)

    def _extract_batch_serial(
        self,
        work_items: Sequence[ExtractionWorkItem],
        *,
        correlation_id: str | None = None,
    ) -> list[PendingExtraction]:
        """Run the legacy serial batch flow with deprecated throttles preserved."""
        pending: list[PendingExtraction] = []
        total = len(work_items)
        inter_job_delay = _serial_inter_job_delay()
        chunk_size = _serial_chunk_size()
        chunk_cooldown = _serial_chunk_cooldown()

        for idx, item in enumerate(work_items):
            if idx > 0 and inter_job_delay > 0:
                time.sleep(inter_job_delay)

            with self._job_span_context(
                item,
                execution_mode="serial",
                correlation_id=correlation_id,
                index=idx + 1,
                total=total,
            ):
                job_start = time.perf_counter()
                try:
                    tools, skills_list, meta, _ = self._extract_work_item_no_taxonomy(item)
                except Exception as exc:
                    tools = []
                    skills_list = []
                    meta = _job_extraction_failure_meta(item, exc)
                wall_clock_ms = int((time.perf_counter() - job_start) * 1000)
            pending_result = PendingExtraction(
                item=item,
                tools=tools,
                skills_list=skills_list,
                meta=meta,
                wall_clock_ms=wall_clock_ms,
            )
            pending.append(pending_result)
            self._log_job_complete(pending_result, execution_mode="serial")

            chunk_pos = idx + 1
            if chunk_size > 0 and chunk_pos % chunk_size == 0 and chunk_pos < total:
                log.info(
                    "skills_extraction_chunk_cooldown",
                    processed=chunk_pos,
                    total=total,
                    cooldown_seconds=chunk_cooldown,
                )
                time.sleep(chunk_cooldown)

        return pending

    async def _extract_batch_parallel(
        self,
        work_items: Sequence[ExtractionWorkItem],
        *,
        concurrency: int,
        correlation_id: str | None = None,
    ) -> list[PendingExtraction]:
        """Run multiple jobs concurrently while preserving output ordering."""
        semaphore = asyncio.Semaphore(concurrency)
        total = len(work_items)
        _in_flight = 0
        _saturation_events = 0
        _peak_in_flight = 0

        async def _extract_one(index: int, item: ExtractionWorkItem) -> PendingExtraction:
            nonlocal _in_flight, _saturation_events, _peak_in_flight
            if semaphore.locked():
                _saturation_events += 1
                log.debug(
                    "skills_extraction_semaphore_saturated",
                    job_id=item.job_id,
                    concurrency=concurrency,
                    queued_index=index,
                    saturation_events=_saturation_events,
                )
            async with semaphore:
                _in_flight += 1
                _peak_in_flight = max(_peak_in_flight, _in_flight)
                with self._job_span_context(
                    item,
                    execution_mode="parallel",
                    correlation_id=correlation_id,
                    index=index,
                    total=total,
                ):
                    job_start = time.perf_counter()
                    try:
                        tools, skills_list, meta, _ = await self._extract_work_item_no_taxonomy_async(item)
                    except Exception as exc:
                        tools = []
                        skills_list = []
                        meta = _job_extraction_failure_meta(item, exc)
                    wall_clock_ms = int((time.perf_counter() - job_start) * 1000)
                _in_flight -= 1
                pending_result = PendingExtraction(
                    item=item,
                    tools=tools,
                    skills_list=skills_list,
                    meta=meta,
                    wall_clock_ms=wall_clock_ms,
                )
                self._log_job_complete(pending_result, execution_mode="parallel")
                return pending_result

        results = list(
            await asyncio.gather(
                *[_extract_one(index, item) for index, item in enumerate(work_items, start=1)]
            )
        )
        if _saturation_events > 0:
            log.info(
                "skills_extraction_semaphore_saturation_summary",
                concurrency=concurrency,
                total_jobs=total,
                saturation_events=_saturation_events,
                peak_in_flight=_peak_in_flight,
            )
        return results

    def _log_job_complete(
        self,
        pending_result: PendingExtraction,
        *,
        execution_mode: str,
    ) -> None:
        """Emit one structured log line per finished job for observability and tuning."""
        meta = pending_result.meta or {}
        log.info(
            "skills_extraction_job_complete",
            execution_mode=execution_mode,
            job_id=pending_result.item.job_id,
            normalized_job_id=pending_result.item.normalized_job_id,
            wall_clock_ms=pending_result.wall_clock_ms,
            extraction_status=meta.get("extraction_status"),
            dimensions_succeeded=list(meta.get("pass2_dimensions_succeeded") or []),
            dimensions_failed=list(meta.get("pass2_dimensions_failed") or []),
        )

    def _log_batch_complete(
        self,
        pending: Sequence[PendingExtraction],
        *,
        parallel_enabled: bool,
        concurrency: int,
        batch_wall_clock_ms: int,
    ) -> None:
        """Emit a summary log line for one extraction batch."""
        total_jobs = len(pending)
        total_job_ms = sum(result.wall_clock_ms for result in pending)
        utilization_denominator = max(batch_wall_clock_ms * max(concurrency, 1), 1)
        concurrency_utilization = min(total_job_ms / utilization_denominator, 1.0)
        log.info(
            "skills_extraction_batch_complete",
            total_jobs=total_jobs,
            parallel_enabled=parallel_enabled,
            concurrency=concurrency,
            total_wall_clock_ms=batch_wall_clock_ms,
            total_llm_calls=sum(int((result.meta or {}).get("pass2_llm_calls") or 0) for result in pending),
            avg_per_job_ms=int(total_job_ms / total_jobs) if total_jobs else 0,
            concurrency_utilization=round(concurrency_utilization, 4),
            failed_jobs=sum(
                1
                for result in pending
                if (result.meta or {}).get("extraction_status") == "failed"
            ),
            degraded_jobs=sum(
                1
                for result in pending
                if (result.meta or {}).get("extraction_status") == "degraded"
            ),
        )

    def _extract_work_item_no_taxonomy_parallel_bridge(
        self, item: ExtractionWorkItem
    ) -> tuple[list[ToolRecord], list, dict, bool]:
        """Run one work item through the async intra-job path from sync agent code."""
        pending = self._extract_batch_parallel_bridge([item], concurrency=1)
        if not pending:
            return [], [], _job_extraction_failure_meta(
                item,
                RuntimeError("parallel bridge returned no pending results"),
            ), False
        result = pending[0]
        return result.tools, result.skills_list, result.meta, True

    def _extract_work_item_no_taxonomy(
        self, item: ExtractionWorkItem
    ) -> tuple[list[ToolRecord], list, dict, bool]:
        """Pass 1: context + tools. Pass 2: tasks, responsibilities, skills (taxonomy deferred).

        Returns ``(tools, skills_list, combined_meta, used_llm)``. ``combined_meta`` carries
        serialized dimension payloads and per-dimension metadata for ``_build_extraction_result``.
        """
        job = item.job_record
        tools = extract_tools(job)
        context_signals, ctx_meta = extract_context(job)

        has_normalized_text = bool(
            (job.description or "").strip()
            or (job.requirements or "").strip()
            or (job.responsibilities or "").strip()
        )

        if not has_normalized_text:
            return tools, [], _no_normalized_text_meta(item, context_signals, ctx_meta), False

        tasks, tasks_meta = extract_tasks(job, pass1_context=context_signals)
        responsibilities, resp_meta = extract_responsibilities(
            job, pass1_context=context_signals
        )
        skills_list, skills_meta = extract_skills_no_taxonomy(job, pass1_tools=tools)

        combined_meta = _build_combined_pass2_meta(
            context_signals=context_signals,
            ctx_meta=ctx_meta,
            tasks=tasks,
            tasks_meta=tasks_meta,
            responsibilities=responsibilities,
            resp_meta=resp_meta,
            skills_meta=skills_meta,
            pass2_latency_ms=(
                int(tasks_meta.get("latency_ms") or 0)
                + int(resp_meta.get("latency_ms") or 0)
                + int(skills_meta.get("latency_ms") or 0)
            ),
        )
        return tools, skills_list, combined_meta, True

    async def _extract_work_item_no_taxonomy_async(
        self, item: ExtractionWorkItem
    ) -> tuple[list[ToolRecord], list, dict, bool]:
        """Pass 1 sync + Pass 2 async gather for one work item (taxonomy deferred)."""
        job = item.job_record
        tools = extract_tools(job)
        context_signals, ctx_meta = extract_context(job)

        has_normalized_text = bool(
            (job.description or "").strip()
            or (job.requirements or "").strip()
            or (job.responsibilities or "").strip()
        )

        if not has_normalized_text:
            return tools, [], _no_normalized_text_meta(item, context_signals, ctx_meta), False

        start = time.perf_counter()
        tasks_result, resp_result, skills_result = await asyncio.gather(
            extract_tasks_async(job, pass1_context=context_signals),
            extract_responsibilities_async(job, pass1_context=context_signals),
            extract_skills_no_taxonomy_async(job, pass1_tools=tools),
            return_exceptions=True,
        )
        pass2_latency_ms = int((time.perf_counter() - start) * 1000)

        tasks, tasks_meta = _resolve_async_dimension_result(tasks_result, "tasks")
        responsibilities, resp_meta = _resolve_async_dimension_result(
            resp_result, "responsibilities"
        )
        skills_list, skills_meta = _resolve_async_dimension_result(
            skills_result, "skills"
        )

        combined_meta = _build_combined_pass2_meta(
            context_signals=context_signals,
            ctx_meta=ctx_meta,
            tasks=tasks,
            tasks_meta=tasks_meta,
            responsibilities=responsibilities,
            resp_meta=resp_meta,
            skills_meta=skills_meta,
            pass2_latency_ms=pass2_latency_ms,
        )
        return tools, skills_list, combined_meta, True

    def _build_extraction_result(
        self,
        item: ExtractionWorkItem,
        tools: list[ToolRecord],
        skills_list: list,
        meta: dict,
    ) -> ExtractionResult:
        """Build ExtractionResult from tools + taxonomy-resolved skills and Week 5 dimensions."""
        if meta and ("success" in meta or "extraction_failed" in meta):
            skills_payload = [s.model_dump() for s in skills_list]
            status = meta.get("extraction_status")
            if status not in ("success", "degraded", "failed"):
                status = "success" if not meta.get("extraction_failed") else "failed"
            tasks_raw = meta.get("tasks") or []
            resp_raw = meta.get("responsibilities") or []
            ctx_raw = meta.get("context_signals") or []
            tasks_payload = [t.model_dump() for t in tasks_raw]
            resp_payload = [r.model_dump() for r in resp_raw]
            context_payload = [c.model_dump() for c in ctx_raw]
            warn = tuple(str(w) for w in (meta.get("extraction_warnings") or []))
            meta_blob = _metadata_from_pass2(meta, tools, extraction_version=EXTRACTION_VERSION)
            return ExtractionResult(
                work_item=item,
                skills=skills_payload,
                tools=tools,
                tasks=tasks_payload,
                responsibilities=resp_payload,
                context=context_payload,
                seniority=None,
                extraction_status=status,
                extraction_tokens_used=meta.get("tokens_used", 0) or 0,
                extraction_cost_usd=meta.get("cost_usd", 0.0) or 0.0,
                alert_skills_extraction=meta.get("alert_skills_extraction", False),
                extraction_warnings=warn,
                extraction_metadata=meta_blob,
                persisted_extraction_version=EXTRACTION_VERSION,
                persisted_extraction_model=_persisted_extraction_model_llm(),
            )
        # No fixture fallback — fail explicitly so data issues surface
        import structlog as _sl
        _sl.get_logger().error(
            "skills_extraction_no_metadata",
            job_id=item.job_id,
            title=item.title,
            reason="No extraction metadata — possible pipeline misconfiguration",
        )
        return ExtractionResult(
            work_item=item,
            skills=[],
            tools=tools,
            seniority=None,
            extraction_status="failed",
            extraction_warnings=("No extraction metadata — check pipeline wiring",),
            persisted_extraction_version=EXTRACTION_VERSION,
            persisted_extraction_model="none",
        )

    def _build_payload(
        self,
        event: EventEnvelope,
        results: Sequence[ExtractionResult],
    ) -> dict[str, Any]:
        """Build a batch-aligned SkillsExtracted payload with single-record compatibility."""
        summaries = [_result_summary(result) for result in results]
        job_ids = [summary["job_id"] for summary in summaries if summary["job_id"] is not None]
        total_tasks = sum(len(getattr(result, "tasks", []) or []) for result in results)
        total_resp = sum(len(getattr(result, "responsibilities", []) or []) for result in results)
        total_ctx = sum(len(getattr(result, "context", []) or []) for result in results)
        total_skills = sum(len(result.skills) for result in results)
        skills_with_taxonomy = sum(
            1
            for result in results
            for s in result.skills
            if isinstance(s, dict) and (s.get("esco_uri") or s.get("is_genai_extension"))
        )
        taxonomy_coverage = (skills_with_taxonomy / total_skills) if total_skills else 0.0
        total_cost = sum(getattr(result, "extraction_cost_usd", 0.0) or 0.0 for result in results)
        any_llm_called = any(
            (getattr(r, "extraction_tokens_used", 0) or 0) > 0 for r in results
        )
        any_alert = any(
            getattr(r, "alert_skills_extraction", False) for r in results
        )
        payload: dict[str, Any] = {
            "event_type": "SkillsExtracted",
            "batch_id": event.payload.get("batch_id"),
            "job_ids": job_ids,
            "skills_count": total_skills,
            "tools_count": sum(len(result.tools) for result in results),
            "tasks_count": total_tasks,
            "responsibilities_count": total_resp,
            "context_signals_count": total_ctx,
            "context_count": total_ctx,
            "taxonomy_coverage": round(taxonomy_coverage, 4),
            "extraction_cost_usd": round(total_cost, 6),
            "failed_count": sum(1 for result in results if result.extraction_status == "failed"),
            "records": summaries,
            "llm_provider": "azure-openai" if any_llm_called else "stub",
            "llm_model": _llm_deployment_name() if any_llm_called else "stub",
            "llm_call_logged": any_llm_called,
            "skills_extraction_alert": any_alert,
        }

        if len(results) == 1:
            result = results[0]
            payload.update(
                {
                    "posting_id": result.work_item.posting_id,
                    "title": result.work_item.title,
                    "company": result.work_item.company,
                    "skills": result.skills,
                    "tools": [tool.model_dump() for tool in result.tools],
                    "tasks": list(getattr(result, "tasks", []) or []),
                    "responsibilities": list(getattr(result, "responsibilities", []) or []),
                    "context": list(getattr(result, "context", []) or []),
                    "tasks_count": len(getattr(result, "tasks", []) or []),
                    "responsibilities_count": len(getattr(result, "responsibilities", []) or []),
                    "context_signals_count": len(getattr(result, "context", []) or []),
                    "seniority": result.seniority,
                    "extraction_status": result.extraction_status,
                }
            )

        return payload

    def _legacy_fixture_response(self, event: EventEnvelope) -> EventEnvelope:
        """Preserve the original fixture-only behavior when no normalized text is available."""
        posting_id = _int_value(event.payload.get("posting_id"))
        fixture_payload = self._fixture.get(posting_id, {}) if posting_id is not None else {}
        skills = fixture_payload.get("skills", [])
        payload: dict[str, Any] = {
            "event_type": "SkillsExtracted",
            "batch_id": event.payload.get("batch_id"),
            "job_ids": [posting_id] if posting_id is not None else [],
            "skills_count": len(skills),
            "tools_count": 0,
            "tasks_count": 0,
            "responsibilities_count": 0,
            "context_signals_count": 0,
            "context_count": 0,
            "taxonomy_coverage": 0.0,
            "extraction_cost_usd": 0.0,
            "failed_count": 0,
            "posting_id": posting_id,
            "title": fixture_payload.get("title"),
            "company": fixture_payload.get("company"),
            "skills": skills,
            "tools": [],
            "seniority": fixture_payload.get("seniority"),
            "extraction_status": fixture_payload.get("extraction_status", "success"),
            "records": [
                {
                    "job_id": posting_id,
                    "posting_id": posting_id,
                    "normalized_job_id": None,
                    "title": fixture_payload.get("title"),
                    "company": fixture_payload.get("company"),
                    "skills": skills,
                    "tools": [],
                    "tasks": [],
                    "responsibilities": [],
                    "context": [],
                    "tasks_count": 0,
                    "responsibilities_count": 0,
                    "context_signals_count": 0,
                    "seniority": fixture_payload.get("seniority"),
                    "extraction_status": fixture_payload.get("extraction_status", "success"),
                }
            ] if posting_id is not None else [],
            "llm_provider": "stub",
            "llm_model": "stub",
            "llm_call_logged": False,
        }
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )

    def _load_fixture(self) -> bool:
        """Load the existing Week 2 fixture payload once for skills fallback."""
        if self._fixture:
            return True
        if not _FIXTURE_PATH.exists():
            return False
        try:
            records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return False

        self._fixture = {r["posting_id"]: r for r in records}
        return True


def _metadata_from_pass2(
    meta: dict[str, Any],
    tools: list[ToolRecord],
    *,
    extraction_version: str,
) -> dict[str, Any]:
    """Flatten Pass 1/2 dimension metadata for ``extracted_intelligence.extraction_metadata`` JSON."""
    dim = meta.get("dimension_metas") or {}
    raw_warnings = [str(w) for w in (meta.get("extraction_warnings") or [])]
    em = ExtractionMetadata(
        extraction_version=extraction_version,
        model_used=str(meta.get("model") or ""),
        model_tier=os.environ.get("EXTRACTION_MODEL_TIER", "mixed"),
        tokens_used=int(meta.get("tokens_used") or 0),
        cost_usd=float(meta.get("cost_usd") or 0.0),
        extraction_duration_ms=int(meta.get("latency_ms") or 0),
        pass1_tool_count=len(tools),
        pass2_llm_dimensions=list(meta.get("pass2_llm_dimensions") or []),
        pass2_llm_calls=int(meta.get("pass2_llm_calls") or 0),
        extraction_warnings=raw_warnings,
    )
    out: dict[str, Any] = em.model_dump()
    out["pass1_context"] = dim.get("pass1_context", {})
    out["tasks"] = dim.get("tasks", {})
    out["responsibilities"] = dim.get("responsibilities", {})
    out["skills"] = dim.get("skills", {})
    return out


def _no_normalized_text_meta(
    item: ExtractionWorkItem,
    context_signals: list[Any],
    ctx_meta: dict[str, Any],
) -> dict[str, Any]:
    """Build the explicit failed-extraction metadata when no normalized text is available."""
    log.warning(
        "skills_extraction_no_text",
        job_id=item.job_id,
        title=item.title,
        company=item.company,
        reason="No description/requirements/responsibilities text — cannot extract skills",
    )
    warn = _coerce_pass2_warnings(ctx_meta)
    return {
        "success": False,
        "extraction_failed": True,
        "extraction_status": "failed",
        "error_reason": "no_normalized_text",
        "tokens_used": int(ctx_meta.get("tokens_used") or 0),
        "cost_usd": float(ctx_meta.get("cost_usd") or 0.0),
        "latency_ms": int(ctx_meta.get("latency_ms") or 0),
        "extraction_warnings": list(warn)
        + ["No normalized text available for extraction"],
        "alert_skills_extraction": False,
        "provider": ctx_meta.get("provider", "pattern-matching"),
        "model": ctx_meta.get("model", "none"),
        "context_signals": context_signals,
        "tasks": [],
        "responsibilities": [],
        "dimension_metas": {
            "pass1_context": ctx_meta.get("extraction_metadata", {}),
        },
        "pass2_llm_calls": 0,
        "pass2_llm_dimensions": [],
        "pass2_dimensions_succeeded": [],
        "pass2_dimensions_failed": [],
    }


def _job_extraction_failure_meta(
    item: ExtractionWorkItem,
    error: BaseException,
) -> dict[str, Any]:
    """Build metadata for unexpected job-level failures so the batch can continue."""
    error_reason = f"{type(error).__name__}: {error}" if str(error) else type(error).__name__
    log.error(
        "skills_extraction_job_failed",
        job_id=item.job_id,
        title=item.title,
        company=item.company,
        error_type=type(error).__name__,
        error_reason=error_reason,
    )
    return {
        "success": False,
        "extraction_failed": True,
        "extraction_status": "failed",
        "error_reason": error_reason,
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 0,
        "extraction_warnings": [error_reason],
        "alert_skills_extraction": False,
        "provider": "azure-openai",
        "model": _llm_deployment_name(),
        "context_signals": [],
        "tasks": [],
        "responsibilities": [],
        "dimension_metas": {},
        "pass2_llm_calls": 0,
        "pass2_llm_dimensions": [],
        "pass2_dimensions_succeeded": [],
        "pass2_dimensions_failed": [],
    }


def _async_dimension_failure_meta(dimension: str, error: BaseException) -> dict[str, Any]:
    """Build a standard extractor metadata payload when an async dimension raises."""
    error_reason = f"{type(error).__name__}: {error}" if str(error) else type(error).__name__
    log.error(
        "skills_extraction_async_dimension_failed",
        dimension=dimension,
        error_type=type(error).__name__,
        error_reason=error_reason,
    )
    return {
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 0,
        "success": False,
        "extraction_failed": True,
        "error_reason": error_reason,
        "provider": "azure-openai",
        "model": "",
        "extraction_metadata": {},
        "extraction_warnings": [f"{dimension} extraction raised {type(error).__name__}"],
    }


def _resolve_async_dimension_result(
    result: object,
    dimension: str,
) -> tuple[list[Any], dict[str, Any]]:
    """Normalize ``asyncio.gather(..., return_exceptions=True)`` results per dimension."""
    if isinstance(result, BaseException):
        return [], _async_dimension_failure_meta(dimension, result)
    if (
        isinstance(result, tuple)
        and len(result) == 2
        and isinstance(result[1], dict)
    ):
        payload, meta = result
        return list(payload or []), meta
    malformed = RuntimeError(f"{dimension} extractor returned malformed result")
    return [], _async_dimension_failure_meta(dimension, malformed)


def _build_combined_pass2_meta(
    *,
    context_signals: list[Any],
    ctx_meta: dict[str, Any],
    tasks: list[Any],
    tasks_meta: dict[str, Any],
    responsibilities: list[Any],
    resp_meta: dict[str, Any],
    skills_meta: dict[str, Any],
    pass2_latency_ms: int,
) -> dict[str, Any]:
    """Aggregate Pass 1 and Pass 2 metadata into the persisted combined shape."""
    total_tokens = (
        int(ctx_meta.get("tokens_used") or 0)
        + int(tasks_meta.get("tokens_used") or 0)
        + int(resp_meta.get("tokens_used") or 0)
        + int(skills_meta.get("tokens_used") or 0)
    )
    total_cost = (
        float(ctx_meta.get("cost_usd") or 0.0)
        + float(tasks_meta.get("cost_usd") or 0.0)
        + float(resp_meta.get("cost_usd") or 0.0)
        + float(skills_meta.get("cost_usd") or 0.0)
    )
    total_latency = int(ctx_meta.get("latency_ms") or 0) + max(0, pass2_latency_ms)

    skills_failed = bool(skills_meta.get("extraction_failed"))
    tasks_failed = bool(tasks_meta.get("extraction_failed"))
    resp_failed = bool(resp_meta.get("extraction_failed"))

    if skills_failed:
        extraction_status = "failed"
    elif tasks_failed or resp_failed:
        extraction_status = "degraded"
    else:
        extraction_status = "success"

    pass2_dimensions_succeeded = [
        dimension
        for dimension, failed in (
            ("tasks", tasks_failed),
            ("responsibilities", resp_failed),
            ("skills", skills_failed),
        )
        if not failed
    ]
    pass2_dimensions_failed = [
        dimension
        for dimension, failed in (
            ("tasks", tasks_failed),
            ("responsibilities", resp_failed),
            ("skills", skills_failed),
        )
        if failed
    ]
    warn = _coerce_pass2_warnings(ctx_meta, tasks_meta, resp_meta, skills_meta)

    return {
        "success": extraction_status == "success",
        "extraction_failed": skills_failed,
        "extraction_status": extraction_status,
        "error_reason": skills_meta.get("error_reason"),
        "tokens_used": total_tokens,
        "cost_usd": total_cost,
        "latency_ms": total_latency,
        "extraction_warnings": list(warn),
        "alert_skills_extraction": bool(
            skills_meta.get("alert_skills_extraction")
            or tasks_meta.get("alert_tasks_extraction")
            or resp_meta.get("alert_responsibilities_extraction")
        ),
        "provider": skills_meta.get("provider", "azure-openai"),
        "model": skills_meta.get("model") or _llm_deployment_name(),
        "context_signals": context_signals,
        "tasks": tasks,
        "responsibilities": responsibilities,
        "dimension_metas": {
            "pass1_context": ctx_meta.get("extraction_metadata", {}),
            "tasks": tasks_meta.get("extraction_metadata", {}),
            "responsibilities": resp_meta.get("extraction_metadata", {}),
            "skills": {
                k: skills_meta.get(k)
                for k in (
                    "model",
                    "tokens_used",
                    "cost_usd",
                    "latency_ms",
                    "success",
                    "extraction_failed",
                    "error_reason",
                )
                if k in skills_meta
            },
        },
        "pass2_llm_calls": 3,
        "pass2_llm_dimensions": ["tasks", "responsibilities", "skills"],
        "pass2_dimensions_succeeded": pass2_dimensions_succeeded,
        "pass2_dimensions_failed": pass2_dimensions_failed,
    }


def _coerce_pass2_warnings(*metas: dict[str, Any]) -> tuple[str, ...]:
    """Deduplicate warnings and error_reason strings from Pass 2 extractor metas."""
    out: list[str] = []
    for m in metas:
        for w in m.get("extraction_warnings") or []:
            s = str(w)
            if s and s not in out:
                out.append(s)
        err = m.get("error_reason")
        if err:
            es = str(err)
            if es and es not in out:
                out.append(es)
    return tuple(out)


def _result_summary(result: ExtractionResult) -> dict[str, Any]:
    """Serialize one extraction result for the batch payload."""
    tasks = list(getattr(result, "tasks", []) or [])
    resp = list(getattr(result, "responsibilities", []) or [])
    ctx = list(getattr(result, "context", []) or [])
    jr = result.work_item.job_record
    return {
        "job_id": result.work_item.job_id,
        "posting_id": result.work_item.posting_id,
        "normalized_job_id": result.work_item.normalized_job_id,
        "title": result.work_item.title,
        "company": result.work_item.company,
        "source": jr.source,
        "external_id": jr.external_id,
        "description": jr.description,
        "skills": result.skills,
        "tools": [tool.model_dump() for tool in result.tools],
        "tasks": tasks,
        "responsibilities": resp,
        "context": ctx,
        "tasks_count": len(tasks),
        "responsibilities_count": len(resp),
        "context_signals_count": len(ctx),
        "seniority": result.seniority,
        "extraction_status": result.extraction_status,
    }


def _average_tool_confidence(tools: Sequence[ToolRecord]) -> float | None:
    """Compute a simple overall confidence score for persisted Pass 1 output."""
    if not tools:
        return None
    return sum(tool.confidence for tool in tools) / len(tools)


def _overall_extraction_confidence(result: ExtractionResult) -> float | None:
    """Blend tool and JSONB dimension confidences for a single scalar score."""
    scores: list[float] = []
    for tool in result.tools:
        scores.append(tool.confidence)
    for row in getattr(result, "tasks", []) or []:
        if isinstance(row, dict) and row.get("confidence") is not None:
            with suppress(TypeError, ValueError):
                scores.append(float(row["confidence"]))
    for row in getattr(result, "responsibilities", []) or []:
        if isinstance(row, dict) and row.get("confidence") is not None:
            with suppress(TypeError, ValueError):
                scores.append(float(row["confidence"]))
    for row in getattr(result, "context", []) or []:
        if isinstance(row, dict) and row.get("confidence") is not None:
            with suppress(TypeError, ValueError):
                scores.append(float(row["confidence"]))
    if not scores:
        return _average_tool_confidence(result.tools)
    return sum(scores) / len(scores)


def _int_value(value: Any) -> int | None:
    """Best-effort integer coercion for ids carried on event payloads."""
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _string_value(value: Any) -> str | None:
    """Return a stripped string or None when the value is empty."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


# Architecture docs name; implementation class is SkillsExtractionAgent.
WorkIntelligenceAgent = SkillsExtractionAgent
