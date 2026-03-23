"""
Skills Extraction Agent (Work Intelligence Agent) — Week 5 six-dimension extraction.

Pass 1: ``extract_context`` (regex, zero LLM tokens), ``extract_tools`` (pattern catalog).
Pass 2: ``extract_tasks`` (Haiku-tier deployment), ``extract_responsibilities`` (Sonnet-tier
deployment), ``extract_skills`` (skills deployment). Pass 1 context signals are injected
into task and responsibility prompts.

Input modes (in order):
1. Inline normalized records on the event payload
2. Batch load from ``dbo.normalized_jobs`` by ``batch_id`` / ``ingestion_run_id``
3. Legacy ``posting_id`` fixture fallback for walking-skeleton tests
"""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from agents.common.base_agent import BaseAgent
from agents.common.data_store import check_db_connection, session_scope
from agents.common.data_store.models import ExtractedIntelligence, NormalizedJob
from agents.common.event_envelope import EventEnvelope
from agents.common.types import JobRecord, ToolRecord
from agents.skills_extraction.extractors import (
    extract_context,
    extract_responsibilities,
    extract_skills,
    extract_tasks,
    extract_tools,
)

_FIXTURE_PATH = (
    Path(__file__).parent.parent / "data" / "fixtures" / "fixture_skills_extracted.json"
)
EXTRACTION_VERSION = "week5-six-dim-v1"
EXTRACTION_MODEL = "hybrid-pattern-llm"


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
    extraction_metadata_blob: dict[str, Any] | None = field(default=None)


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
        if not results or not check_db_connection():
            return

        with session_scope() as session:
            for result in results:
                normalized_job_id = result.work_item.normalized_job_id
                if normalized_job_id is None:
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
                    extraction_model=EXTRACTION_MODEL,
                )
                if not existing_rows:
                    session.add(row)
                for duplicate in existing_rows[1:]:
                    session.delete(duplicate)

                row.extraction_version = EXTRACTION_VERSION
                row.extraction_model = EXTRACTION_MODEL
                row.extraction_tokens_used = getattr(result, "extraction_tokens_used", 0) or 0
                row.extraction_cost_usd = getattr(result, "extraction_cost_usd", 0.0) or 0.0
                row.skills = result.skills
                row.tools = [tool.model_dump() for tool in result.tools]
                row.tasks = list(getattr(result, "tasks", []) or [])
                row.responsibilities = list(getattr(result, "responsibilities", []) or [])
                row.context = list(getattr(result, "context", []) or [])
                row.overall_confidence = _overall_extraction_confidence(result)
                row.extraction_warnings = _flatten_extraction_warnings(result)
                # Degraded = partial LLM failure (e.g. tasks) but skills OK — not a hard failure.
                row.extraction_failed = result.extraction_status == "failed"
                blob = getattr(result, "extraction_metadata_blob", None)
                row.extraction_metadata = blob if isinstance(blob, dict) else None


