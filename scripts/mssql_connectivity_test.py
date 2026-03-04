#!/usr/bin/env python3
"""Minimal MSSQL connectivity test: count job_postings using SQLAlchemy + pyodbc."""

import os
import sys
from urllib.parse import quote_plus

import pyodbc
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def _sqlserver_driver():
    """Pick first installed ODBC driver that can connect to SQL Server."""
    wanted = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]
    installed = pyodbc.drivers()
    for name in wanted:
        if name in installed:
            return quote_plus(name)
    for name in installed:
        if "SQL Server" in name:
            return quote_plus(name)
    return None

load_dotenv()

url = os.getenv("DATABASE_URL")
if not url:
    print("DATABASE_URL is not set.", file=sys.stderr)
    sys.exit(1)

# Prisma: sqlserver://host:port;database=x;user=u;password=p;...
# SQLAlchemy+pyodbc: mssql+pyodbc://user:password@host:port/database?...
if url.startswith("sqlserver://"):
    rest = url[len("sqlserver://") :].strip()
    parts = rest.split(";")
    host_port = parts[0].strip()
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.strip().lower()] = v.strip()
    host, _, port = host_port.rpartition(":")
    port = port or "1433"
    user = params.get("user", "")
    password = params.get("password", "")
    database = params.get("database", "")
    auth = f"{quote_plus(user)}:{quote_plus(password)}@" if user or password else ""
    q = []
    if params.get("trustservercertificate") == "true":
        q.append("TrustServerCertificate=yes")
    if params.get("encrypt") == "false":
        q.append("Encrypt=no")
    driver = _sqlserver_driver()
    if not driver:
        print("No SQL Server ODBC driver found. Install 'ODBC Driver 17 or 18 for SQL Server'.", file=sys.stderr)
        sys.exit(1)
    q.append(f"driver={driver}")
    url = f"mssql+pyodbc://{auth}{host}:{port}/{database}?{'&'.join(q)}"

engine = create_engine(url)
with engine.connect() as conn:
    row = conn.execute(text("SELECT COUNT(*) AS n FROM job_postings")).fetchone()
    n = row[0]

print(f"job_postings row count: {n}")
