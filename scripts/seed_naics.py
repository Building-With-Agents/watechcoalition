#!/usr/bin/env python3
# ruff: noqa: T201 -- CLI success output
"""Seed dbo.naics from the Census NAICS 2022 Excel reference.

Loads ``data/naics-2022-taxonomy-reference.xlsx``, normalizes headers/codes,
creates ``dbo.naics`` if missing, replaces all rows (idempotent full refresh).

Environment
------------
- ``--env local`` reads ``PYTHON_DATABASE_URL``.
- ``--env azure`` reads ``AZURE_DATABASE_URL``.

Both can be **PostgreSQL** (e.g. Docker and **Azure Database for PostgreSQL**): pass any
SQLAlchemy URL ``create_engine`` accepts, such as ``postgresql+psycopg2://...``. The
script does not assume Azure means SQL Server.

For **Azure SQL** (SQL Server) instead, use a URL such as::

    mssql+pyodbc://USER:PASS@HOST.database.windows.net:1433/DBNAME?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes

Run from repository root with the agents virtualenv activated so ``agents`` and
dependencies (pandas, openpyxl, sqlalchemy, pyodbc) are importable.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_REPO_ROOT / ".env")
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd  # noqa: E402
from sqlalchemy import create_engine, delete, text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from agents.common.data_store.models import NAICS  # noqa: E402

# Official Census workbook column headers (pandas preserves internal spacing).
_EXCEL_CODE_COL = "2022 NAICS US   Code"
_EXCEL_TITLE_COL = "2022 NAICS US Title"
_EXCEL_SEQ_COL = "Seq. No."

_DEFAULT_XLSX = _REPO_ROOT / "data" / "naics-2022-taxonomy-reference.xlsx"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed dbo.naics from NAICS 2022 Excel.")
    p.add_argument(
        "--env",
        choices=("local", "azure"),
        required=True,
        help="local uses PYTHON_DATABASE_URL; azure uses AZURE_DATABASE_URL",
    )
    p.add_argument(
        "--excel",
        type=Path,
        default=_DEFAULT_XLSX,
        help=f"path to NAICS xlsx (default: {_DEFAULT_XLSX})",
    )
    return p.parse_args()


def _database_url(env: str) -> str:
    if env == "local":
        url = os.getenv("PYTHON_DATABASE_URL")
        var = "PYTHON_DATABASE_URL"
    else:
        url = os.getenv("AZURE_DATABASE_URL")
        var = "AZURE_DATABASE_URL"
    if not url or not url.strip():
        raise SystemExit(f"Missing or empty {var} in environment (.env or shell).")
    return url.strip()


def _ensure_dbo_schema(engine: Engine) -> None:
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS dbo"))


def _ensure_naics_table(engine: Engine) -> None:
    _ensure_dbo_schema(engine)
    NAICS.__table__.create(bind=engine, checkfirst=True)


def _normalize_naics_code(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if value == int(value):
            return str(int(value))
        s = str(value).strip()
        return s or None
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s


def _resolve_excel_columns(df: pd.DataFrame) -> tuple[str, str, str | None]:
    cols = list(df.columns)
    code_col = _EXCEL_CODE_COL if _EXCEL_CODE_COL in df.columns else None
    title_col = _EXCEL_TITLE_COL if _EXCEL_TITLE_COL in df.columns else None
    seq_col = _EXCEL_SEQ_COL if _EXCEL_SEQ_COL in df.columns else None

    if code_col is None:
        code_col = next(
            (c for c in cols if "code" in str(c).lower() and "naics" in str(c).lower()),
            None,
        )
    if title_col is None:
        title_col = next(
            (c for c in cols if "title" in str(c).lower() and "naics" in str(c).lower()),
            None,
        )
    if seq_col is None:
        seq_col = next((c for c in cols if "seq" in str(c).lower()), None)

    if not code_col or not title_col:
        raise SystemExit(
            "Could not resolve NAICS code/title columns. "
            f"Found columns: {cols!r}. Expected '{_EXCEL_CODE_COL}' and '{_EXCEL_TITLE_COL}'."
        )
    return code_col, title_col, seq_col


def _read_naics_dataframe(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise SystemExit(f"Excel file not found: {path}")
    df = pd.read_excel(path, sheet_name=0, engine="openpyxl")
    code_c, title_c, seq_c = _resolve_excel_columns(df)
    out = pd.DataFrame(
        {
            "naics_code": df[code_c].map(_normalize_naics_code),
            "title": df[title_c].map(lambda x: str(x).strip() if pd.notna(x) else ""),
        }
    )
    if seq_c is not None:
        out["seq_no"] = df[seq_c]
    else:
        out["seq_no"] = None

    out = out[out["naics_code"].notna() & (out["title"] != "")]
    out = out.drop_duplicates(subset=["naics_code"], keep="last")

    def _seq(v: object) -> int | None:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return int(v) if float(v) == int(v) else None
        return None

    out["seq_no"] = out["seq_no"].map(_seq)
    return out


def _seed(engine: Engine, df: pd.DataFrame) -> int:
    now = datetime.now(timezone.utc)
    rows: list[dict] = []
    for rec in df.itertuples(index=False):
        code = rec.naics_code
        title = rec.title
        seq = getattr(rec, "seq_no", None)
        rows.append(
            {
                "naics_code": code,
                "title": title,
                "seq_no": seq,
                "createdat": now,
                "updatedat": now,
            }
        )

    _ensure_naics_table(engine)
    batch = 500
    with Session(engine) as session:
        session.execute(delete(NAICS))
        session.commit()
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        with Session(engine) as session:
            session.bulk_insert_mappings(NAICS, chunk)
            session.commit()
    return len(rows)


def main() -> None:
    args = _parse_args()
    url = _database_url(args.env)
    engine = create_engine(url)
    df = _read_naics_dataframe(args.excel.resolve())
    n = _seed(engine, df)
    print(f"Seeded dbo.naics with {n} rows ({args.env}).")


if __name__ == "__main__":
    main()
