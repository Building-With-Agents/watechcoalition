"""Internal shared utilities for chardet."""

from __future__ import annotations

import warnings

#: Default maximum number of bytes to examine during detection.
DEFAULT_MAX_BYTES: int = 200_000

#: Default minimum confidence threshold for filtering results.
MINIMUM_THRESHOLD: float = 0.20

#: Default chunk_size value (deprecated, kept for backward-compat signatures).
_DEFAULT_CHUNK_SIZE: int = 65_536


def _warn_deprecated_chunk_size(chunk_size: int, stacklevel: int = 3) -> None:
    """Emit a deprecation warning if *chunk_size* differs from the default."""
    if chunk_size != _DEFAULT_CHUNK_SIZE:
        warnings.warn(
            "chunk_size is not used in this version of chardet and will be ignored",
            DeprecationWarning,
            stacklevel=stacklevel,
        )


def _validate_max_bytes(max_bytes: int) -> None:
    """Raise ValueError if *max_bytes* is not a positive integer."""
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        msg = "max_bytes must be a positive integer"
        raise ValueError(msg)
