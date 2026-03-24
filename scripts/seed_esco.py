#!/usr/bin/env python3
from __future__ import annotations
# ruff: noqa: E402  -- module docstring must be first; imports follow

"""
Seed ESCO digital skills data from the official English CSV package.

What this script does
---------------------
1. Downloads the official ESCO English CSV ZIP if a URL is provided.
2. Or reuses an already-extracted local folder.
3. Reads:
      - digitalSkillsCollection_en.csv
      - skills_en.csv
4. Builds a normalized JSON store at taxonomy/esco_digital_skills.json.
5. Optionally seeds the records into PostgreSQL.

Why this shape
--------------
- The ESCO portal supports CSV downloads and API access; for a one-time setup
  seed, the English CSV package is the simplest and most reproducible option. 
- ESCO's digital label is an official subset of the skills pillar, so this
  script treats digitalSkillsCollection_en.csv as the authoritative digital
  subset and enriches each row from skills_en.csv. 

Expected inputs
---------------
Either:
  A) --download-url <official_esco_zip_url>
     The ZIP should extract to a directory containing the two required CSVs.
Or:
  B) --extracted-dir <folder>
     A local extracted folder that already contains the CSVs.

Expected outputs
----------------
- taxonomy/esco_digital_skills.json
- taxonomy/esco_source_metadata.json
- optional database rows in dbo.esco_digital_skills when --seed-db is used

Typical usage
-------------
Using a local extracted folder:
    python scripts/seed_esco.py \
      --extracted-dir "/path/to/ESCO dataset - v1.2.1 - classification - en - csv"

Using a download URL:
    python scripts/seed_esco.py \
      --download-url "<official_esco_zip_url>"

Using PostgreSQL too:
    python scripts/seed_esco.py \
      --extracted-dir "/path/to/esco" \
      --seed-db \
      --db-url "$PYTHON_DATABASE_URL"

Optional environment:
    ESCO_SEED_APPLY_FILTER=1   If set, run filter_records() then merge any ESCO
    concepts whose preferred_label matches a GenAI extension parent (so nodes
    like the official \"machine learning\" knowledge skill are not dropped).
"""

import argparse
import csv
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from dotenv import load_dotenv

load_dotenv()

try:
    from sqlalchemy import create_engine, text
except Exception:  # pragma: no cover - SQLAlchemy may not be available in all envs
    create_engine = None
    text = None

DIGITAL_COLLECTION_FILENAME = Path(__file__).parent.parent / "agents" / "skills_extraction" / "taxonomy" / "digitalSkillsCollection_en.csv"
SKILLS_FILENAME = Path(__file__).parent.parent / "agents" / "skills_extraction" / "taxonomy" / "skills_en.csv"
DEFAULT_OUTPUT_JSON = Path(__file__).parent.parent / "agents" / "skills_extraction" / "taxonomy" / "esco_digital_skills.json"
DEFAULT_METADATA_JSON = Path(__file__).parent.parent / "agents" / "skills_extraction" / "taxonomy" / "esco_source_metadata.json"
DEFAULT_GENAI_EXTENSION_JSON = (
    Path(__file__).parent.parent / "agents" / "skills_extraction" / "taxonomy" / "genai_extension.json"
)
DEFAULT_DB_TABLE = "esco_digital_skills"


KEEP_PARENT_LABELS = {
    "computer programming",
    "software and applications development and analysis",
    "designing ict systems or applications",
    "managing, gathering and storing digital data",
    "database and network design and administration",
    "web programming",
    "protecting ict devices",
    "ict infrastructure",
    "tools for software configuration management",
    "data extraction, transformation and loading tools",
    "query languages",
    "style sheet languages",
    "integrated development environment software",
    "software design methodologies",
    "software interaction design",
    "programming computer systems",
    "maintain ict system",
    "setting up computer systems",
    "resolving computer problems",
    "problem-solving with digital tools",
    "use databases",
    "store digital data and systems",
    "create digital content",
    "using digital tools for collaboration and productivity",
    "technology evaluation",
    "quality assurance",
    "systems integration",
    "information retrieval",
    "machine learning",
    "database management",
    "digital ethics",
}

