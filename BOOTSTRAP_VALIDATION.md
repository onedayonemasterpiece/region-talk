# Bootstrap validation receipt

Generated: 2026-08-04

Checks executed locally:

- `PYTHONPATH=src pytest -q` — 9 passed;
- `PYTHONPATH=src python scripts/validate_repository.py` — passed;
- `python -m compileall -q src scripts tests` — passed;
- all YAML files parsed with PyYAML — passed;
- SQLite initial schema applied to a clean database;
- `PRAGMA integrity_check` — `ok`;
- `PRAGMA foreign_key_check` — empty;
- clean SQLite backup and SHA-256 test — passed.

Not validated in this bootstrap:

- remote GitHub settings, secrets or Actions execution;
- Supabase migration against a live project;
- Kaggle API/secrets/kernels/datasets;
- YDB export;
- Telegram/VK transports;
- production candidates or publishing.
