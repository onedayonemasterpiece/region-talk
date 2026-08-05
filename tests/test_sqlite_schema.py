from pathlib import Path

from region_talk_control.sqlite_store import clean_backup, initialize_database


def test_initial_schema_and_clean_backup(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    source = tmp_path / "state.sqlite"
    clean = tmp_path / "state.clean.sqlite"
    initialize_database(source, root / "sql/sqlite/0001_initial.sql")
    digest = clean_backup(source, clean)
    assert len(digest) == 64
    assert clean.exists() and clean.stat().st_size > 0
