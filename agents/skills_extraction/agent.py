"""
Skills Extraction Agent stub — Week 2 Walking Skeleton.

Real implementation: Week 4.

In the walking skeleton this agent returns a pre-computed fixture payload
instead of making an LLM call.  The fixture (fixture_skills_extracted.json)
contains realistic skill extractions for all 10 demo postings, matched to
the actual job descriptions in fallback_scrape_sample.json.

Agent ID (canonical): skills-extraction-agent
Emits:    SkillsExtracted
Consumes: NormalizationComplete

Fixture: agents/data/fixtures/fixture_skills_extracted.json

Week 4 replaces this stub with:
- LLM-based skill extraction via LangChain + Azure OpenAI
- Taxonomy linking against the watechcoalition skills table
- Embedding cosine similarity fallback (>= 0.92 threshold)
- O*NET occupation code fallback
- LLM call logging to llm_audit_log
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.data_store.database import check_db_connection, session_scope
from agents.common.data_store.models import ExtractedIntelligence
from agents.common.event_envelope import EventEnvelope
from agents.common.types.extraction_metadata import ExtractionMetadata
from agents.skills_extraction.validator import validate_extraction_result

log = structlog.get_logger()

_FIXTURE_PATH = (
    Path(__file__).parent.parent / "data" / "fixtures" / "fixture_skills_extracted.json"
)

_EXTRACTION_VERSION = "stub-week2"
_STUB_MODEL = "stub"


class SkillsExtractionAgent(BaseAgent):
    """
    Stub for the Skills Extraction Agent.

    Week 2: returns fixture data indexed by posting_id instead of calling an LLM.
    Week 4: replaces this with real LLM extraction + taxonomy linking.
    """

    @property
    def agent_id(self) -> str:
        return "skills-extraction-agent"

    def __init__(self) -> None:
        self._fixture: dict[int, dict] = {}

    def health_check(self) -> dict:
        """Return agent health: fixture availability + DB reachability."""
        fixture_ok = False
        if _FIXTURE_PATH.exists():
            try:
                records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
                self._fixture = {r["posting_id"]: r for r in records}
                fixture_ok = True
            except Exception:
                pass

        db_reachable = check_db_connection()
        status = "ok" if (fixture_ok and db_reachable) else "degraded"

        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {},
            "db_reachable": db_reachable,
            "fixture_available": fixture_ok,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Accept a NormalizationComplete event and emit a SkillsExtracted event.

        Loads fixture data for the given posting_id, runs validation guardrails,
        and writes an ExtractedIntelligence row when a normalized_job_id is
        present in the payload (real pipeline path). The fixture-only path
        (no normalized_job_id) skips the DB write safely.
        """
        if not self._fixture:
            records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
            self._fixture = {r["posting_id"]: r for r in records}

        posting_id = event.payload.get("posting_id")
        normalized_job_id: int | None = event.payload.get("normalized_job_id")
        fx = self._fixture.get(posting_id, {})

        raw_skills = fx.get("skills", [])
        raw_tools: list[dict] = []  # fixture merges tools into skills; real extraction separates them

        # Validate extraction output — always run, even on stub data
        warnings = validate_extraction_result(skills=raw_skills, tools=raw_tools)

        # Stub cost/token values (Week 4 replaces with real llm_adapter.complete() output)
        extraction_tokens_used = 0
        extraction_cost_usd = 0.0
        extraction_duration_ms = 0

        metadata = ExtractionMetadata(
            extraction_version=_EXTRACTION_VERSION,
            model_used=_STUB_MODEL,
            model_tier="stub",
            tokens_used=extraction_tokens_used,
            cost_usd=extraction_cost_usd,
            extraction_duration_ms=extraction_duration_ms,
            pass1_tool_count=len(raw_tools),
            pass2_llm_dimensions=[],
            extraction_warnings=warnings,
        )

        # Wire into extracted_intelligence when a real normalized_job_id is available
        if normalized_job_id is not None:
            self._write_extracted_intelligence(
                normalized_job_id=normalized_job_id,
                raw_skills=raw_skills,
                raw_tools=raw_tools,
                warnings=warnings,
                extraction_tokens_used=extraction_tokens_used,
                extraction_cost_usd=extraction_cost_usd,
                metadata=metadata,
            )

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "SkillsExtracted",
                "posting_id": posting_id,
                "normalized_job_id": normalized_job_id,
                "title": fx.get("title"),
                "company": fx.get("company"),
                "skills": raw_skills,
                "seniority": fx.get("seniority"),
                "extraction_status": fx.get("extraction_status", "success"),
                "extraction_warnings": warnings,
                "extraction_tokens_used": extraction_tokens_used,
                "extraction_cost_usd": extraction_cost_usd,
                "extraction_metadata": metadata.model_dump(),
                # LLM call metadata — stub values; real data logged in Week 4
                "llm_provider": "stub",
                "llm_model": _STUB_MODEL,
                "llm_call_logged": False,
            },
        )

    def _write_extracted_intelligence(
        self,
        normalized_job_id: int,
        raw_skills: list[dict],
        raw_tools: list[dict],
        warnings: list[str],
        extraction_tokens_used: int,
        extraction_cost_usd: float,
        metadata: ExtractionMetadata,
    ) -> None:
        """Write one ExtractedIntelligence row. Never raises — DB writes must not break the pipeline."""
        try:
            with session_scope() as session:
                session.add(ExtractedIntelligence(
                    normalized_job_id=normalized_job_id,
                    extraction_version=_EXTRACTION_VERSION,
                    extraction_model=_STUB_MODEL,
                    extraction_tokens_used=extraction_tokens_used,
                    extraction_cost_usd=extraction_cost_usd,
                    skills=raw_skills,
                    tools=raw_tools,
                    tasks=[],
                    responsibilities=[],
                    context=[],
                    overall_confidence=None,
                    extraction_warnings=warnings,
                    extraction_failed=False,
                    extraction_metadata=metadata.model_dump(),
                ))
            log.info(
                "extracted_intelligence_written",
                normalized_job_id=normalized_job_id,
                skill_count=len(raw_skills),
                warning_count=len(warnings),
                cost_usd=extraction_cost_usd,
            )
        except Exception as exc:
            log.warning("extracted_intelligence_write_failed", error=str(exc))
