from __future__ import annotations

import ast
import json
from pathlib import Path

from region_talk_control.kaggle_status_client import KaggleStatusClient


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_DIRECT_KAGGLE_API_MODULES = {
    Path("src/region_talk_control/kaggle_runtime.py"),
}


def _direct_kaggle_api_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "kaggle" or alias.name.startswith("kaggle."):
                    found.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "kaggle" or module.startswith("kaggle."):
                found.append(module)
    return found


def test_no_second_direct_kaggle_client() -> None:
    violations: list[str] = []
    for root_name in ("src", "scripts"):
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(ROOT)
            imports = _direct_kaggle_api_imports(path)
            if imports and relative not in ALLOWED_DIRECT_KAGGLE_API_MODULES:
                violations.append(f"{relative}: {', '.join(imports)}")
    assert violations == [], "Direct Kaggle API usage must stay in one compatibility runtime: " + "; ".join(violations)


def test_runtime_source_is_pinned_to_events_bot() -> None:
    source = (ROOT / "config/kaggle-runtime-source.yml").read_text(encoding="utf-8")
    assert "source_repository: onedayonemasterpiece/events-bot-new" in source
    assert "source_commit: 5bbdb681623d5e4e0bff2133e487a6663c1a838a" in source
    assert "reuse_proven_runtime_no_greenfield_client" in source
    assert "a second standalone Kaggle API client" in source


def test_vendored_status_client_has_exact_provenance() -> None:
    source = (ROOT / "src/region_talk_control/kaggle_status_client.py").read_text(encoding="utf-8")
    assert "source path: kaggle/kaggle_status_client.py" in source
    assert "source blob: 4f06b7c9fc35a1cc725df2bdea4815d999508acf" in source


def test_status_event_redacts_callback_token(tmp_path: Path, monkeypatch) -> None:
    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b'{"ok": true}'

    monkeypatch.setattr(
        "region_talk_control.kaggle_status_client.urllib.request.urlopen",
        lambda request, timeout: _Response(),
    )
    client = KaggleStatusClient(
        {
            "callback_url": "https://example.invalid/callback",
            "run_id": "run-1",
            "token": "super-secret-token",
            "kind": "candidate_e5",
            "notebook": "RegionTalkCandidateE5",
        },
        output_dir=tmp_path,
        log=lambda _message: None,
    )
    response = client.event("alive", phase="run", status="alive")
    assert response == {"ok": True}

    row = json.loads((tmp_path / "kaggle_status_events.jsonl").read_text(encoding="utf-8"))
    assert row["payload"]["token"] == "<redacted>"
    assert "super-secret-token" not in json.dumps(row)
