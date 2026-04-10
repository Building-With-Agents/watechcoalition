r"""Compare Pass-1 ``extract_context`` output to manual labels in fatima_context_temp.json.

Loads 30 eval records, builds ``JobRecord``, runs ``extract_context``.

- **Work mode (code):** ``remote_policy`` ContextSignals first; if none, fall back to
  structured ``JobRecord.city`` (``Remote`` -> Remote, any other non-empty city -> On-site),
  then title parenthetical containing ``Remote``, else undetermined.
- **Location (code):** ``city`` / ``state`` from the eval record, formatted like
  ``fatima_context_temp.json`` (``extract_context`` does not emit location).
- **Seniority (code):** title + full description/requirements heuristic (``extract_context``
  does not emit seniority).

Usage (repo root, venv active)::

    python agents/scripts/debug_context_metrics.py
"""
# ruff: noqa: T201

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path

import structlog

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from agents.common.types import ContextSignal, JobRecord
from agents.skills_extraction.extractors.context import extract_context

_EVAL_PATH = _REPO_ROOT / "agents/eval/extraction_ground_truth.json"
_MANUAL_PATH = _REPO_ROOT / "agents/eval/fatima_context_temp.json"

_STATE_ABB = {
    "texas": "TX",
    "washington": "WA",
    "california": "CA",
    "georgia": "GA",
    "new jersey": "NJ",
    "new york": "NY",
}


def _format_location_from_eval(city: object, state: object, title: str | None = None) -> str:
    """Match fatima_context_temp formatting from eval city/state (and title fallback)."""
    c = city if city is not None else None
    s = state if state is not None else None
    if not c and not s and title:
        m = re.search(r"\(([^)]*\bRemote\b[^)]*)\)", title, re.IGNORECASE)
        if m:
            inner = m.group(1).strip()
            if re.search(r"continental|united states|u\.s\.", inner, re.I):
                return "Remote (Continental US)"
            return inner
    if not c and not s:
        return "Location not specified"
    if c and str(c).lower() == "remote":
        if s and str(s).upper() not in ("US", "USA", "UNITED STATES"):
            return f"Remote ({s})"
        return "Remote"
    st = str(s) if s else ""
    if len(st) > 2:
        st = _STATE_ABB.get(st.lower(), st)
    if c and st:
        return f"{c}, {st}"
    return str(c or st or "Location not specified")


def _normalize_location(a: str, b: str) -> bool:
    """Loose equality: lower case, collapse spaces, map full state names."""

    def norm(x: str) -> str:
        t = " ".join(x.strip().lower().split())
        for full, ab in _STATE_ABB.items():
            t = re.sub(rf",\s*{re.escape(full)}\s*$", f", {ab.lower()}", t)
        return t

    return norm(a) == norm(b)


def _work_mode_from_signals(signals: list[ContextSignal]) -> str | None:
    remote_sigs = [s for s in signals if s.signal_type == "remote_policy"]
    if not remote_sigs:
        return None
    vals = [s.value.lower() for s in remote_sigs]
    joined = " ".join(vals)
    if any("hybrid" in v for v in vals):
        return "Hybrid"
    if re.search(r"on[- ]?site\s*(?:required|only)?|office[- ]based", joined):
        return "On-site"
    if any(
        k in joined
        for k in (
            "remote",
            "wfh",
            "work from home",
            "100%",
            "fully remote",
            "full-time remote",
        )
    ):
        return "Remote"
    return (
        f"— (unmapped: {remote_sigs[0].value[:48]}…)"
        if len(remote_sigs[0].value) > 48
        else f"— (unmapped: {remote_sigs[0].value})"
    )


def _work_mode_code(signals: list[ContextSignal], job: JobRecord) -> str:
    from_sig = _work_mode_from_signals(signals)
    if from_sig in ("Hybrid", "Remote", "On-site"):
        return from_sig

    def _from_structured() -> str | None:
        city = (job.city or "").strip().lower()
        if city == "remote":
            return "Remote"
        if city:
            return "On-site"
        tl = job.title or ""
        if re.search(r"\([^)]*\bremote\b[^)]*\)", tl, re.IGNORECASE):
            return "Remote"
        return None

    if from_sig and from_sig.startswith("— (unmapped"):
        fb = _from_structured()
        if fb is not None:
            return fb
        return from_sig

    fb = _from_structured()
    if fb is not None:
        return fb
    return "— (undetermined)"


