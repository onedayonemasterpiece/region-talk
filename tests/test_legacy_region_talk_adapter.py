from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "legacy_region_talk_adapter.py"
SPEC = importlib.util.spec_from_file_location("legacy_region_talk_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


def test_source_commit_and_product_files_are_pinned() -> None:
    assert adapter.SOURCE_COMMIT == "5bbdb681623d5e4e0bff2133e487a6663c1a838a"
    assert "scripts/region_talk_scheduled_runner.py" in adapter.CRITICAL_BLOBS
    assert "scripts/region_talk_orchestrator.py" in adapter.CRITICAL_BLOBS
    assert "kaggle/RegionTalkCandidateReport/region_talk_candidate_report.py" in adapter.CRITICAL_BLOBS


def test_json_parser_keeps_outer_receipt_not_nested_tail() -> None:
    payload = adapter._last_json_payload(
        'log before\n{\n  "ok": true,\n  "metrics": {"published": 3}\n}\n'
    )
    assert payload == {"ok": True, "metrics": {"published": 3}}


def test_canary_allowlist_excludes_local_and_publication_actions() -> None:
    assert adapter.SAFE_REMOTE_ACTIONS == {
        "launch_candidate_report",
        "launch_bge_m3",
        "launch_image_diagnostic",
    }
    assert "notify_confirmed" not in adapter.SAFE_REMOTE_ACTIONS
    assert "run_finalizer" not in adapter.SAFE_REMOTE_ACTIONS
    assert "publisher" not in adapter.SAFE_REMOTE_ACTIONS


def test_compact_plan_preserves_product_metrics_and_hides_commands() -> None:
    result = adapter._compact_plan(
        {
            "ok": True,
            "dry_run": True,
            "metrics": {
                "processed_posts_unique_total": 12,
                "publication_confirmed_total": 4,
                "secret_internal_metric": 99,
            },
            "actions": [
                {
                    "action": "launch_candidate_report",
                    "reason": "continuous discovery",
                    "resource": "telegram:DISCOVERY1",
                    "parallel_safe": True,
                    "cmd": ["python", "secret.py"],
                    "env": {"TOKEN": "not-for-receipt"},
                }
            ],
        }
    )
    assert result["metrics"] == {
        "processed_posts_unique_total": 12,
        "publication_confirmed_total": 4,
    }
    assert result["actions"] == [
        {
            "action": "launch_candidate_report",
            "reason": "continuous discovery",
            "resource": "telegram:DISCOVERY1",
            "parallel_safe": True,
        }
    ]
