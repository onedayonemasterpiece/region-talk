#!/usr/bin/env python3
"""Mechanically vendor the working Region Talk runtime from an exact source checkout.

The selection is deterministic and source-backed: all Region Talk product scripts,
all Region Talk Kaggle launchers/workers, their recursive local Python imports, and
worker data files are copied without rewriting their contents.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

EXPECTED_REPOSITORY = "onedayonemasterpiece/events-bot-new"
EXPECTED_COMMIT = "5bbdb681623d5e4e0bff2133e487a6663c1a838a"
WORKER_DIRECTORIES = (
    "kaggle/RegionTalkCandidateReport",
    "kaggle/RegionTalkBgeM3Enrichment",
    "kaggle/RegionTalkImageDiagnostic",
    "kaggle/RegionTalkQwen3Embedding06BEnrichment",
)
CRITICAL_PATHS = (
    "scripts/region_talk_scheduled_runner.py",
    "scripts/region_talk_orchestrator.py",
    "scripts/region_talk_publication_finalizer.py",
    "kaggle/execute_region_talk_candidate_report.py",
    "kaggle/execute_region_talk_bge_m3_enrichment.py",
    "kaggle/execute_region_talk_image_diagnostic.py",
    "kaggle/RegionTalkCandidateReport/region_talk_candidate_report.py",
    "kaggle/RegionTalkBgeM3Enrichment/region_talk_bge_m3_enrichment.py",
    "kaggle/RegionTalkImageDiagnostic/region_talk_image_diagnostic.py",
)
FORBIDDEN_SUFFIXES = {
    ".sqlite",
    ".sqlite3",
    ".db",
    ".session",
    ".token",
    ".pem",
    ".key",
    ".zip",
    ".tar",
    ".gz",
    ".xz",
}
FORBIDDEN_NAMES = {".env", "kaggle.json"}


def _run_git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=source,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip()[:500]}"
        )
    return result.stdout.strip()


def verify_source(source: Path, expected_commit: str = EXPECTED_COMMIT) -> str:
    if not (source / ".git").exists():
        raise RuntimeError(f"source checkout has no .git metadata: {source}")
    commit = _run_git(source, "rev-parse", "HEAD")
    if commit != expected_commit:
        raise RuntimeError(
            f"unexpected source commit: expected={expected_commit} actual={commit}"
        )
    for relative in CRITICAL_PATHS:
        if not (source / relative).is_file():
            raise RuntimeError(f"missing critical Region Talk source: {relative}")
    return commit


def build_module_map(source: Path) -> dict[str, Path]:
    module_map: dict[str, Path] = {}
    for path in source.rglob("*.py"):
        relative = path.relative_to(source)
        if any(
            part in {".git", "__pycache__", ".pytest_cache", "node_modules", "artifacts"}
            for part in relative.parts
        ):
            continue
        parts = list(relative.with_suffix("").parts)
        module = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
        if module:
            module_map[module] = path
    return module_map


def package_for(source: Path, path: Path) -> str:
    parts = list(path.relative_to(source).with_suffix("").parts)
    parts = parts[:-1]
    return ".".join(parts)


def add_module(module: str, module_map: dict[str, Path], output: set[Path]) -> None:
    if module in module_map:
        output.add(module_map[module])
    parts = module.split(".")
    for index in range(1, len(parts) + 1):
        parent = ".".join(parts[:index])
        if parent in module_map:
            output.add(module_map[parent])


def local_imports(
    source: Path,
    path: Path,
    module_map: dict[str, Path],
) -> set[Path]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        raise RuntimeError(f"cannot parse {path.relative_to(source)}: {exc}") from exc

    output: set[Path] = set()
    package = package_for(source, path)
    relative_name = path.relative_to(source).as_posix()
    # Importing video_announce.kaggle_client executes package __init__, but its
    # handler import is intentionally lazy inside a function and is unrelated
    # to Region Talk. Do not pull the whole bot/video product through that edge.
    nodes: Iterable[ast.AST]
    nodes = tree.body if relative_name == "video_announce/__init__.py" else ast.walk(tree)

    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                add_module(alias.name, module_map, output)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                package_parts = package.split(".") if package else []
                keep = max(0, len(package_parts) - (node.level - 1))
                prefix = ".".join(package_parts[:keep])
                base = ".".join(item for item in (prefix, base) if item)
            if base:
                add_module(base, module_map, output)
            for alias in node.names:
                if alias.name != "*":
                    child = ".".join(item for item in (base, alias.name) if item)
                    add_module(child, module_map, output)

    text = path.read_text(encoding="utf-8")
    for match in re.finditer(
        r"['\"]((?:scripts|kaggle|source_parsing|video_announce)/[^'\"]+\.py)['\"]",
        text,
    ):
        candidate = source / match.group(1)
        if candidate.is_file():
            output.add(candidate)
    return output


def initial_seeds(source: Path) -> set[Path]:
    seeds: set[Path] = set(source.glob("scripts/region_talk_*.py"))
    seeds.update(source.glob("kaggle/execute_region_talk_*.py"))
    for directory in WORKER_DIRECTORIES:
        seeds.update((source / directory).glob("*.py"))
    for relative in CRITICAL_PATHS:
        seeds.add(source / relative)
    return {path for path in seeds if path.is_file()}


def dependency_closed_files(source: Path) -> set[Path]:
    module_map = build_module_map(source)
    selected = initial_seeds(source)
    queue = list(selected)
    while queue:
        path = queue.pop()
        for dependency in local_imports(source, path, module_map):
            if dependency not in selected:
                selected.add(dependency)
                queue.append(dependency)

    for directory in WORKER_DIRECTORIES:
        root = source / directory
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
                continue
            if "__pycache__" in path.parts:
                continue
            selected.add(path)
    for relative in ("requirements.txt", "pytest.ini"):
        path = source / relative
        if path.is_file():
            selected.add(path)

    missing = [relative for relative in CRITICAL_PATHS if source / relative not in selected]
    if missing:
        raise RuntimeError(f"dependency closure lost critical files: {missing}")
    return selected


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def vendor(source: Path, destination: Path, manifest_path: Path, commit: str) -> dict:
    selected = dependency_closed_files(source)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    rows: list[dict[str, object]] = []
    for path in sorted(selected):
        relative = path.relative_to(source)
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise RuntimeError(f"forbidden runtime file selected: {relative}")
        data = path.read_bytes()
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        rows.append(
            {
                "path": relative.as_posix(),
                "bytes": len(data),
                "git_blob_sha1": git_blob_sha(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )

    manifest = {
        "schema_version": "region-talk-legacy-runtime-import-manifest-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_repository": EXPECTED_REPOSITORY,
        "source_commit": commit,
        "destination_root": destination.as_posix(),
        "file_count": len(rows),
        "total_bytes": sum(int(row["bytes"]) for row in rows),
        "files": rows,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default="legacy-src")
    parser.add_argument("--destination", default="legacy_runtime")
    parser.add_argument(
        "--manifest", default="config/legacy-runtime-import-manifest.json"
    )
    parser.add_argument("--expected-commit", default=EXPECTED_COMMIT)
    args = parser.parse_args()

    source = Path(args.source_dir).resolve()
    destination = Path(args.destination).resolve()
    manifest_path = Path(args.manifest).resolve()
    commit = verify_source(source, args.expected_commit)
    manifest = vendor(source, destination, manifest_path, commit)
    print(
        json.dumps(
            {
                "ok": True,
                "source_commit": commit,
                "file_count": manifest["file_count"],
                "total_bytes": manifest["total_bytes"],
                "destination": str(destination),
                "manifest": str(manifest_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
