"""Abstract base for per-source field mappers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class FieldMapper(ABC):
    """Maps raw source-specific fields to canonical normalized fields."""

    @abstractmethod
    def map(self, raw: dict) -> dict:
        """Transform a raw record dict into canonical field names.

        Returns a dict suitable for constructing a ``JobRecord``.
        """
