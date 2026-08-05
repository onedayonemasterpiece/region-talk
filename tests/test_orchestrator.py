from region_talk_control.orchestrator import ControlSnapshot, StageAttempt, choose_actions


def kinds(actions):
    return [action.kind for action in actions]


def stages(actions):
    return [action.stage for action in actions if action.stage]


def test_terminal_reconciliation_blocks_new_launches():
    snapshot = ControlSnapshot(
        attempts=(StageAttempt("a1", "candidate_e5", "terminal_output_pending"),),
        counts={"bge_missing_current": 20},
    )
    actions = choose_actions(snapshot)
    assert kinds(actions) == ["reconcile_attempt"]


def test_product_priority_before_discovery():
    snapshot = ControlSnapshot(
        counts={
            "finalizer_ready": 2,
            "bge_missing_current": 50,
            "candidate_discovery_ready": 500,
        }
    )
    actions = choose_actions(snapshot, max_new_workers=2)
    assert stages(actions) == ["finalizer_writer", "bge_enrichment"]


def test_same_telegram_scope_is_not_reused():
    snapshot = ControlSnapshot(
        attempts=(StageAttempt("a1", "candidate_e5", "active", "telegram:discovery1"),),
        counts={"profile_ready": 5, "image_ready": 4, "bge_missing_current": 4},
    )
    actions = choose_actions(snapshot, max_new_workers=3)
    assert "source_profile_capture" not in stages(actions)
    assert "image_diagnostic" in stages(actions)
    assert "bge_enrichment" in stages(actions)


def test_operator_path_precedes_workers():
    snapshot = ControlSnapshot(
        counts={"reaction_sync_due": 1, "bge_missing_current": 10},
        due_publications=1,
        unsent_review_revisions=1,
    )
    assert kinds(choose_actions(snapshot))[:3] == [
        "reaction_sync", "publish_due", "operator_notify"
    ]


def test_paused_controller_reports_only():
    assert kinds(choose_actions(ControlSnapshot(mode="paused"))) == ["report_only"]
