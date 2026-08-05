#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []
    for path in sorted((ROOT / "schemas").glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or "$schema" not in payload:
                errors.append(f"invalid_schema_shape:{path}")
        except Exception as exc:  # pragma: no cover - CLI diagnostic
            errors.append(f"schema_parse:{path}:{type(exc).__name__}:{exc}")

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "state.sqlite"
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.executescript((ROOT / "sql/sqlite/0001_initial.sql").read_text(encoding="utf-8"))
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0] != "ok":
                errors.append(f"sqlite_integrity:{result!r}")
            if conn.execute("PRAGMA foreign_key_check").fetchall():
                errors.append("sqlite_foreign_keys")
        except Exception as exc:
            errors.append(f"sqlite_schema:{type(exc).__name__}:{exc}")
        finally:
            conn.close()

    forbidden_suffixes = {".pem", ".key", ".session", ".token", ".sqlite", ".db"}
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in forbidden_suffixes:
            errors.append(f"forbidden_file:{path.relative_to(ROOT)}")
        if path.is_file() and path.name in {".env", "kaggle.json"}:
            errors.append(f"forbidden_file:{path.relative_to(ROOT)}")

    if errors:
        print("repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
