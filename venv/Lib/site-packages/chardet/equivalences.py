"""Encoding equivalences and legacy name remapping.

This module defines:

1. **Directional supersets** for accuracy evaluation: detecting a superset
   encoding when the expected encoding is a subset is correct (e.g., detecting
   utf-8 when expected is ascii), but not the reverse.

2. **Bidirectional equivalents**: groups of encodings where detecting any
   member when another member was expected is considered correct.  This
   includes UTF-16/UTF-32 endian variants (which encode the same text with
   different byte order) and ISO-2022-JP branch variants (which are
   compatible extensions of the same base encoding).

3. **Preferred superset mapping** for the ``should_rename_legacy`` API option:
   replaces detected ISO/subset encoding names with their Windows/CP superset
   equivalents that modern software actually uses.
"""

from __future__ import annotations

import codecs
import unicodedata

from chardet.pipeline import DetectionDict


def normalize_encoding_name(name: str) -> str:
    """Normalize encoding name for comparison.

    :param name: The encoding name to normalize.
    :returns: The canonical codec name, or a lowered/stripped fallback.
    """
    try:
        return codecs.lookup(name).name
    except LookupError:
        return name.lower().replace("-", "").replace("_", "")


# Directional superset relationships: detecting any of the supersets
# when the expected encoding is the subset counts as correct.
# E.g., expected=ascii, detected=utf-8 -> correct (utf-8 ⊃ ascii).
# But expected=utf-8, detected=ascii -> wrong (ascii ⊄ utf-8).
#
# Note: some subset keys (iso-8859-11) are not in the detection
# registry — the detector never returns them.  They appear here because
# chardet test-suite expected values use these names, so the superset
# mapping is needed for accuracy evaluation only.
SUPERSETS: dict[str, frozenset[str]] = {
    "ascii": frozenset({"utf-8", "windows-1252"}),
    "tis-620": frozenset({"iso-8859-11", "cp874"}),
    "iso-8859-11": frozenset({"cp874"}),
    "gb2312": frozenset({"gb18030"}),
    "gbk": frozenset({"gb18030"}),
    "big5": frozenset({"big5hkscs", "cp950"}),
    "shift_jis": frozenset({"cp932", "shift_jis_2004"}),
    "shift-jisx0213": frozenset({"shift_jis_2004"}),
    "euc-jp": frozenset({"euc-jis-2004"}),
    "euc-jisx0213": frozenset({"euc-jis-2004"}),
    "euc-kr": frozenset({"cp949"}),
    "cp037": frozenset({"cp1140"}),
    # ISO-2022-JP subsets: any branch variant is acceptable
    "iso-2022-jp": frozenset({"iso2022-jp-2", "iso2022-jp-2004", "iso2022-jp-ext"}),
    "iso2022-jp-1": frozenset({"iso2022-jp-2", "iso2022-jp-ext"}),
    "iso2022-jp-3": frozenset({"iso2022-jp-2004"}),
    # ISO/Windows superset pairs
    "iso-8859-1": frozenset({"windows-1252"}),
    "iso-8859-2": frozenset({"windows-1250"}),
    "iso-8859-5": frozenset({"windows-1251"}),
    "iso-8859-6": frozenset({"windows-1256"}),
    "iso-8859-7": frozenset({"windows-1253"}),
    "iso-8859-8": frozenset({"windows-1255"}),
    "iso-8859-9": frozenset({"windows-1254"}),
    "iso-8859-13": frozenset({"windows-1257"}),
}

# Preferred superset name for each encoding, used by the ``should_rename_legacy``
# API option.  When enabled, detected encoding names are replaced with the
# Windows/CP superset that modern software actually uses (browsers, editors,
# etc. treat these ISO subsets as their Windows counterparts).
# Values use display-cased names (e.g. "Windows-1252") to match chardet 6.x output.
PREFERRED_SUPERSET: dict[str, str] = {
    "ascii": "Windows-1252",
    "euc-kr": "CP949",
    "iso-8859-1": "Windows-1252",
    "iso-8859-2": "Windows-1250",
    "iso-8859-5": "Windows-1251",
    "iso-8859-6": "Windows-1256",
    "iso-8859-7": "Windows-1253",
    "iso-8859-8": "Windows-1255",
    "iso-8859-9": "Windows-1254",
    "iso-8859-11": "CP874",
    "iso-8859-13": "Windows-1257",
    "tis-620": "CP874",
}


def apply_legacy_rename(
    result: DetectionDict,
) -> DetectionDict:
    """Replace the encoding name with its preferred Windows/CP superset.

    Modifies the ``"encoding"`` value in *result* in-place and returns *result*
    for fluent chaining.

    :param result: A detection result dict containing an ``"encoding"`` key.
    :returns: The same *result* dict, modified in-place.
    """
    enc = result.get("encoding")
    if isinstance(enc, str):
        result["encoding"] = PREFERRED_SUPERSET.get(enc.lower(), enc)
    return result


# Bidirectional equivalents -- groups where any member is acceptable for any other.
BIDIRECTIONAL_GROUPS: tuple[tuple[str, ...], ...] = (
    ("utf-16", "utf-16-le", "utf-16-be"),
    ("utf-32", "utf-32-le", "utf-32-be"),
    ("iso2022-jp-2", "iso2022-jp-2004", "iso2022-jp-ext"),
)