# Tighter second-pass filter:
# exclude broad end-user / office / media-ish / non-core categories that still slip through.
EXCLUDE_PARENT_LABELS = {
    "office software",
    "use office systems",
    "using digital tools for collaboration and productivity",
    "create digital content",
    "digital content creation tools",
    "audio-visual techniques and media production",
    "marketing and advertising",
    "journalism and reporting",
    "sales activities",
    "hotel, restaurants and catering",
    "transport services",
    "education science",
}

# Optional keyword denylist for labels that are usually too broad or off-target
EXCLUDE_LABEL_KEYWORDS = {
    "spreadsheet",
    "word processor",
    "presentation software",
    "desktop publishing",
    "video editing",
    "photo editing",
    "social media",
    "accounting software",
    "point of sale",
    "cash register",
    "office suite",
}

# Optional keyword allowlist for strong technical relevance
INCLUDE_LABEL_KEYWORDS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "sql",
    "haskell",
    "scala",
    "c++",
    "c#",
    "docker",
    "kubernetes",
    "linux",
    "git",
    "api",
    "database",
    "query",
    "cloud",
    "network",
    "security",
    "machine learning",
    "data engineering",
    "etl",
    "devops",
    "programming",
    "software",
    "web",
}

@dataclass(frozen=True)
class Config:
    download_url: str | None
    extracted_dir: Path | None
    output_json: Path
    metadata_json: Path
    keep_workdir: bool
    timeout_seconds: int
    seed_db: bool
    db_url: str | None
    db_table: str


def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="Seed ESCO digital skills from English CSV data")
    parser.add_argument(
        "--download-url",
        default=None,
        help="Official ESCO ZIP URL. Omit this when using --extracted-dir.",
    )
    parser.add_argument(
        "--extracted-dir",
        default=None,
        help="Path to an already-extracted ESCO English CSV directory.",
    )
    parser.add_argument(
        "--output-json",
        default=str(DEFAULT_OUTPUT_JSON),
        help="Path for the derived ESCO digital skills JSON file.",
    )
    parser.add_argument(
        "--metadata-json",
        default=str(DEFAULT_METADATA_JSON),
        help="Path for the source metadata JSON file.",
    )
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Keep the temporary download/extraction directory after the run.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=120,
        help="HTTP timeout for ZIP download.",
    )
    parser.add_argument(
        "--seed-db",
        action="store_true",
        help="Also seed the derived records into PostgreSQL.",
    )
    parser.add_argument(
        "--db-url",
        default=None,
        help="PostgreSQL SQLAlchemy URL. Defaults to PYTHON_DATABASE_URL if omitted.",
    )
    parser.add_argument(
        "--db-table",
        default=DEFAULT_DB_TABLE,
        help="Destination Postgres table when --seed-db is enabled.",
    )
    args = parser.parse_args()

    if not args.download_url and not args.extracted_dir:
        if not DIGITAL_COLLECTION_FILENAME.exists() or not SKILLS_FILENAME.exists():
            parser.error(
                "Provide either --download-url or --extracted-dir, or place "
                "digitalSkillsCollection_en.csv and skills_en.csv under "
                "agents/skills_extraction/taxonomy/"
            )

    return Config(
        download_url=args.download_url,
        extracted_dir=Path(args.extracted_dir).expanduser().resolve() if args.extracted_dir else None,
        output_json=Path(args.output_json),
        metadata_json=Path(args.metadata_json),
        keep_workdir=args.keep_workdir,
        timeout_seconds=args.timeout_seconds,
        seed_db=args.seed_db,
        db_url=args.db_url or os.getenv("PYTHON_DATABASE_URL"),
        db_table=args.db_table,
    )


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def normalize_text(value: str | None) -> str:
    """Normalize labels for deterministic matching later.

    This intentionally stays conservative:
    - NFKC Unicode normalization
    - lowercase
    - strip outer whitespace
    - collapse internal repeated whitespace

    It avoids stemming here because the seed store should preserve the canonical
    labels; stemming can be applied later in the resolver if the team wants it.
    """
    text_value = unicodedata.normalize("NFKC", value or "")
    text_value = text_value.lower().strip()
    text_value = re.sub(r"\s+", " ", text_value)
    return text_value


def split_multivalue(value: str | None) -> list[str]:
    """Split ESCO multi-value fields into a clean list.

    In the English CSV export, altLabels commonly arrive newline-separated.
    We also support ';' and '|' defensively.
    """
    if not value:
        return []
    parts = re.split(r"[\n;|]+", value)
    return [part.strip() for part in parts if part and part.strip()]


