# Legacy SQL migration scripts

These files used to live next to a sibling ``migrations.py`` module as:

- ``agents/common/data_store/migrations/001_phase1_tables.py``
- ``agents/common/data_store/migrations/002_extraction_tables.py``

Python cannot load **both** ``data_store/migrations.py`` and a ``data_store/migrations/``
package, so when ``migrations.py`` was restored (layout from commit
``65b81b2b315b97aefdde0c60aee97f1af45fa1ae``), the numbered scripts were moved here.

**Canonical migrations:** ``from agents.common.data_store.migrations import run_migrations``
(module ``agents/common/data_store/migrations.py``).

Run legacy scripts directly, e.g.:

```bash
python agents/common/data_store/legacy_migrations/001_phase1_tables.py
```
