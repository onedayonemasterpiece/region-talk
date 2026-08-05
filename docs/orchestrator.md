# Оркестратор

## 1. Runtime choice

Оркестратор — короткий GitHub Actions controller, а не долгоживущий polling process и не Kaggle notebook.

Default schedule после отладки:

```yaml
schedule:
  - cron: '7,22,37,52 * * * *'
```

Один catch-up tick каждые 15 минут, со смещением от начала часа. Дополнительно:

- `workflow_dispatch` для ручного анализа/ускорения;
- bounded self-dispatch после terminal reconciliation, максимум четыре hop подряд;
- trusted research intake после merge JSON в `main`.

## 2. Единственный controller без новой БД

```yaml
concurrency:
  group: region-talk-orchestrator
  cancel-in-progress: false
```

Для первого рабочего контура этого достаточно вместе с optimistic state commit:

1. controller читает exact current state dataset version и SHA;
2. планирует attempt относительно этого base;
3. reconciler применяет delta только если current HEAD всё ещё равен base;
4. stale-base delta архивируется и не меняет state;
5. новая Kaggle Dataset version публикуется только после SQLite invariants/readback.

Отдельный Supabase controller lease не требуется. Он может быть добавлен позже только при появлении второго реально независимого controller.

Никакая GitHub job не ждёт Kaggle 20–90 минут. Controller запускает kernel и завершается; следующий tick проверяет статус.

## 3. Имена assets выводятся, а не вводятся вручную

При `KAGGLE_USERNAME=<owner>`:

```text
state dataset      = <owner>/region-talk-state
run history        = <owner>/region-talk-run-history
candidate kernel   = <owner>/region-talk-candidate-e5
bge kernel         = <owner>/region-talk-bge-m3
image kernel       = <owner>/region-talk-image-diagnostic
profile kernel     = <owner>/region-talk-source-profile
```

Runtime variables нужны только как optional override, не как обязательные настройки. Model revisions закрепляются в versioned config.

## 4. State machine

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

## 5. Priority order per tick

1. Reconcile every terminal Kaggle output.
2. Recover incomplete archive/state readback.
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
13. Only then expand generic discovery.

Это оптимизирует число готовых публикаций, а не число найденных строк.

## 6. Action selection

Controller читает:

- latest private state manifest;
- active/terminal Kaggle kernel statuses;
- append-only attempt rows из SQLite snapshot;
- current queue/product counters;
- Telegram review/publication evidence для due actions.

Затем выбирает:

- все безопасные local/reconciliation actions;
- не более одного нового Kaggle stage на один auth/resource scope;
- не более одной publication attempt на target/idempotency key;
- bounded self-dispatch, если immediate work осталось.

Existing Supabase используется только при реальном Google provider admission через canonical limiter.

## 7. Parallelism

Разрешено:

- Candidate/E5 с DISCOVERY1 одновременно с ImageDiagnostic на DISCOVERY2;
- BGE с любым Telegram stage;
- local finalizer с BGE/Image, если он читает только committed state.

Запрещено:

- два kernels с одним Telegram auth bundle;
- два reconcilers;
- commit delta к другому base version;
- publisher и notifier, меняющие одну revision одновременно;
- BGE worker с Telegram/Google secrets.

## 8. Kernel attempt lifecycle

```text
planned
→ launched
→ active
→ terminal_output_pending
→ output_downloaded
→ archive_verified
→ reconciled
→ state_readback_verified
→ complete
```

Ошибки классифицируются как platform, worker, timeout, output missing, schema invalid, secret scan, stale base, invariant, state publish или readback. Semantic/invariant failures не ретраятся вслепую.

## 9. Почти непрерывная, но экономная работа

- Heavy work выполняется на Kaggle CPU.
- GitHub jobs короткие и не poll/sleep.
- Пропущенный cron увеличивает latency, но не теряет durable work.
- После завершения stage следующий tick запускает successor; bounded self-dispatch сокращает разрыв.
- Discovery batch уменьшается при downstream backlog.
- Каждый stage имеет per-run/per-day budgets.

## 10. Manual modes

```text
tick
health
analyze
research_import
replay_stage
force_candidate
pause
resume
publish_canary
```

`publish_canary` требует exact approved revision и отдельного feature gate. Отсутствие платного GitHub required-reviewer rule компенсируется fail-closed application gate, а не автоматическим включением publisher.