def split_pipe_field(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split("|") if part and part.strip()]


def download_zip(download_url: str, destination: Path, timeout_seconds: int) -> Path:
    ensure_parent(destination)
    with urllib.request.urlopen(download_url, timeout=timeout_seconds) as response:
        if getattr(response, "status", 200) >= 400:
            raise RuntimeError(f"Failed to download ESCO ZIP: HTTP {response.status}")
        destination.write_bytes(response.read())
    return destination


def extract_zip(zip_path: Path, extract_dir: Path) -> Path:
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(extract_dir)
    return extract_dir


def find_required_csvs(root_dir: Path) -> tuple[Path, Path]:
    # First: prefer the repo-local files you explicitly configured
    if DIGITAL_COLLECTION_FILENAME.exists() and SKILLS_FILENAME.exists():
        return DIGITAL_COLLECTION_FILENAME, SKILLS_FILENAME

    # Fallback: search within an extracted ESCO folder
    digital_matches = list(root_dir.rglob("digitalSkillsCollection_en.csv"))
    skills_matches = list(root_dir.rglob("skills_en.csv"))

    if not digital_matches:
        raise FileNotFoundError(f"Could not find digitalSkillsCollection_en.csv under {root_dir}")
    if not skills_matches:
        raise FileNotFoundError(f"Could not find skills_en.csv under {root_dir}")

    digital_csv = sorted(digital_matches, key=lambda p: len(str(p)))[0]
    skills_csv = sorted(skills_matches, key=lambda p: len(str(p)))[0]
    return digital_csv, skills_csv


def load_skills_by_uri(skills_csv_path: Path) -> dict[str, dict[str, str]]:
    """Load skills_en.csv as a lookup keyed by conceptUri.

    Reused logic:
    - The join key is conceptUri.
    - skills_en.csv provides extra metadata not guaranteed in the digital subset,
      especially hiddenLabels, definition, and scopeNote.
    """
    skills_by_uri: dict[str, dict[str, str]] = {}
    with skills_csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"conceptUri", "preferredLabel", "altLabels", "hiddenLabels", "definition", "scopeNote", "description"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"skills_en.csv missing expected columns: {sorted(missing)}")
        for row in reader:
            uri = (row.get("conceptUri") or "").strip()
            if uri:
                skills_by_uri[uri] = row
    return skills_by_uri


def load_digital_rows(digital_csv_path: Path) -> list[dict[str, str]]:
    with digital_csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "conceptUri",
            "preferredLabel",
            "skillType",
            "reuseLevel",
            "altLabels",
            "description",
            "broaderConceptUri",
            "broaderConceptPT",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"digitalSkillsCollection_en.csv missing expected columns: {sorted(missing)}"
            )
        return list(reader)