# Bidirectional language equivalences — groups of ISO 639-1 codes for
# languages that are nearly indistinguishable by statistical detection.
# Detecting any member when another member of the same group was expected
# is considered acceptable.
LANGUAGE_EQUIVALENCES: tuple[tuple[str, ...], ...] = (
    ("sk", "cs"),  # Slovak / Czech — ~85% mutual intelligibility
    (
        "uk",
        "ru",
        "bg",
        "be",
    ),  # East Slavic + Bulgarian — shared Cyrillic, high written overlap
    ("ms", "id"),  # Malay / Indonesian — standardized variants of one language
    (
        "no",
        "da",
        "sv",
    ),  # Scandinavian — mutual intelligibility across the dialect continuum
)


def _build_language_equiv_index() -> dict[str, frozenset[str]]:
    """Build a lookup: ISO code -> frozenset of all equivalent ISO codes."""
    result: dict[str, frozenset[str]] = {}
    for group in LANGUAGE_EQUIVALENCES:
        group_set = frozenset(group)
        for code in group:
            result[code] = group_set
    return result


_LANGUAGE_EQUIV: dict[str, frozenset[str]] = _build_language_equiv_index()


def is_language_equivalent(expected: str, detected: str) -> bool:
    """Check whether *detected* is an acceptable language for *expected*.

    Returns ``True`` when *expected* and *detected* are the same ISO 639-1
    code, or belong to the same equivalence group in
    :data:`LANGUAGE_EQUIVALENCES`.

    :param expected: Expected ISO 639-1 language code.
    :param detected: Detected ISO 639-1 language code.
    :returns: ``True`` if the languages are equivalent.
    """
    if expected == detected:
        return True
    group = _LANGUAGE_EQUIV.get(expected)
    return group is not None and detected in group


# Pre-built normalized lookups for fast comparison.
_NORMALIZED_SUPERSETS: dict[str, frozenset[str]] = {
    normalize_encoding_name(subset): frozenset(
        normalize_encoding_name(s) for s in supersets
    )
    for subset, supersets in SUPERSETS.items()
}


def _build_bidir_index() -> dict[str, frozenset[str]]:
    """Build the bidirectional equivalence lookup index."""
    result: dict[str, frozenset[str]] = {}
    for group in BIDIRECTIONAL_GROUPS:
        normed = frozenset(normalize_encoding_name(n) for n in group)
        for name in group:
            result[normalize_encoding_name(name)] = normed
    return result


_NORMALIZED_BIDIR: dict[str, frozenset[str]] = _build_bidir_index()


def is_correct(expected: str | None, detected: str | None) -> bool:
    """Check whether *detected* is an acceptable answer for *expected*.

    Acceptable means:

    1. Exact match (after normalization), OR
    2. Both belong to the same bidirectional byte-order group, OR
    3. *detected* is a known superset of *expected*.

    :param expected: The expected encoding name, or ``None`` for binary files.
    :param detected: The detected encoding name, or ``None``.
    :returns: ``True`` if the detection is acceptable.
    """
    if expected is None:
        return detected is None
    if detected is None:
        return False
    norm_exp = normalize_encoding_name(expected)
    norm_det = normalize_encoding_name(detected)

    # 1. Exact match
    if norm_exp == norm_det:
        return True

    # 2. Bidirectional (same byte-order group)
    if norm_exp in _NORMALIZED_BIDIR and norm_det in _NORMALIZED_BIDIR[norm_exp]:
        return True

    # 3. Superset is acceptable (detected is a known superset of expected)
    return (
        norm_exp in _NORMALIZED_SUPERSETS
        and norm_det in _NORMALIZED_SUPERSETS[norm_exp]
    )


def _strip_combining(text: str) -> str:
    """NFKD-normalize *text* and strip all combining marks."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Pre-computed symbol pair lookups for O(1) equivalence checks.
# Both orderings are stored to avoid constructing temporaries per call.
_EQUIVALENT_SYMBOL_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("¤", "€"),
        ("€", "¤"),
    }
)


def _chars_equivalent(a: str, b: str) -> bool:
    """Return True if characters *a* and *b* are functionally equivalent.

    Equivalent means:
    - Same character, OR
    - Same base letter after stripping combining marks, OR
    - An explicitly listed symbol equivalence (e.g. ¤ ↔ €)
    """
    if a == b:
        return True
    if (a, b) in _EQUIVALENT_SYMBOL_PAIRS:
        return True
    # Compare base letters after stripping combining marks.
    return _strip_combining(a) == _strip_combining(b)


def is_equivalent_detection(
    data: bytes, expected: str | None, detected: str | None
) -> bool:
    """Check whether *detected* produces functionally identical text to *expected*.

    Returns ``True`` when:

    1. *detected* is not ``None`` and both encoding names normalize to the same
       codec, OR
    2. Decoding *data* with both encodings yields identical strings, OR
    3. Every differing character pair is functionally equivalent: same base
       letter after stripping combining marks, or an explicitly listed symbol
       equivalence (e.g. ¤ ↔ €).

    Returns ``False`` if *detected* is ``None``, either encoding is unknown,
    or either encoding cannot decode *data*.

    :param data: The raw byte data that was detected.
    :param expected: The expected encoding name, or ``None`` for binary files.
    :param detected: The detected encoding name, or ``None``.
    :returns: ``True`` if decoding with *detected* yields functionally identical
        text to decoding with *expected*.
    """
    if expected is None:
        return detected is None
    if detected is None:
        return False

    norm_exp = normalize_encoding_name(expected)
    norm_det = normalize_encoding_name(detected)

    if norm_exp == norm_det:
        return True

    try:
        text_exp = data.decode(norm_exp)
        text_det = data.decode(norm_det)
    except (UnicodeDecodeError, LookupError):
        return False

    if text_exp == text_det:
        return True

    if len(text_exp) != len(text_det):
        return False

    return all(_chars_equivalent(a, b) for a, b in zip(text_exp, text_det, strict=True))
