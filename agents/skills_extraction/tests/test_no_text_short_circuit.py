"""Skills Extraction short-circuits when no normalized text (no Pass-1 extractors)."""

from __future__ import annotations

from unittest.mock import patch

from agents.common.types import JobRecord
from agents.skills_extraction.agent import ExtractionWorkItem, SkillsExtractionAgent


def test_no_text_does_not_call_extract_tools_or_context() -> None:
    job = JobRecord(
        source="jsearch",
        external_id="ext-1",
        title="Title",
        company="Co",
        description=None,
        requirements=None,
        responsibilities=None,
    )
    item = ExtractionWorkItem(
        job_id=1,
        posting_id=None,
        normalized_job_id=1,
        title=job.title,
        company=job.company,
        job_record=job,
    )
    agent = SkillsExtractionAgent()
    with (
        patch("agents.skills_extraction.agent.extract_tools") as mock_tools,
        patch("agents.skills_extraction.agent.extract_context") as mock_ctx,
    ):
        tools, skills, meta, used_llm = agent._extract_work_item_no_taxonomy(item)
        mock_tools.assert_not_called()
        mock_ctx.assert_not_called()
    assert tools == []
    assert skills == []
    assert used_llm is False
    assert meta.get("error_reason") == "no_normalized_text"
    assert meta.get("extraction_status") == "failed"
