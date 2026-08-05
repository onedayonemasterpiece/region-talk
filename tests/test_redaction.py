from pathlib import Path

from region_talk_control.redaction import scan_bytes, scan_tree


def test_exact_secret_is_detected_without_exposing_value():
    secret = b"very-secret-token-123456"
    hits = scan_bytes(b"before " + secret + b" after", path="stdout.log", exact_secrets=[secret])
    assert hits and hits[0].kind == "exact_injected_secret"
    assert secret.decode() not in repr(hits)


def test_key_pattern_is_detected():
    hits = scan_bytes(b"key=AIzaabcdefghijklmnopqrstuvwx", path="events.jsonl")
    assert any(hit.kind == "google_api_key" for hit in hits)


def test_forbidden_file_is_detected(tmp_path: Path):
    (tmp_path / ".env").write_text("X=Y", encoding="utf-8")
    hits = scan_tree(tmp_path)
    assert any(hit.kind == "forbidden_file" for hit in hits)
