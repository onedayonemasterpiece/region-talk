"""Pure, deterministic Region Talk action selection.

The production controller should translate remote Supabase/Kaggle state into
``ControlSnapshot`` and execute returned actions. This module deliberately has
no network calls so the orchestration policy can be exhaustively tested.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Sequence


TERMINAL_ATTEMPT_STATES = frozenset(
    {"complete", "failed", "blocked", "cancelled", "terminal_output_pending"}
)
ACTIVE_ATTEMPT_STATES = frozenset({"planned", "launched", "active"})


@dataclass(frozen=True)
class StageAttempt:
    attempt_id: str
    stage: str
    status: str
    auth_scope: str | None = None
    terminal_output_reconciled: bool = False


@dataclass(frozen=True)
class ControlSnapshot:
    mode: str = "running"
    attempts: tuple[StageAttempt, ...] = ()
    counts: Mapping[str, int] = field(default_factory=dict)
    due_publications: int = 0
    unsent_review_revisions: int = 0
    projection_repair_required: bool = False
    archive_repair_required: bool = False
    now: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class Action:
    kind: str
    stage: str | None = None
    attempt_id: str | None = None
    reason: str = ""


_STAGE_RULES: tuple[tuple[str, str, str], ...] = (
    ("finalizer_writer", "finalizer_ready", "finalizer_ready"),
    ("source_profile_capture", "profile_ready", "profile_ready"),
    ("image_diagnostic", "image_ready", "image_ready"),
    ("fusion", "fusion_ready", "fusion_ready"),
    ("bge_enrichment", "bge_missing_current", "bge_missing_current"),
    ("candidate_e5", "candidate_exact_ready", "candidate_exact_ready"),
    ("candidate_e5", "candidate_discovery_ready", "candidate_discovery_ready"),
)


def _active_scopes(attempts: Sequence[StageAttempt]) -> set[str]:
    return {
        attempt.auth_scope
        for attempt in attempts
        if attempt.status in ACTIVE_ATTEMPT_STATES and attempt.auth_scope
    }


def choose_actions(snapshot: ControlSnapshot, *, max_new_workers: int = 2) -> list[Action]:
    """Return actions in safety/product priority order.

    Local reconciliation/review/publication actions may be returned together.
    New worker launches are bounded and cannot reuse a live auth scope.
    """

    if snapshot.mode != "running":
        return [Action("report_only", reason=f"controller_mode:{snapshot.mode}")]

    actions: list[Action] = []

    # Terminal output is always reconciled before new work. Failed outputs are
    # still archived and classified; they do not silently disappear.
    for attempt in snapshot.attempts:
        if attempt.status in TERMINAL_ATTEMPT_STATES and not attempt.terminal_output_reconciled:
            actions.append(
                Action(
                    "reconcile_attempt",
                    stage=attempt.stage,
                    attempt_id=attempt.attempt_id,
                    reason="terminal_output_pending",
                )
            )

    if snapshot.archive_repair_required:
        actions.append(Action("repair_archive", reason="archive_receipt_incomplete"))
    if snapshot.projection_repair_required:
        actions.append(Action("repair_projection", reason="canonical_state_ahead_of_projection"))

    # Operator/publication safety path outranks discovery.
    if snapshot.counts.get("reaction_sync_due", 0) > 0:
        actions.append(Action("reaction_sync", reason="exact_reactions_due"))
    if snapshot.due_publications > 0:
        actions.append(Action("publish_due", reason="approved_current_slot_due"))
    if snapshot.unsent_review_revisions > 0:
        actions.append(Action("operator_notify", reason="current_revision_unsent"))

    # Never launch against state while terminal deltas are waiting to reconcile.
    if any(action.kind == "reconcile_attempt" for action in actions):
        return actions

    active_stages = {
        attempt.stage for attempt in snapshot.attempts if attempt.status in ACTIVE_ATTEMPT_STATES
    }
    active_scopes = _active_scopes(snapshot.attempts)
    new_workers = 0

    for stage, count_key, reason in _STAGE_RULES:
        if new_workers >= max(0, max_new_workers):
            break
        if snapshot.counts.get(count_key, 0) <= 0 or stage in active_stages:
            continue

        auth_scope = {
            "candidate_e5": "telegram:discovery1",
            "image_diagnostic": "telegram:discovery2",
            "source_profile_capture": "telegram:discovery1",
        }.get(stage)
        if auth_scope and auth_scope in active_scopes:
            continue

        kind = "run_local_stage" if stage in {"fusion", "finalizer_writer"} else "launch_worker"
        actions.append(Action(kind, stage=stage, reason=reason))
        new_workers += 1
        if auth_scope:
            active_scopes.add(auth_scope)

    if not actions:
        actions.append(Action("idle", reason="no_due_work"))
    return actions
