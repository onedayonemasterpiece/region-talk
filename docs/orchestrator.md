# Оркестратор

## 1. Runtime choice

Оркестратор — короткий GitHub Actions controller, а не долгоживущий polling process и не Kaggle notebook.

Default schedule:

```yaml
schedule:
  - cron: '7,22,37,52 * * * *'
```

То есть один catch-up tick каждые 15 минут, со смещением от начала часа. Дополнительно:

- `workflow_dispatch` для ручного анализа/ускорения;
- bounded self-dispatch после terminal reconciliation, максимум четыре hop подряд;
- `repository_dispatch` для trusted research intake или operator command при необходимости.

## 2. Concurrency

```yaml
concurrency:
  group: region-talk-orchestrator
  cancel-in-progress: false
```

Controller также берёт compact lease через `region_talk_control.claim_controller`. GitHub concurrency защищает от одновременных workflow, Supabase lease — от ручного/повторного запуска и stale attempt.

Никакой job не должен ждать Kaggle 20–90 минут. Controller запускает kernel, записывает attempt и завершается. Следующий tick проверяет статус.

## 3. State machine

### 3.1. Системные стадии

```text
IDLE
RESEARCH_IMPORT_READY
CANDIDATE_E5_READY | CANDIDATE_E5_RUNNING | CANDIDATE_E5_TERMINAL
BGE_READY          | BGE_RUNNING          | BGE_TERMINAL
FUSION_READY
IMAGE_READY        | IMAGE_RUNNING        | IMAGE_TERMINAL
PROFILE_READY      | PROFILE_RUNNING      | PROFILE_TERMINAL
FINALIZER_READY
OPERATOR_NOTIFY_READY
REACTION_SYNC_READY
SCHEDULE_PLAN_READY
PUBLISH_READY
DEGRADED / BLOCKED
```

### 3.2. Priority order per tick

1. Reconcile every terminal Kaggle output.
2. Recover incomplete state/run archive commits.
3. Sync exact operator reactions.
4. Finalize due publication outbox attempts.
5. Publish a due, approved, current revision.
6. Send unsent current candidates to review chat.
7. Run Writer/finalizer for image/profile-ready candidates.
8. Capture missing source/publisher evidence for strong candidates.
9. Run image diagnostics for text-confirmed candidates.
10. Fuse newly available E5+BGE pairs.
11. Run BGE for missing current pairs.
12. Run Candidate/E5 for exact links, research intake and high-priority queue.
13. Only then expand generic source discovery.

This order intentionally optimizes candidates delivered to the operator, not the number of discovered rows.

## 4. Action selection

Controller reads one compact Supabase RPC response:

```json
{
  "controller_lease": {},
  "active_attempts": [],
  "queue_counts": {},
  "due_publications": 0,
  "unsent_review_revisions": 0,
  "state_head": {"version": 17, "sha256": "..."}
}
```

Then it chooses at most:

- all safe local/reconciliation actions;
- one new Kaggle stage per auth/resource scope;
- one publication attempt per target/idempotency key;
- a bounded self-dispatch when immediate work remains.

## 5. Parallelism

Allowed:

- Candidate/E5 with DISCOVERY1 and ImageDiagnostic with DISCOVERY2, if exact auth scopes differ;
- BGE with any Telegram stage, because BGE has no Telegram credentials;
- local reaction sync only when its Telegram role is not active in Kaggle;
- local finalizer with BGE/Image if it only reads committed state/projections.

Forbidden:

- two kernels with the same Telegram auth bundle;
- two state reconcilers;
- state commit while another reconciler has a live lease;
- reusing a candidate delta against a different base version;
- publisher and notifier mutating the same revision concurrently.

## 6. Kernel attempt lifecycle

```text
planned
→ launched
→ active
→ terminal_output_pending
→ output_downloaded
→ archive_verified
→ reconciled
→ state_readback_verified
→ projection_updated
→ complete
```

Terminal failure states are classified:

- `platform_failed`;
- `worker_exception`;
- `timeout`;
- `output_missing`;
- `schema_invalid`;
- `secret_scan_failed`;
- `stale_base`;
- `invariant_failed`;
- `state_publish_failed`;
- `readback_failed`.

Each class has a bounded retry policy. A semantic/invariant failure is never retried blindly.

## 7. Nearly continuous but economical operation

- Heavy work is in Kaggle CPU.
- GitHub jobs are short and do not sleep/poll.
- Fifteen-minute ticks are enough because heavy stages usually last longer than one tick.
- When a stage finishes, the next controller starts the successor within one tick; bounded self-dispatch can reduce the gap.
- Idle ticks perform one compact status read and exit.
- Discovery batch size adapts downward when downstream backlog exists.
- No catch-up loop can generate unbounded API calls; every stage has per-run and per-day budgets.

## 8. Manual operations

`workflow_dispatch` modes:

- `tick` — ordinary state-machine step;
- `health` — no mutation, full status report;
- `analyze` — build diagnostic report from selected time window;
- `research_import` — validate a committed JSON path;
- `replay_stage` — exact run/stage, requires operator environment approval;
- `force_candidate` — prioritize a canonical URL without bypassing gates;
- `pause` / `resume` — change controller state only;
- `publish_canary` — one exact approved revision to configured canary target.

Every mutation mode writes an immutable operator action event.
