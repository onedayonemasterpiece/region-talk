# Region Talk launch-readiness audit — 2026-08-06

## Решение

**Статус: NOT_RUNNABLE / IMPLEMENTATION_REQUIRED.**

Репозиторий целостен как архитектурный bootstrap и набор контрактов, но не является завершённым исполняемым Region Talk после миграции. Рабочий Kaggle credential подтверждён, однако GitHub Actions → Kaggle pipeline, canonical state, workers, reconciler, review и publisher не доведены до первого полного запуска.

`REGION_TALK_ORCHESTRATOR_ENABLED` нельзя включать до выполнения launch slice ниже. Текущий control workflow при включении гарантированно завершается `exit 1` и не запускает Kaggle.

Проверенный `main`:

```text
9812e8a736462c6f42e24621811caf6c25260944
```

## Что реально запускалось и проверялось

### 1. Kaggle authentication — подтверждено

Успешный GitHub Actions run:

- run: `30990961846`;
- artifact: `8924068337`;
- authenticated endpoint: `kernels list --mine`;
- `server_authenticated=true`;
- наблюдались две owned-kernel строки;
- dataset не создавался;
- kernel не запускался.

Это доказывает работоспособность legacy-пары `KAGGLE_USERNAME` + `KAGGLE_KEY` на 2026-08-05, но не доказывает Region Talk runtime.

### 2. Scheduled controller — только skipped ticks

Последний проверенный scheduled run:

- run: `31071539463`;
- commit: `9812e8a736462c6f42e24621811caf6c25260944`;
- conclusion: `skipped`;
- причина: job-level gate `vars.REGION_TALK_ORCHESTRATOR_ENABLED == '1'` не выполнен.

Manual `workflow_dispatch` runs для controller отсутствуют.

### 3. Повторная CI-проверка — заблокирована GitHub Billing

Повторно запущен validation run:

- run: `31000455705`;
- attempt: `2`;
- job: `92541644647`;
- runner не был назначен;
- ни один step не стартовал.

GitHub annotation:

```text
The job was not started because recent account payments have failed or your
spending limit needs to be increased. Please check the 'Billing & plans'
section in your settings.
```

Это внешний P0-блокер любого нового GitHub Actions → Kaggle запуска в private repository. Он не является падением тестов или Python-кода.

### 4. Незавершённая migration branch

Ветка `agent/complete-region-talk-migration-20260805`:

- на один commit впереди своего merge base;
- на 12 commits позади текущего `main`;
- её единственный migration workflow run `31004677626` не получил runner из-за того же billing gate.

Ветку нельзя сливать целиком: она устарела относительно `main`. Из неё допустимо извлекать только отдельно проверенные части migration tooling.

## Фактическая точка исполнения

### Control workflow

`.github/workflows/region-talk-control.yml` сейчас:

- запускается по cron каждые 15 минут;
- полностью закрыт feature gate;
- устанавливает только базовый package без runtime extra;
- не вызывает `scripts/control_tick.py`;
- заканчивается обязательным `exit 1`;
- имеет `contents: read`, хотя observability contract требует обновлять `ops-current` branch.

### Controller entrypoint

`scripts/control_tick.py` сейчас:

- при выключенном gate возвращает `disabled`;
- при включённом gate требует локальный fixture `REGION_TALK_CONTROL_SNAPSHOT_FILE`;
- не читает canonical Kaggle/SQLite state;
- только вычисляет план действий;
- не исполняет ни одного action.

### Kaggle runtime

`src/region_talk_control/kaggle_runtime.py` содержит только часть compatibility layer:

- authentication;
- private dataset create/version/delete;
- dataset status/file listing;
- kernel listing/status/output download;
- dataset-source readback;
- bounded readiness waits.

Не реализованы обязательные части proven lifecycle:

- local kernel tree preparation и ignore policy;
- status helper injection;
- kernel push/update retries;
- exact source binding after push;
- terminal polling и transient recovery;
- failed-output recovery;
- cleanup/TTL-GC receipts;
- host ledger, active-job registry и auth-scope guard.

### Canonical state

SQLite DDL подробный, но production state layer отсутствует:

- нет private `region-talk-state` lifecycle proof;
- нет private `region-talk-run-history` lifecycle proof;
- нет typed delta reconciler;
- нет exact replay/stale-base implementation;
- нет dataset publish/readback transaction;
- `sqlite_store.py` содержит только initialize/validate/backup helpers.

### Workers

Не реализованы и не доказаны отдельные Region Talk kernels:

- Candidate/E5;
- BGE-M3;
- ImageDiagnostic;
- Source Profile.

В `config/stages.yml` обе model revisions всё ещё имеют значение `REQUIRED_PIN`, несмотря на контракт хранения точных revisions в versioned config.

## Дефекты целостности

### P0 — блокируют первый безопасный run

1. GitHub private Actions runner заблокирован Billing/Spending Limit.
2. Control workflow — явный bootstrap stub с `exit 1`.
3. Controller не имеет remote state acquisition и action executor.
4. Нет kernel push/poll/recovery/cleanup lifecycle.
5. Нет canonical state dataset и reconciler.
6. Нет runnable Region Talk workers.
7. E5/BGE model revisions не закреплены.

### P1 — блокируют доверие к результату и cutover

