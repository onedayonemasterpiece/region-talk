"""Small SQLite bootstrap/validation helpers.

Production reconciliation must add typed delta handlers and dataset upload/readback.
This module intentionally provides only the non-negotiable local integrity boundary.
"""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def initialize_database(path: Path, migration_sql: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(migration_sql.read_text(encoding="utf-8"))
        connection.commit()
        validate_database(connection)
    finally:
        connection.close()


def validate_database(connection: sqlite3.Connection) -> None:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()
    if not integrity or integrity[0] != "ok":
        raise RuntimeError(f"sqlite_integrity_failed:{integrity!r}")
    foreign = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign:
        raise RuntimeError(f"sqlite_foreign_key_failed:{foreign[:10]!r}")


def clean_backup(source: Path, destination: Path) -> str:
    if destination.exists():
        destination.unlink()
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(destination)
    try:
        src.backup(dst)
        validate_database(dst)
    finally:
        dst.close()
        src.close()
    return file_sha256(destination)