def build_record(digital_row: dict[str, str], skills_by_uri: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Build one final ESCO digital skill record.

    Output shape is designed for the Week 4 taxonomy resolver:
    - exact match support: preferred_label
    - normalized match support: normalized_label + normalized_alt_labels
    - semantic match support later: stable ESCO URI + descriptive metadata
    - GenAI parent-cluster work later: broader_concept_* fields preserved
    """
    uri = (digital_row.get("conceptUri") or "").strip()
    if not uri:
        raise ValueError("digital row missing conceptUri")

    skill_row = skills_by_uri.get(uri, {})

    preferred_label = (digital_row.get("preferredLabel") or "").strip()
    alt_labels = split_multivalue(digital_row.get("altLabels"))
    hidden_labels = split_multivalue(skill_row.get("hiddenLabels"))
    broader_uris = split_pipe_field(digital_row.get("broaderConceptUri"))
    broader_labels = split_pipe_field(digital_row.get("broaderConceptPT"))

    # Use the richer description from the digital collection when present; fall
    # back to the master skills table otherwise.
    description = (digital_row.get("description") or skill_row.get("description") or "").strip()
    definition = (skill_row.get("definition") or "").strip()
    scope_note = (skill_row.get("scopeNote") or "").strip()

    return {
        "concept_type": (digital_row.get("conceptType") or "").strip(),
        "esco_uri": uri,
        "preferred_label": preferred_label,
        "normalized_label": normalize_text(preferred_label),
        "skill_type": (digital_row.get("skillType") or "").strip(),
        "reuse_level": (digital_row.get("reuseLevel") or "").strip(),
        "status": (digital_row.get("status") or "").strip(),
        "alt_labels": alt_labels,
        "normalized_alt_labels": [normalize_text(label) for label in alt_labels],
        "hidden_labels": hidden_labels,
        "normalized_hidden_labels": [normalize_text(label) for label in hidden_labels],
        "description": description,
        "definition": definition,
        "scope_note": scope_note,
        "broader_concept_uris": broader_uris,
        "broader_concept_labels": broader_labels,
    }


def build_records(digital_rows: Iterable[dict[str, str]], skills_by_uri: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen_uris: set[str] = set()

    for row in digital_rows:
        record = build_record(row, skills_by_uri)
        if record["esco_uri"] in seen_uris:
            # Defensive dedupe in case a future ESCO export duplicates rows.
            continue
        seen_uris.add(record["esco_uri"])
        records.append(record)

    records.sort(key=lambda item: (item["preferred_label"].lower(), item["esco_uri"]))
    return records


def write_json(records: list[dict[str, Any]], output_json: Path) -> None:
    ensure_parent(output_json)
    with output_json.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)


def write_metadata(
    metadata_json: Path,
    *,
    download_url: str | None,
    digital_csv_path: Path,
    skills_csv_path: Path,
    record_count: int,
) -> None:
    ensure_parent(metadata_json)
    metadata = {
        "source": {
            "download_url": download_url,
            "digital_collection_file": str(digital_csv_path),
            "skills_file": str(skills_csv_path),
        },
        "version_note": "Expected source package: ESCO English CSV export",
        "record_count": record_count,
    }
    with metadata_json.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, ensure_ascii=False)

def filter_records(records: list[dict]) -> list[dict]:
    """
    Narrow the full ESCO digital collection to a tighter Week 4 working set.

    Strategy:
    1. Keep records whose broader_concept_labels intersect with KEEP_PARENT_LABELS
    2. Exclude records whose parent labels intersect with EXCLUDE_PARENT_LABELS
    3. Exclude records whose preferred_label looks too broad / office / media / end-user oriented
    4. Keep records with strong technical signal in label OR in kept parent groups

    Returns a filtered list of records.
    """
    filtered: list[dict] = []

    for item in records:
        normalized_label = (item.get("normalized_label") or "").strip()
        parents = {x.strip().lower() for x in item.get("broader_concept_labels", []) if x.strip()}

        # Step 1: must belong to at least one core technical parent group
        if not (parents & KEEP_PARENT_LABELS):
            continue

        # Step 2: reject if it belongs to an explicitly excluded parent group
        if parents & EXCLUDE_PARENT_LABELS:
            continue

        # Step 3: reject by label keyword if it looks too non-core
        if any(keyword in normalized_label for keyword in EXCLUDE_LABEL_KEYWORDS):
            continue

        # Step 4: stronger keep rule
        # Keep if:
        # - it has a strong technical keyword in the label, OR
        # - it belongs to one of the especially strong technical parent groups
        strong_parent_groups = {
            "computer programming",
            "software and applications development and analysis",
            "database and network design and administration",
            "machine learning",
            "protecting ict devices",
            "data extraction, transformation and loading tools",
            "query languages",
            "ict infrastructure",
            "systems integration",
            "database management",
            "web programming",
        }

        has_strong_label_signal = any(keyword in normalized_label for keyword in INCLUDE_LABEL_KEYWORDS)
        has_strong_parent_signal = bool(parents & strong_parent_groups)

        if not (has_strong_label_signal or has_strong_parent_signal):
            continue

        filtered.append(item)

    # Optional dedup by ESCO URI, just to be safe
    deduped: list[dict] = []
    seen_uris: set[str] = set()

    for item in filtered:
        uri = item.get("esco_uri")
        if not uri or uri in seen_uris:
            continue
        seen_uris.add(uri)
        deduped.append(item)

    return deduped


def merge_missing_genai_parent_concepts(
    universe: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    genai_json: Path | None = None,
) -> list[dict[str, Any]]:
    """Re-insert ESCO records needed for GenAI Extension parent URIs after filtering.

    ``filter_records`` keeps rows by *broader* parent labels. Official ESCO nodes
    such as the knowledge \"machine learning\" often have broader labels like
    \"principles of artificial intelligence\" — not the string \"machine learning\"
    — so they can be dropped even though ``genai_extension.json`` names
    \"Machine learning\" as a parent. This pass adds any universe row whose
    ``preferred_label`` matches a GenAI parent string (normalized) if missing
    from ``selected``.
    """
    path = genai_json or DEFAULT_GENAI_EXTENSION_JSON
    parents_norm: set[str] = set()
    if path.exists():
        blob = json.loads(path.read_text(encoding="utf-8"))
        for _, parent_label in blob.items():
            parents_norm.add(normalize_text(str(parent_label)))
    if not parents_norm:
        return selected

    selected_uris = {r["esco_uri"] for r in selected if r.get("esco_uri")}
    pref_to_rec: dict[str, dict[str, Any]] = {}
    for r in universe:
        pl = (r.get("preferred_label") or "").strip()
        if not pl:
            continue
        k = normalize_text(pl)
        pref_to_rec.setdefault(k, r)

    extra: list[dict[str, Any]] = []
    for pn in parents_norm:
        rec = pref_to_rec.get(pn)
        if rec and rec.get("esco_uri") and rec["esco_uri"] not in selected_uris:
            extra.append(rec)
            selected_uris.add(rec["esco_uri"])
    if not extra:
        return selected

    merged = list(selected) + extra
    merged.sort(key=lambda item: (item["preferred_label"].lower(), item["esco_uri"]))
    return merged


def ensure_db_support() -> None:
    if create_engine is None or text is None:
        raise RuntimeError("SQLAlchemy is not available; cannot use --seed-db")


def parse_schema_and_table(qualified_name: str) -> tuple[str, str]:
    if "." in qualified_name:
        schema, table = qualified_name.split(".", 1)
        return schema, table
    return "public", qualified_name


def seed_postgres(records: list[dict[str, Any]], db_url: str, db_table: str) -> None:
    """Seed Postgres with one row per ESCO digital skill.

    Table shape intentionally mirrors the JSON store closely so your taxonomy
    code can later choose either file-based or DB-backed lookup.
    """
    ensure_db_support()
    if not db_url:
        raise RuntimeError("--seed-db requires --db-url or PYTHON_DATABASE_URL")

    schema, table = parse_schema_and_table(db_table)
    engine = create_engine(db_url)

    create_schema_sql = text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    create_table_sql = text(
        f'''
        CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (
            esco_uri TEXT PRIMARY KEY,
            preferred_label TEXT NOT NULL,
            normalized_label TEXT NOT NULL,
            skill_type TEXT,
            reuse_level TEXT,
            status TEXT,
            alt_labels JSONB NOT NULL DEFAULT '[]'::jsonb,
            normalized_alt_labels JSONB NOT NULL DEFAULT '[]'::jsonb,
            hidden_labels JSONB NOT NULL DEFAULT '[]'::jsonb,
            normalized_hidden_labels JSONB NOT NULL DEFAULT '[]'::jsonb,
            description TEXT,
            definition TEXT,
            scope_note TEXT,
            broader_concept_uris JSONB NOT NULL DEFAULT '[]'::jsonb,
            broader_concept_labels JSONB NOT NULL DEFAULT '[]'::jsonb
        )
        '''
    )
    upsert_sql = text(
        f'''
        INSERT INTO "{schema}"."{table}" (
            esco_uri,
            preferred_label,
            normalized_label,
            skill_type,
            reuse_level,
            status,
            alt_labels,
            normalized_alt_labels,
            hidden_labels,
            normalized_hidden_labels,
            description,
            definition,
            scope_note,
            broader_concept_uris,
            broader_concept_labels
        ) VALUES (
            :esco_uri,
            :preferred_label,
            :normalized_label,
            :skill_type,
            :reuse_level,
            :status,
            CAST(:alt_labels AS JSONB),
            CAST(:normalized_alt_labels AS JSONB),
            CAST(:hidden_labels AS JSONB),
            CAST(:normalized_hidden_labels AS JSONB),
            :description,
            :definition,
            :scope_note,
            CAST(:broader_concept_uris AS JSONB),
            CAST(:broader_concept_labels AS JSONB)
        )
        ON CONFLICT (esco_uri) DO UPDATE SET
            preferred_label = EXCLUDED.preferred_label,
            normalized_label = EXCLUDED.normalized_label,
            skill_type = EXCLUDED.skill_type,
            reuse_level = EXCLUDED.reuse_level,
            status = EXCLUDED.status,
            alt_labels = EXCLUDED.alt_labels,
            normalized_alt_labels = EXCLUDED.normalized_alt_labels,
            hidden_labels = EXCLUDED.hidden_labels,
            normalized_hidden_labels = EXCLUDED.normalized_hidden_labels,
            description = EXCLUDED.description,
            definition = EXCLUDED.definition,
            scope_note = EXCLUDED.scope_note,
            broader_concept_uris = EXCLUDED.broader_concept_uris,
            broader_concept_labels = EXCLUDED.broader_concept_labels
        '''
    )

    payload = []
    for record in records:
        payload.append(
            {
                "esco_uri": record["esco_uri"],
                "preferred_label": record["preferred_label"],
                "normalized_label": record["normalized_label"],
                "skill_type": record["skill_type"],
                "reuse_level": record["reuse_level"],
                "status": record["status"],
                "alt_labels": json.dumps(record["alt_labels"], ensure_ascii=False),
                "normalized_alt_labels": json.dumps(record["normalized_alt_labels"], ensure_ascii=False),
                "hidden_labels": json.dumps(record["hidden_labels"], ensure_ascii=False),
                "normalized_hidden_labels": json.dumps(record["normalized_hidden_labels"], ensure_ascii=False),
                "description": record["description"],
                "definition": record["definition"],
                "scope_note": record["scope_note"],
                "broader_concept_uris": json.dumps(record["broader_concept_uris"], ensure_ascii=False),
                "broader_concept_labels": json.dumps(record["broader_concept_labels"], ensure_ascii=False),
            }
        )

    with engine.begin() as connection:
        connection.execute(create_schema_sql)
        connection.execute(create_table_sql)
        connection.execute(upsert_sql, payload)

def resolve_workspace(config: Config) -> tuple[Path, Path | None, bool]:
    """Return (workspace_dir, zip_path_or_none, cleanup_when_done)."""
    # Repo-local mode
    if not config.download_url and not config.extracted_dir:
        repo_taxonomy_dir = DIGITAL_COLLECTION_FILENAME.parent
        return repo_taxonomy_dir, None, False

    # External extracted folder mode
    if config.extracted_dir:
        return config.extracted_dir, None, False

    # Download mode
    workspace_dir = Path(tempfile.mkdtemp(prefix="esco_seed_"))
    zip_path = workspace_dir / "esco_dataset.zip"
    return workspace_dir, zip_path, not config.keep_workdir

def run(config: Config) -> int:
    workspace_dir, zip_path, cleanup_when_done = resolve_workspace(config)

    try:
        if config.download_url:
            if zip_path is None:
                raise RuntimeError("Internal error: zip path missing for download mode")
            download_zip(config.download_url, zip_path, config.timeout_seconds)
            extract_zip(zip_path, workspace_dir)

        digital_csv_path, skills_csv_path = find_required_csvs(workspace_dir)

        skills_by_uri = load_skills_by_uri(skills_csv_path)
        digital_rows = load_digital_rows(digital_csv_path)
        all_records = build_records(digital_rows, skills_by_uri)
        # Optional Week-4 subset. When enabled, merge back GenAI parent concepts
        # (see merge_missing_genai_parent_concepts) so taxonomy step 1 stays valid.
        apply_filter = os.getenv("ESCO_SEED_APPLY_FILTER", "").lower() in (
            "1",
            "true",
            "yes",
        )
        if apply_filter:
            records = merge_missing_genai_parent_concepts(
                all_records, filter_records(all_records)
            )
        else:
            records = all_records

        write_json(records, config.output_json)
        write_metadata(
            config.metadata_json,
            download_url=config.download_url,
            digital_csv_path=digital_csv_path,
            skills_csv_path=skills_csv_path,
            record_count=len(records),
        )

        if config.seed_db:
            seed_postgres(records, config.db_url or "", config.db_table)

        return 0
    finally:
        if cleanup_when_done:
            shutil.rmtree(workspace_dir, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(run(parse_args()))
    except Exception:
        sys.exit(1)
