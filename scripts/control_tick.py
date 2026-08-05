#!/usr/bin/env python3
"""Safe bootstrap entry point.

The implementation agent must replace the fixture-only snapshot acquisition
with compact Supabase/Kaggle clients. Until then it exits without mutation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from region_talk_control.orchestrator import ControlSnapshot, choose_actions


def main() -> int:
    if os.getenv("REGION_TALK_ORCHESTRATOR_ENABLED") != "1":
        print(json.dumps({"status": "disabled", "reason": "feature_gate_off"}))
        return 0
    fixture = os.getenv("REGION_TALK_CONTROL_SNAPSHOT_FILE")
    if not fixture:
        raise RuntimeError("bootstrap controller has no remote client; snapshot fixture is required")
    payload = json.loads(Path(fixture).read_text(encoding="utf-8"))
    snapshot = ControlSnapshot(
        mode=str(payload.get("mode") or "running"),
        counts={str(k): int(v) for k, v in (payload.get("counts") or {}).items()},
        due_publications=int(payload.get("due_publications") or 0),
        unsent_review_revisions=int(payload.get("unsent_review_revisions") or 0),
    )
    actions = [action.__dict__ for action in choose_actions(snapshot)]
    print(json.dumps({"status": "planned", "actions": actions}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
