"""Fail-closed secret scanning helpers for run bundles."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


_KEY_PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("google_api_key", re.compile(rb"AIza[0-9A-Za-z_-]{20,}")),
    ("supabase_secret_key", re.compile(rb"sb_(?:secret|service_role)_[0-9A-Za-z._-]{16,}")),
    ("private_key", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("bearer_header", re.compile(rb"Authorization\s*:\s*Bearer\s+[0-9A-Za-z._~+/=-]{12,}", re.I)),
    ("env_assignment", re.compile(
        rb"(?:TOKEN|SECRET|PASSWORD|SESSION|SERVICE_KEY|API_KEY|PRIVATE_KEY)\s*=\s*[^\s]{8,}", re.I
    )),
)


@dataclass(frozen=True)
class SecretHit:
    path: str
    kind: str
    offset: int
    fingerprint: str


def _fingerprint(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()[:16]


def scan_bytes(data: bytes, *, path: str, exact_secrets: Iterable[bytes] = ()) -> list[SecretHit]:
    hits: list[SecretHit] = []
    for secret in exact_secrets:
        if not secret:
            continue
        start = data.find(secret)
        if start >= 0:
            hits.append(SecretHit(path, "exact_injected_secret", start, _fingerprint(secret)))
    for kind, pattern in _KEY_PATTERNS:
        for match in pattern.finditer(data):
            hits.append(SecretHit(path, kind, match.start(), _fingerprint(match.group(0))))
    return hits


def scan_tree(root: Path, *, exact_secrets: Iterable[bytes] = ()) -> list[SecretHit]:
    hits: list[SecretHit] = []
    forbidden_names = {".env", "kaggle.json"}
    forbidden_suffixes = {".pem", ".key", ".session", ".token"}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.name in forbidden_names or path.suffix.lower() in forbidden_suffixes:
            hits.append(SecretHit(rel, "forbidden_file", 0, _fingerprint(rel.encode())))
            continue
        # Run bundles are bounded. Refuse unexpectedly huge files rather than
        # silently skipping a potentially sensitive payload.
        if path.stat().st_size > 256 * 1024 * 1024:
            hits.append(SecretHit(rel, "unscanned_oversize_file", 0, _fingerprint(rel.encode())))
            continue
        hits.extend(scan_bytes(path.read_bytes(), path=rel, exact_secrets=exact_secrets))
    return hits