1. `MANIFEST.sha256` устарел, не включает ряд текущих файлов и не проверяется `scripts/validate_repository.py`.
2. SQLite migration receipt сохраняет literal placeholder `BOOTSTRAP_REPLACE_WITH_FILE_SHA256`, а не SHA migration file.
3. `validate.yml` использует mock/fake Kaggle tests; live dataset/kernel lifecycle test отсутствует.
4. Нет materializer для `product_metric_snapshots` и current reports.
5. `reports/current/README.md` — только placeholder; `ops-current` branch отсутствует.
6. `contents: read` недостаточно для документированного обновления `ops-current`, если не будет отдельного scoped writer.
7. Документ миграции называет environment `region-talk-ydb-migration`, фактически создан `region-talk-migration`.
8. Созданные environments не имеют protection rules; до production publish нужны required reviewer и branch/deployment restrictions.
9. Несколько заявленных invariants остаются только документацией: event-before-current-mutation, diagnostic query packs, metric snapshots и archive readback.

## Внешние параметры

### Уже доказано

- `KAGGLE_USERNAME`;
- `KAGGLE_KEY`.

Имена/наличие остальных repository/environment secrets GitHub App перечислить не может: API отвечает `403 Resource not accessible by integration`. Их нужно проверять по exact preflight в stage-specific canary, не выводя значения.

### Потребуется до YDB migration

- временный `REGION_TALK_YDB_READONLY_CREDENTIAL` в одном согласованном migration environment;
- protected migration environment;
- bounded export approval.

### Потребуется до review chat

- существующий `TELEGRAM_BOT_TOKEN`;
- `REGION_TALK_REVIEW_CHAT_ID`;
- exact reviewer allowlist.

Эти параметры не нужны для dataset lifecycle canary, fixture reconciler и E5/BGE smoke.

## Продуктовые показатели

Продуктовая модель в `docs/product-metrics.md` корректна по направлению. North-star outcome — не количество fetched rows и не зелёный controller, а регулярная доставка оператору новых, качественных, действительно публикуемых внешних взглядов на Калининградскую область.

### Главная иерархия

1. **Полезный выпуск pipeline:** `fresh_operator_candidates` за день/7 дней.
2. **Качество:** `operator_approved_candidates`, approval/rewrite/reject rate и reason distribution.
3. **End-to-end yield:** `source_discovery_to_operator_candidate_rate` и `research_intake_to_operator_candidate_rate`.
4. **Скорость:** `candidate_time_to_review_ready`, queue age p50/p90.
5. **Нулевой результат:** `cycles_with_zero_operator_candidates_rate` с проверенной причиной.
6. **Разнообразие:** unique sources, topics, places, article/social balance и concentration violations.
7. **Эффективность:** Kaggle CPU, provider calls и GitHub ticks на operator-approved candidate.
8. **Downstream:** scheduled/published candidates, on-time slot fill и duplicate/ambiguous publication incidents.

`published_candidates` нельзя использовать в одиночку как оценку discovery/editorial pipeline: на него влияют ручное решение оператора и ограниченное расписание. Ближайший управляемый outcome системы — operator-ready/approved candidate с quality/diversity guardrails.

### Текущий фактический статус метрик

Метрики **спроектированы, но не измеряются**:

- таблица `product_metric_snapshots` есть;
- granular source/post/candidate/review/outbox/provider tables есть;
- кода вычисления metric snapshots нет;
- `reports/current/product-metrics.json` не создаётся;
- первого full-run funnel нет;
- targets/alert thresholds ещё не калиброваны.

Текущие значения следует обозначать как `NOT_MEASURED`, а не как ноль.

## Минимальная задача кодовому агенту

Не реализовывать весь publisher одним большим изменением. Сначала завершить доказуемый launch foundation.

### Slice A — repository and runtime integrity

1. Исправить Billing вне кода и получить PASS `validate.yml` на exact `main` SHA.
2. Закрепить exact E5/BGE model revisions.
3. Довести единственный `KaggleRuntimeClient` от pinned `events-bot-new` blobs: staging, push/update, binding readback, polling, output recovery, cleanup.
4. Добавить manifest verification и удалить migration SHA placeholder.
5. Добавить live private ephemeral dataset create/ready/readback/version/delete canary.

### Slice B — deterministic state cycle

1. Создать/readback private state и run-history datasets.
2. Реализовать typed immutable delta envelope и reconciler.
3. Доказать: apply, exact replay no-op, stale base zero writes, integrity/FK checks, independent readback.
4. Реализовать persisted attempts/active-scope guard и terminal archive reconciliation.
5. Создать sanitized health/queue/product reports; дать writer минимальные scoped permissions.

### Slice C — worker smokes

1. Отдельный CPU Candidate/E5 fixture kernel.
2. Отдельный CPU BGE fixture kernel без Telegram/Google secrets.
3. Exact dataset-source binding и complete run bundle.
4. Failed kernel output recovery canary.
5. Image/Profile fixture smoke после базовых workers.

### Slice D — real cutover

1. Bounded YDB read-only export и 100% accounting.
2. Три shadow comparison cycle.
3. Один полный manual pipeline run без production publication.
4. Funnel/materialized metrics и P0/P1 review.
5. Только затем review-chat canary, private publish canary и решение об autonomous scheduler.

## Acceptance evidence

Кодовый агент должен вернуть:

- exact commit SHA;
- GitHub Actions run IDs;
- Kaggle dataset refs/versions и kernel refs/versions;
- state SHA before/after;
- replay/stale-base receipts;
- complete run-bundle checksums;
- product funnel counts и reason codes;
- current queue/product reports;
- список оставшихся внешних blockers.

Зелёный technical job без operator-ready candidates или доказанного supply explanation не считается продуктовым результатом.
