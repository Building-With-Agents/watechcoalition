"""LangGraph state definition for the Ingestion Agent."""

from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel

from agents.common.types import RawJobRecord


class SourceResult(BaseModel):
    """Result from a single source adapter fetch."""

    source_name: str
    records_fetched: int
    error: str | None = None


class IngestionState(TypedDict, total=False):
    """Typed state dict for the Ingestion Agent LangGraph graph."""

    run_id: str
    region_config: dict
    correlation_id: str
    fetched_records: list[RawJobRecord]
    source_results: list[SourceResult]
    staged_count: int
    dedup_count: int
    error_count: int
    status: str
    errors: list[str]
    batch_id: str
    ingest_batch_event: dict
