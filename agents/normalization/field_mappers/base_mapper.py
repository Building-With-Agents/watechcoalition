"""Backward-compatibility shim — use ``agents.normalization.mappers.base`` instead."""

from agents.normalization.mappers.base import FieldMapper, MapperBase  # noqa: F401

__all__ = ["FieldMapper", "MapperBase"]
