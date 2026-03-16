"""Backward-compatibility shim — use ``agents.normalization.mappers.jsearch`` instead."""

from agents.normalization.mappers.jsearch import JSearchMapper  # noqa: F401

__all__ = ["JSearchMapper"]
