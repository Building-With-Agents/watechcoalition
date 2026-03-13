"""
Normalization Agent stub — Week 2 Walking Skeleton.

Real implementation: Week 3.

In the walking skeleton this agent receives an IngestBatch event and
returns a NormalizationComplete event.  No real transformation happens;
fields are passed through with stub normalized values added.

Agent ID (canonical): normalization-agent
Emits:    NormalizationComplete
Consumes: IngestBatch

Week 3 replaces this stub with:
- Per-source field mappers to canonical JobRecord schema
- ISO 8601 date standardisation
- Salary min/max/currency/period normalisation
- Location standardisation
- Employment type inference
- Schema-violation quarantine (bad records never pass downstream)
"""

from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class NormalizationAgent(BaseAgent):
    """
    Stub for the Normalization Agent.

    Week 2: passes payload through with stub normalized fields added.
    Week 3: replaces this with real field mapping and schema enforcement.
    """

    @property
    def agent_id(self) -> str:
        return "normalization-agent"

    def health_check(self) -> dict:
        """Always ready — no external dependencies in stub mode."""
        return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept an IngestBatch event and emit a NormalizationComplete event.

        Stub adds normalized_location and employment_type fields.
        In Week 3, this is where field mapping and validation run.
        """
        p = event.payload
        batch_id = event.payload.get("batch_id")
        if not batch_id:
            log.error("normalization_missing_batch_id", payload_keys=list(event.payload.keys()))
            return self._emit_failed(
                inbound=event,
                error_type="missing_batch_id",
                error_reason="IngestBatch event missing batch_id",
            )
        latencies_ms: list[float] = []
        valid_count = 0
        quarantine_count = 0

        try:
            with SessionLocal() as session:
                raw_records = self._load_raw_records(session, batch_id)
                if not raw_records:
                    log.warning("normalization_no_raw_records", batch_id=batch_id)

                for raw_job in raw_records:
                    start = time.perf_counter()
                    try:
                        job_record = self._map_and_validate(raw_job)
                        self._write_normalized(session, job_record, raw_job, validation_status="valid")
                        valid_count += 1
                    except ValidationError as exc:
                        quarantine_count += 1
                        self._write_normalized(
                            session,
                            None,
                            raw_job,
                            validation_status="quarantined",
                            quarantine_reason=str(exc),
                        )
                        log.warning(
                            "normalization_record_quarantined",
                            batch_id=batch_id,
                        )
                    except Exception as exc:
                        quarantine_count += 1
                        self._write_normalized(
                            session,
                            None,
                            raw_job,
                            validation_status="quarantined",
                            quarantine_reason=str(exc),
                        )
                        log.error(
                            "normalization_record_error",
                            batch_id=batch_id,
                            error=str(exc),
                        )
                    finally:
                        elapsed_ms = (time.perf_counter() - start) * 1000.0
                        latencies_ms.append(elapsed_ms)

                session.commit()

        except SQLAlchemyError as exc:
            log.error(
                "normalization_batch_db_failure",
                batch_id=batch_id,
                error=str(exc),
            )
            return self._emit_failed(
                inbound=event,
                error_type="database_error",
                error_reason=str(exc),
            )
        except Exception as exc:
            log.error(
                "normalization_batch_unexpected_failure",
                batch_id=batch_id,
                error=str(exc),
            )
            return self._emit_failed(
                inbound=event,
                error_type="unknown_error",
                error_reason=str(exc),
            )

        # Compute median and p99 latency metrics.
        if latencies_ms:
            latencies_sorted = sorted(latencies_ms)
            median_ms = statistics.median(latencies_sorted)
            p99_index = max(int(len(latencies_sorted) * 0.99) - 1, 0)
            p99_ms = latencies_sorted[p99_index]
        else:
            median_ms = 0.0
            p99_ms = 0.0

        self._last_run_at = datetime.utcnow()
        self._last_run_metrics = {
            "batch_id": batch_id,
            "valid_count": valid_count,
            "quarantine_count": quarantine_count,
            "latency_median_ms": median_ms,
            "latency_p99_ms": p99_ms,
        }

        log.info(
            "normalization_latency_metrics",
            batch_id=batch_id,
            median_ms=median_ms,
            p99_ms=p99_ms,
            target_median_ms=200.0,
            target_p99_ms=1000.0,
        )

        payload = {
            "event_type": "NormalizationComplete",
            "batch_id": batch_id,
            "record_count": valid_count,
            "valid_count": valid_count,
            "quarantine_count": quarantine_count,
            "correlation_id": event.correlation_id,
        }
        outbound = EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
        return outbound
