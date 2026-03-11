"""Stage 1b: HTML/XML charset declaration extraction."""

from __future__ import annotations

import codecs
import re

from chardet.pipeline import DETERMINISTIC_CONFIDENCE, DetectionResult

_SCAN_LIMIT = 4096

_XML_ENCODING_RE = re.compile(
    rb"""<\?xml[^>]+encoding\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE
)
_HTML5_CHARSET_RE = re.compile(
    rb"""<meta[^>]+charset\s*=\s*['"]?\s*([^\s'">;]+)""", re.IGNORECASE
)
_HTML4_CONTENT_TYPE_RE = re.compile(
    rb"""<meta[^>]+content\s*=\s*['"][^'"]*charset=([^\s'">;]+)""", re.IGNORECASE
)


def _normalize_encoding(name: bytes) -> str | None:
    """Validate encoding name via codecs and return the lowercased original name.

    We use ``codecs.lookup()`` to verify the encoding is recognized by Python,
    but return the original (lowercased) name rather than the codec's canonical
    name so that common aliases like ``iso-8859-1`` and ``windows-1252`` are
    preserved as-is.
    """
    try:
        text = name.decode("ascii").strip().lower()
        codecs.lookup(text)  # validate only
    except (LookupError, UnicodeDecodeError, ValueError):
        return None
    else:
        return text


def detect_markup_charset(data: bytes) -> DetectionResult | None:
    """Scan the first bytes of *data* for an HTML/XML charset declaration.

    Checks for:

    1. ``<?xml ... encoding="..."?>``
    2. ``<meta charset="...">``
    3. ``<meta http-equiv="Content-Type" content="...; charset=...">``

    :param data: The raw byte data to scan.
    :returns: A :class:`DetectionResult` with confidence 0.95, or ``None``.
    """
    if not data:
        return None

    head = data[:_SCAN_LIMIT]

    for pattern in (_XML_ENCODING_RE, _HTML5_CHARSET_RE, _HTML4_CONTENT_TYPE_RE):
        match = pattern.search(head)
        if match:
            encoding = _normalize_encoding(match.group(1))
            if encoding is not None and _validate_bytes(data, encoding):
                return DetectionResult(
                    encoding=encoding,
                    confidence=DETERMINISTIC_CONFIDENCE,
                    language=None,
                )

    return None


def _validate_bytes(data: bytes, encoding: str) -> bool:
    """Check that *data* can be decoded under *encoding* without errors.

    Only validates the first ``_SCAN_LIMIT`` bytes to avoid decoding a
    full 200 kB input just to verify a charset declaration found in the
    header.
    """
    try:
        data[:_SCAN_LIMIT].decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return False
    return True
