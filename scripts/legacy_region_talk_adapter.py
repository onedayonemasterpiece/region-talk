#!/usr/bin/env python3
"""Run the proven YDB-backed Region Talk implementation from its exact source checkout.

This adapter deliberately does not reimplement Region Talk. GitHub Actions replaces
only the old APScheduler/Fly trigger while the product runtime stays byte-identical
to the pinned events-bot-new commit during parity recovery.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SOURCE_REPOSITORY = "onedayonemasterpiece/events-bot-new"
SOURCE_COMMIT = "5bbdb681623d5e4e0bff2133e487a6663c1a838a"
CRITICAL_BLOBS: dict[str, str] = {
    "scripts/region_talk_scheduled_runner.py": "8e1c955b6096556095e3426054b2cc12d96fabf8",
    "scripts/region_talk_orchestrator.py": "a68385dfa6da91594e99142998093f457d23b39c",
    "scripts/region_talk_publication_finalizer.py": "76e928989585d05d2de2291b36109fba6df78dde",
    "kaggle/RegionTalkCandidateReport/region_talk_candidate_report.py": "7bc15d6175264cd3bfad242f4838c00bd2526394",
    "kaggle/RegionTalkBgeM3Enrichment/region_talk_bge_m3_enrichment.py": "0598777af0c91d9d716817666cfc45c81cda642c",
    "kaggle/RegionTalkImageDiagnostic/region_talk_image_diagnostic.py": "b03a038be6c3dd33b75262244a27b06285b003b9",
}
SAFE_REMOTE_ACTIONS = {
    "launch_candidate_report",
    "launch_bge_m3",
    "launch_image_diagnostic",
}
PRODUCT_METRIC_KEYS = (
    "publics_scanned_with_posts_total",
    "publics_with_ko_candidates_total",
    "processed_posts_unique_total",
    "ko_scope_detected_posts_unique_total",
    "fast_check_exact_posts_processed_unique_total",
    "fast_check_exact_posts_dual_vectorized_total",
    "fast_check_exact_posts_strict_text_accepted_total",
    "text_vector_current_version_e5_without_bge_total",
    "bge_missing_current_sample_total",
    "image_pending_total",
    "image_actionable_work_total",
    "finalizer_pending_url_total",
    "publication_candidate_total",
    "publication_confirmed_total",
    "publication_unsent_confirmed_total",
    "publication_draft_ready_confirmed_total",
    "publication_sent_total",
)


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    timeout_seconds: int = 900,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=dict(env or os.environ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=max(30, int(timeout_seconds)),
        check=False,
    )


def _last_json_payload(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    found: dict[str, Any] | None = None
    found_span = -1
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            payload, end = decoder.raw_decode(text[index:])
        except (TypeError, ValueError):
            continue
        # Nested dictionaries also decode successfully. The outer command
        # receipt is the largest complete JSON object in the captured stream.
        if isinstance(payload, dict) and end > found_span:
            found = payload
            found_span = end
    if found is None:
        raise RuntimeError("legacy Region Talk command produced no JSON receipt")
    return found


def _secret_values(env: Mapping[str, str]) -> list[str]:
    values: set[str] = set()
    markers = (
        "KEY",
        "TOKEN",
        "SECRET",
        "SESSION",
        "BUNDLE",
        "PASSWORD",
        "CREDENTIAL",
        "IAM",
    )
    for name, value in env.items():
        if not value or len(value) < 8:
            continue
        upper = name.upper()
        if any(marker in upper for marker in markers):
            values.add(value)
    return sorted(values, key=len, reverse=True)


def _redact_text(text: str, env: Mapping[str, str]) -> str:
    redacted = str(text)
    for value in _secret_values(env):
        redacted = redacted.replace(value, "<redacted>")
    return redacted


def _sanitize(value: Any, env: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return _redact_text(value, env)
    if isinstance(value, list):
        return [_sanitize(item, env) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item, env) for item in value]
    if isinstance(value, dict):
        return {str(key): _sanitize(item, env) for key, item in value.items()}
    return value


def verify_source(source_dir: Path) -> dict[str, Any]:
    if not (source_dir / ".git").exists():
        raise RuntimeError(f"source checkout has no .git metadata: {source_dir}")
    commit = _run(
        ["git", "rev-parse", "HEAD"], cwd=source_dir, timeout_seconds=30
    ).stdout.strip()
    if commit != SOURCE_COMMIT:
        raise RuntimeError(f"unexpected source commit: {commit or '<missing>'}")

    verified: list[dict[str, str]] = []
    for relative, expected_blob in CRITICAL_BLOBS.items():
        path = source_dir / relative
        if not path.is_file():
            raise RuntimeError(f"missing proven Region Talk file: {relative}")
        result = _run(
            ["git", "hash-object", relative], cwd=source_dir, timeout_seconds=30
        )
        actual_blob = result.stdout.strip()
        if result.returncode != 0 or actual_blob != expected_blob:
            raise RuntimeError(
                f"source blob mismatch: {relative} expected={expected_blob} actual={actual_blob or '<missing>'}"
            )
        verified.append({"path": relative, "blob_sha": actual_blob})
    return {
        "repository": SOURCE_REPOSITORY,
        "commit": commit,
        "critical_blobs": verified,
    }


def _common_env(source_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["REGION_TALK_ALLOW_LOCAL_YC_FALLBACK"] = "0"
    env["REGION_TALK_REQUIRE_NONINTERACTIVE_YDB_CREDENTIAL"] = "1"
    env["REGION_TALK_YDB_REQUIRE_EXPECTED_DATABASE"] = "1"
    env["REGION_TALK_YDB_READ_MODEL_MODE"] = "required"
    env["REGION_TALK_YDB_ALLOW_LEGACY_BROAD_READ_FALLBACK"] = "0"
    env.setdefault("REGION_TALK_YDB_BUDGET_MAX_QUERIES", "64")
    env.setdefault("REGION_TALK_YDB_BUDGET_MAX_ROWS_READ", "5000")
    env.setdefault("REGION_TALK_YDB_BUDGET_MAX_BYTES_READ", str(32 * 1024 * 1024))
    env.setdefault("REGION_TALK_YDB_BUDGET_MAX_ROWS_WRITTEN", "1000")
    env.setdefault("REGION_TALK_YDB_BUDGET_MAX_BYTES_WRITTEN", str(16 * 1024 * 1024))
    env.setdefault("REGION_TALK_YDB_BUDGET_MAX_ESTIMATED_IO_RU", "8000")
    env["REGION_TALK_SCHEDULED_LOCK_FILE"] = str(
        source_dir / ".runtime" / "region-talk.lock"
    )
    env["REGION_TALK_SCHEDULED_LOG_DIR"] = str(
        source_dir / ".runtime" / "logs"
    )
    env.pop("TELEGRAM_AUTH_BUNDLE_E2E", None)
    env.pop("TELEGRAM_SESSION", None)
    env.pop("TG_SESSION", None)
    return env


def _plan_command(limit: int) -> list[str]:
    return [
        sys.executable,
        "scripts/region_talk_orchestrator.py",
        "--limit",
        str(max(100, min(20_000, int(limit)))),
        "--bge-sample-limit",
        "100",
        "--target-confirmed",
        "0",
        "--max-actions-per-cycle",
        "1",
    ]


def _compact_plan(payload: Mapping[str, Any]) -> dict[str, Any]:
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), Mapping) else {}
    actions = payload.get("actions") if isinstance(payload.get("actions"), list) else []
    return {
        "ok": bool(payload.get("ok")),
        "dry_run": bool(payload.get("dry_run")),
        "metrics": {
            key: int(metrics.get(key) or 0)
            for key in PRODUCT_METRIC_KEYS
            if key in metrics
        },
        "actions": [
            {
                "action": str(item.get("action") or ""),
                "reason": str(item.get("reason") or ""),
                "resource": str(item.get("resource") or ""),
                "parallel_safe": bool(item.get("parallel_safe")),
            }
            for item in actions
            if isinstance(item, Mapping)
        ],
        "kaggle_kernel_statuses": dict(metrics.get("kaggle_kernel_statuses") or {}),
        "kaggle_status_error": str(metrics.get("kaggle_status_error") or ""),
        "active_kernel_skips": list(payload.get("active_kernel_skips") or []),
    }


def run_preflight(source_dir: Path, env: Mapping[str, str]) -> tuple[int, dict[str, Any], str]:
    result = _run(
        [
            sys.executable,
            "scripts/region_talk_scheduled_runner.py",
            "--preflight-only",
        ],
        cwd=source_dir,
        env=env,
        timeout_seconds=120,
    )
    raw = _redact_text(result.stdout, env)
    payload = _last_json_payload(raw)
    return result.returncode, {
        "ok": bool(payload.get("ok")),
        "missing": sorted(str(item) for item in (payload.get("missing") or [])),
    }, raw


def run_plan(
    source_dir: Path, env: Mapping[str, str], *, limit: int
) -> tuple[int, dict[str, Any], str, dict[str, Any]]:
    result = _run(
        _plan_command(limit), cwd=source_dir, env=env, timeout_seconds=600
    )
    raw = _redact_text(result.stdout, env)
    payload = _last_json_payload(raw)
    return result.returncode, _compact_plan(payload), raw, payload


def _prepare_action_command(action: Mapping[str, Any], run_id: str) -> list[str]:
    command = [str(item) for item in (action.get("cmd") or [])]
    if not command:
        raise RuntimeError("selected legacy action has no command")
    if Path(command[0]).name.startswith("python"):
        command[0] = sys.executable
    if "--run-id" not in command:
        command.extend(["--run-id", run_id])
    return command


def run_remote_canary(
    source_dir: Path,
    env: Mapping[str, str],
    *,
    limit: int,
    preferred_action: str,
) -> tuple[int, dict[str, Any], str]:
    plan_rc, compact_plan, plan_raw, full_plan = run_plan(
        source_dir, env, limit=limit
    )
    if plan_rc != 0 or not compact_plan.get("ok"):
        return plan_rc or 2, {
            "ok": False,
            "status": "plan_failed",
            "plan": compact_plan,
        }, plan_raw

    actions = [item for item in (full_plan.get("actions") or []) if isinstance(item, Mapping)]
    allowed = [item for item in actions if str(item.get("action") or "") in SAFE_REMOTE_ACTIONS]
    selected: Mapping[str, Any] | None = None
    if preferred_action:
        selected = next(
            (item for item in allowed if str(item.get("action") or "") == preferred_action),
            None,
        )
    if selected is None and allowed:
        selected = allowed[0]
    if selected is None:
        return 3, {
            "ok": False,
            "status": "no_safe_remote_action",
            "plan": compact_plan,
        }, plan_raw

    action_name = str(selected.get("action") or "")
    run_id = (
        "region-talk-github-canary-"
        + action_name.replace("launch_", "").replace("_", "-")
        + "-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    command = _prepare_action_command(selected, run_id)
    child_env = dict(env)
    child_env.update(
        {str(key): str(value) for key, value in dict(selected.get("env") or {}).items()}
    )
    # This canary may launch only a proven private Kaggle worker. It cannot run
    # local notifier/finalizer/publisher actions and does not wait for terminal
    # completion; subsequent bounded control ticks recover the exact output.
    timeout = min(600, max(60, int(selected.get("timeout_seconds") or 300)))
    result = _run(command, cwd=source_dir, env=child_env, timeout_seconds=timeout)
    raw = _redact_text(result.stdout, child_env)
    return result.returncode, {
        "ok": result.returncode == 0,
        "status": "launched" if result.returncode == 0 else "launch_failed",
        "run_id": run_id,
        "action": action_name,
        "resource": str(selected.get("resource") or ""),
        "command": command,
        "returncode": result.returncode,
        "output_tail": raw[-4000:],
        "plan": compact_plan,
    }, plan_raw + "\n" + raw


def run_scheduled_tick(
    source_dir: Path,
    env: Mapping[str, str],
    *,
    scheduler_run_id: str,
) -> tuple[int, dict[str, Any], str]:
    child_env = dict(env)
    child_env.setdefault("REGION_TALK_SCHEDULED_MAX_ACTIONS_PER_CYCLE", "1")
    child_env.setdefault("REGION_TALK_SCHEDULED_MAX_RUNTIME_MINUTES", "30")
    child_env.setdefault("REGION_TALK_SCHEDULED_NO_PROGRESS_CYCLES", "2")
    child_env.setdefault("REGION_TALK_SCHEDULED_POLL_SECONDS", "180")
    child_env.setdefault("REGION_TALK_SCHEDULED_DOWNSTREAM_POLL_SECONDS", "60")
    child_env.setdefault("REGION_TALK_SCHEDULED_SCAN_LIMIT", "5000")
    child_env.setdefault("REGION_TALK_EXTERNAL_RESEARCH_ENABLED", "0")
    # Publication itself remains a separate explicit gate. The existing
    # scheduled runner handles discovery, enrichment, finalization and operator
    # queue semantics; channel publishing is never enabled here.
    child_env["REGION_TALK_TELEGRAM_PUBLISH_ENABLED"] = "0"
    child_env["REGION_TALK_VK_PUBLISH_ENABLED"] = "0"
    result = _run(
        [
            sys.executable,
            "scripts/region_talk_scheduled_runner.py",
            "--scheduler-run-id",
            scheduler_run_id,
            "--db-path",
            str(source_dir / ".runtime" / "ops.sqlite"),
        ],
        cwd=source_dir,
        env=child_env,
        timeout_seconds=45 * 60,
    )
    raw = _redact_text(result.stdout, child_env)
    payload = _last_json_payload(raw)
    receipt = {
        "ok": bool(payload.get("ok")),
        "status": str(payload.get("status") or ""),
        "metrics": dict(payload.get("metrics") or {}),
        "last_cycle": payload.get("last_cycle"),
        "last_selected_actions": list(payload.get("last_selected_actions") or []),
        "external_research_status": payload.get("external_research_status"),
        "publication_plan_status": payload.get("publication_plan_status"),
        "reaction_sync_status": payload.get("reaction_sync_status"),
        "timed_out": bool(payload.get("timed_out")),
        "exit_code": payload.get("exit_code"),
    }
    return result.returncode, receipt, raw


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default="legacy-src")
    parser.add_argument(
        "--mode", choices=("preflight", "plan", "canary", "scheduled"), required=True
    )
    parser.add_argument("--receipt", default="artifacts/legacy-region-talk/receipt.json")
    parser.add_argument("--log", default="artifacts/legacy-region-talk/command.log")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument(
        "--preferred-action",
        choices=("", *sorted(SAFE_REMOTE_ACTIONS)),
        default="launch_candidate_report",
    )
    parser.add_argument("--scheduler-run-id", default="github-actions-manual")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    receipt_path = Path(args.receipt).resolve()
    log_path = Path(args.log).resolve()
    source = verify_source(source_dir)
    env = _common_env(source_dir)

    if args.mode == "preflight":
        rc, result, raw = run_preflight(source_dir, env)
    elif args.mode == "plan":
        rc, result, raw, _ = run_plan(source_dir, env, limit=args.limit)
    elif args.mode == "canary":
        rc, result, raw = run_remote_canary(
            source_dir,
            env,
            limit=args.limit,
            preferred_action=args.preferred_action,
        )
    else:
        rc, result, raw = run_scheduled_tick(
            source_dir, env, scheduler_run_id=args.scheduler_run_id
        )

    receipt = {
        "schema_version": "region-talk-ydb-parity-receipt-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "source": source,
        "result": _sanitize(result, env),
        "mutated_product_state": args.mode in {"canary", "scheduled"},
        "production_publication_enabled": False,
    }
    _write_json(receipt_path, receipt)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(_redact_text(raw, env), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if rc == 0 and bool(result.get("ok")) else int(rc or 1)


if __name__ == "__main__":
    raise SystemExit(main())
