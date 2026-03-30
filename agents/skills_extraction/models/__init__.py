from __future__ import annotations

"""Backward-compatible re-exports for skills extraction models.

Canonical definitions: ``agents.common.types`` and ``extraction_schemas.py``.
"""

from agents.common.types import ContextSignal, SpanRecord

__all__ = ["SpanRecord", "ContextSignal"]