def _seniority_heuristic(title: str, blob: str) -> str:
    """Rough bucket for comparison to manual (not from extract_context)."""
    tl = (title or "").lower()
    # Full body: year/requirements bullets often appear after the first ~3k chars.
    bl = (blob or "").lower()
    if re.search(r"\b(intern|internship)\b", tl):
        return "Junior"
    if re.search(r"\b(junior|jr\.)\b", tl):
        return "Junior"
    if re.search(r"entry[- ]level|entry level", tl) or (
        "entry level" in bl[:1200] and re.search(r"\b(analyst|developer|engineer)\b", tl)
    ):
        return "Junior"
    if re.search(r"\banalyst\s+i\b|\bdeveloper\s+i\b|\bassociate\s+i\b|\(entry level\)", tl):
        return "Junior"
    if re.search(r"\b(senior|sr\.)\b", tl):
        return "Senior"
    if re.search(r"\bstaff\b", tl) or re.search(r"\bprincipal\b", tl):
        return "Senior"
    if re.search(r"\b(director|vp |vice president|head of)\b", tl):
        return "Lead"
    if re.search(r"\b(lead|team lead|tech lead)\b", tl) and "manager" not in tl:
        return "Lead"
    if "manager" in tl and re.search(r"leadership|grc manager", tl):
        return "Lead"
    if re.search(r"\b5\+\s*years|\b7\+\s*years", bl) and re.search(r"engineer|scientist", tl):
        return "Senior"
    if "senior individual contributor" in bl or re.search(r"\bsenior\s+individual\s+contributor\b", bl):
        return "Senior"
    if re.search(r"\b>\s*1[01]\s*years|1[01]\+\s*years|\b1[12]\s*\+\s*years", bl):
        return "Senior"
    if re.search(r"\b(ii|iii)\b", tl) and "engineer" in tl:
        return "Senior" if "iii" in tl else "Mid"
    return "Mid"


def _eval_to_job(record: dict) -> JobRecord:
    ext = record.get("external_id") or record.get("ground_truth_id")
    if not ext:
        raise ValueError("record missing external_id and ground_truth_id")
    return JobRecord(
        source=str(record.get("source") or "eval"),
        external_id=str(ext),
        title=str(record.get("title") or "Untitled"),
        company=str(record.get("company") or "Unknown"),
        description=record.get("description"),
        requirements=record.get("requirements"),
        responsibilities=record.get("responsibilities"),
        city=record.get("city"),
        state_province=record.get("state"),
    )


def main() -> int:
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR),
    )

    eval_rows = json.loads(_EVAL_PATH.read_text(encoding="utf-8"))
    manual = json.loads(_MANUAL_PATH.read_text(encoding="utf-8"))

    if len(eval_rows) != 30:
        print(f"Expected 30 eval records, got {len(eval_rows)}", file=sys.stderr)
        return 1

    loc_hits = wm_hits = sen_hits = 0
    mismatch_rows: list[tuple[str, str, str, str]] = []

    print("Notes:")
    print(
        "  • Work mode (code) = remote_policy signals, else city=Remote -> Remote, else title (…Remote…) -> Remote, else On-site."
    )
    print("  • Location (code) = city/state from eval JSON (same basis as fatima labels).")
    print("  • Seniority (code) = title/body heuristic (extract_context has no seniority).")
    print()

    for rec in eval_rows:
        ext = rec.get("external_id") or rec.get("ground_truth_id")
        if ext not in manual:
            print(f"Missing manual entry for {ext}", file=sys.stderr)
            return 1
        m = manual[ext]
        man_loc = m["location"]
        man_wm = m["work_mode"]
        man_sen = m["seniority"]

        job = _eval_to_job(rec)
        signals, _meta = extract_context(job)
        code_wm = _work_mode_code(signals, job)
        code_loc = _format_location_from_eval(rec.get("city"), rec.get("state"), rec.get("title"))
        blob = f"{rec.get('title', '')}\n{rec.get('description', '')}"
        code_sen = _seniority_heuristic(rec.get("title") or "", blob)

        loc_ok = _normalize_location(man_loc, code_loc)
        wm_ok = man_wm == code_wm
        sen_ok = man_sen == code_sen

        if loc_ok:
            loc_hits += 1
        if wm_ok:
            wm_hits += 1
        if sen_ok:
            sen_hits += 1

        if not (loc_ok and wm_ok and sen_ok):
            parts = []
            if not loc_ok:
                parts.append(f"location manual={man_loc!r} code={code_loc!r}")
            if not wm_ok:
                parts.append(f"work_mode manual={man_wm!r} code={code_wm!r}")
            if not sen_ok:
                parts.append(f"seniority manual={man_sen!r} code={code_sen!r}")
            mismatch_rows.append((ext, man_loc, man_wm, man_sen, code_loc, code_wm, code_sen, " | ".join(parts)))

    n = len(eval_rows)
    print(f"Accuracy (n={n}):")
    print(f"  Location:  {loc_hits}/{n}  ({100.0 * loc_hits / n:.1f}%)")
    print(f"  Work mode: {wm_hits}/{n}  ({100.0 * wm_hits / n:.1f}%)")
    print(f"  Seniority: {sen_hits}/{n}  ({100.0 * sen_hits / n:.1f}%)")
    print()
    print(
        "Mismatches (external_id | manual location | manual WM | manual sen | code location | code WM | code sen | diff)"
    )
    print("-" * 120)
    if not mismatch_rows:
        print("(none — all records match on all three dimensions)")
    else:
        for row in mismatch_rows:
            ext, ml, mm, ms, cl, cw, cs, diff = row
            print(f"{ext}")
            print(f"  manual:  loc={ml!r}  work_mode={mm!r}  seniority={ms!r}")
            print(f"  code:    loc={cl!r}  work_mode={cw!r}  seniority={cs!r}")
            print(f"  diff:    {diff}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
