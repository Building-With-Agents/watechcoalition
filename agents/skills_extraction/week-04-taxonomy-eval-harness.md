Command to run seed_esco that will get skill records from ESCO v1.2.1 English CSV skills_en.csv and digitalSkillsCollection_en.csv
```
python scripts/seed_esco.py
```
- Skills extracted is originally 1284 but are filtered down to 390 using a seed_esco.filter_records(..) for week 4

Add this flag to uplaod skills into database
```
python scripts/seed_esco.py --seed-db
```

Run this command to confirm postgress table.
```
python - <<'PY'
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

load_dotenv(dotenv_path=Path(".env"))

engine = create_engine(os.getenv("PYTHON_DATABASE_URL"))

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM esco_digital_skills"))
    print("rows in db:", result.scalar())
PY
```

command to view tables
```
python - <<'PY'
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

load_dotenv(dotenv_path=Path(".env"))

db_url = os.getenv("PYTHON_DATABASE_URL")
print("db url loaded:", bool(db_url))

engine = create_engine(db_url)

with engine.connect() as conn:
    tables = conn.execute(text("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name ILIKE '%esco%'
        ORDER BY table_schema, table_name
    """)).fetchall()

    print("matching tables:")
    for row in tables:
        print(row)

    result = conn.execute(text("SELECT COUNT(*) FROM esco_digital_skills"))
    print("rows in db:", result.scalar())
PY
```

Taxonomy finished
ESCO digital skills store
- Load ESCO digital skills clusters into a queryable format

Work to do next 
ESCO digital skills store
- Support exact match, normalized match, and embedding-based similarity lookup

resolve_taxonomy()
resolve_taxonomy_batch()