class SkillsExtractionAgent(BaseAgent):
    """
    Stub for the Skills Extraction Agent.

    Week 2: returns fixture data indexed by posting_id instead of calling an LLM.
    Week 4: replaces this with real LLM extraction + taxonomy linking.
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

        Pass 1 (tools) runs against inline normalized payloads or batch-loaded
        dbo.normalized_jobs rows. Skills remain fixture-backed until Pass 2
        LLM extraction lands.
        """
        self._load_fixture()

        work_items = self._work_item_loader.load(event)
        if not work_items:
            return self._legacy_fixture_response(event)

        # Cap work items per run for faster pipeline runs (default 10; set SKILLS_EXTRACTION_MAX_JOBS to override)
        try:
            max_jobs = int(os.environ.get("SKILLS_EXTRACTION_MAX_JOBS", "10"))
        except (TypeError, ValueError):
            max_jobs = 10
        if max_jobs > 0 and len(work_items) > max_jobs:
            work_items = work_items[:max_jobs]

        results = [self._extract_work_item(item) for item in work_items]
        self._extraction_store.save(results)
        # When payload["skills_extraction_alert"] is True, caller/orchestrator should
        # publish SkillsExtractionAlert so the Orchestration Agent can react.

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=self._build_payload(event, results),
        )

    def _extract_work_item(self, item: ExtractionWorkItem) -> ExtractionResult:
        """Run Pass 1 (context, tools) then Pass 2 (tasks, responsibilities, skills)."""
        job = item.job_record
        # Pass 1: context signals first (zero LLM), then tools (pattern).
        context_signals, ctx_meta = extract_context(job)
        tools = extract_tools(job)

        has_normalized_text = bool(
            (job.description or "").strip()
            or (job.requirements or "").strip()
            or (job.responsibilities or "").strip()
        )

        if has_normalized_text:
            tasks, tasks_meta = extract_tasks(job, pass1_context=context_signals)
            responsibilities, resp_meta = extract_responsibilities(
                job, pass1_context=context_signals
            )
            skills_list, skills_meta = extract_skills(job, pass1_tools=tools)

            skills_payload = [s.model_dump() for s in skills_list]
            tasks_payload = [t.model_dump() for t in tasks]
            resp_payload = [r.model_dump() for r in responsibilities]
            context_payload = [c.model_dump() for c in context_signals]

            total_tokens = (
                (skills_meta.get("tokens_used") or 0)
                + (ctx_meta.get("tokens_used") or 0)
                + (tasks_meta.get("tokens_used") or 0)
                + (resp_meta.get("tokens_used") or 0)
            )
            total_cost = (
                float(skills_meta.get("cost_usd") or 0.0)
                + float(ctx_meta.get("cost_usd") or 0.0)
                + float(tasks_meta.get("cost_usd") or 0.0)
                + float(resp_meta.get("cost_usd") or 0.0)
            )

            skills_failed = bool(skills_meta.get("extraction_failed"))
            tasks_failed = bool(tasks_meta.get("extraction_failed"))
            resp_failed = bool(resp_meta.get("extraction_failed"))
            status = "success"
            if skills_failed:
                status = "failed"
            elif tasks_failed or resp_failed:
                status = "degraded"

            meta_blob = {
                "pass1_context": ctx_meta.get("extraction_metadata", {}),
                "tasks": tasks_meta.get("extraction_metadata", {}),
                "responsibilities": resp_meta.get("extraction_metadata", {}),
            }

            return ExtractionResult(
                work_item=item,
                skills=skills_payload,
                tools=tools,
                tasks=tasks_payload,
                responsibilities=resp_payload,
                context=context_payload,
                seniority=None,
                extraction_status=status,
                extraction_tokens_used=int(total_tokens),
                extraction_cost_usd=total_cost,
                alert_skills_extraction=skills_meta.get("alert_skills_extraction", False),
                extraction_metadata_blob=meta_blob,
            )

        fixture_payload = self._fixture.get(item.posting_id, {}) if item.posting_id is not None else {}
        context_payload = [c.model_dump() for c in context_signals]
        return ExtractionResult(
            work_item=item,
            skills=fixture_payload.get("skills", []),
            tools=tools,
            tasks=[],
            responsibilities=[],
            context=context_payload,
            seniority=fixture_payload.get("seniority"),
            extraction_status=fixture_payload.get("extraction_status", "success"),
            extraction_metadata_blob={"pass1_context": ctx_meta.get("extraction_metadata", {})},
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
            "llm_model": "sonnet" if any_llm_called else "stub",
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


def _result_summary(result: ExtractionResult) -> dict[str, Any]:
    """Serialize one extraction result for the batch payload."""
    tasks = list(getattr(result, "tasks", []) or [])
    resp = list(getattr(result, "responsibilities", []) or [])
    ctx = list(getattr(result, "context", []) or [])
    return {
        "job_id": result.work_item.job_id,
        "posting_id": result.work_item.posting_id,
        "normalized_job_id": result.work_item.normalized_job_id,
        "title": result.work_item.title,
        "company": result.work_item.company,
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
            try:
                scores.append(float(row["confidence"]))
            except (TypeError, ValueError):
                pass
    for row in getattr(result, "responsibilities", []) or []:
        if isinstance(row, dict) and row.get("confidence") is not None:
            try:
                scores.append(float(row["confidence"]))
            except (TypeError, ValueError):
                pass
    for row in getattr(result, "context", []) or []:
        if isinstance(row, dict) and row.get("confidence") is not None:
            try:
                scores.append(float(row["confidence"]))
            except (TypeError, ValueError):
                pass
    if not scores:
        return _average_tool_confidence(result.tools)
    return sum(scores) / len(scores)


def _flatten_extraction_warnings(result: ExtractionResult) -> list[str]:
    """Collect nested extraction_warnings from dimension metadata blobs."""
    out: list[str] = []
    blob = getattr(result, "extraction_metadata_blob", None) or {}
    if not isinstance(blob, dict):
        return out
    for key in ("pass1_context", "tasks", "responsibilities"):
        inner = blob.get(key)
        if isinstance(inner, dict):
            w = inner.get("extraction_warnings")
            if isinstance(w, list):
                out.extend(str(x) for x in w)
    return out


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
