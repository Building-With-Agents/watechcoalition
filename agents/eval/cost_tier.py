"""Resolve pricing tier labels for rows in `dbo.llm_audit_log`.

Azure OpenAI stores the **deployment name** in `model`, which often does not
contain the substrings ``sonnet`` or ``haiku``. This module mirrors the intent
of ``EXTRACTION_MODEL_TIER`` and deployment env vars used in
``agents/common/llm_client.py``.
"""

from __future__ import annotations

import os

from agents.common.llm_adapter import MODEL_TIER_MAP


def _deployment_names() -> set[str]:
    names: set[str] = set()
    for key in (
        "EXTRACTION_DEPLOYMENT_SKILLS",
        "EXTRACTION_MODEL_SKILLS",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
    ):
        v = os.getenv(key, "").strip()
        if v:
            names.add(v)
    return names


def resolve_llm_audit_model_tier(model: str | None) -> str:
    """Map ``llm_audit_log.model`` to ``haiku`` | ``sonnet`` | ``other``.

    Order: substring hints → Anthropic-style ``MODEL_TIER_MAP`` keys → exact
    match to configured Azure deployment names (tier from ``EXTRACTION_MODEL_TIER``
    or default ``sonnet``).
    """
    m = (model or "").strip()
    if not m:
        return "other"
    lower = m.lower()
    if "haiku" in lower:
        return "haiku"
    if "sonnet" in lower:
        return "sonnet"
    if m in MODEL_TIER_MAP:
        return MODEL_TIER_MAP[m]
    if m in _deployment_names():
        explicit = os.getenv("EXTRACTION_MODEL_TIER", "").strip().lower()
        if explicit in ("haiku", "sonnet"):
            return explicit
        return "sonnet"
    return "other"
