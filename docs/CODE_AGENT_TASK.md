# Оставшаяся реализация Region Talk

## Главный принцип

Не проектировать Kaggle-контур заново. Использовать pinned рабочую реализацию из `onedayonemasterpiece/events-bot-new` по:

- `config/kaggle-runtime-source.yml`;
- `docs/kaggle-runtime-reuse.md`.

Нельзя создавать второй `KaggleClient`, новый transport секретов, отдельный polling framework или новый remote-session guard. Любое отклонение требует конкретного воспроизводимого дефекта существующего контура и regression test.

Не создавать GitHub issues.

## 1. Перенос доказанного runtime

От exact source blobs адаптировать в один compatibility package:

- generic части `video_announce/kaggle_client.py`;
- host ledger/instrumentation из `kaggle_status.py`;
- active-job semantics из `kaggle_registry.py`;
- auth-scope guard из `remote_telegram_session.py`.

Worker-side `kaggle_status_client.py` уже перенесён буквально с provenance.

Сохранить поведение Telegram Monitoring и CherryFlash:

- private temporary datasets;
- create/version/delete fallback;
- dataset `ready` + exact file readback;
- kernel staging/push;
- exact dataset-source binding readback;
- durable attempt/run ID;
- heartbeat и terminal events;
- bounded transient retries;
- fresh-output recovery при неоднозначном status API;
- output download retries;
- cleanup + recovery receipt;
- Telegram auth-scope conflict guard;
- persisted retry budgets.

Удалить только доменные зависимости Video/Event. Все intentional diffs перечислить в provenance document и покрыть тестами.

## 2. Region Talk state

- Каноническое состояние — SQLite snapshot в private `zigomaro/region-talk-state`.
- Run history — private `zigomaro/region-talk-run-history`.
- Workers не меняют canonical state: они возвращают immutable deltas и полный run bundle.
- Reconciler проверяет base version/SHA, применяет delta в `BEGIN IMMEDIATE`, выполняет integrity/invariant checks, публикует новую dataset version и делает независимый readback.
- Exact replay — no-op; stale base — zero writes.

## 3. Отдельные CPU workers

Создать private CPU-only kernels:

- `zigomaro/region-talk-candidate-e5`;
- `zigomaro/region-talk-bge-m3`;
- `zigomaro/region-talk-image-diagnostic`;
- `zigomaro/region-talk-source-profile` при подтверждённой необходимости отдельной стадии.

E5 и BGE-M3 запрещено загружать в один production kernel.

Scopes:

- Candidate/E5 и Profile: `telegram:discovery1`;
- Image: `telegram:discovery2`;
- BGE: без Telegram/Google/publisher credentials.

## 4. Research intake

После merge файла `research/intake/region-talk-external-research-result-<request_id>.json`:

1. проверить schema и identity conflicts;
2. импортировать exact trusted bytes в SQLite через reconciler;
3. повторный import сделать no-op;
4. любой конфликт должен блокировать весь пакет;
5. retained rows начать как `unreviewed/not_granted`;
6. отправить их в обычный E5 → BGE → fusion → image/profile → finalizer pipeline.

Исследование не может сразу согласовать или опубликовать материал.

## 5. Orchestrator

GitHub Actions выполняет короткий catch-up tick и выходит. Никакого long polling.

Приоритет:

1. terminal output/archive/reconcile recovery;
2. reaction/outbox/publication safety;
3. отправка готовых revisions в review chat;
4. finalizer/profile/image/fusion;
5. missing BGE;
6. exact research/manual links;
7. широкое discovery.

Пока ручной полный pipeline и анализ P0/P1 не завершены:

```text
REGION_TALK_ORCHESTRATOR_ENABLED=0
```

## 6. Логи и диагностика

Для каждого run сохранить:

- Git SHA, kernel version, input dataset versions, base state SHA;
- stdout/stderr;
- `kaggle_status_events.jsonl`;
- run/stage manifest;
- resource samples;
- provider usage без секретов;
- delta, metrics, exception и checksums;
- secret scan result.

GitHub Actions должен скачивать output и для failed kernels. Raw run bundle архивируется до reconciliation.

## 7. YDB migration

- Только bounded read-only export.
- Endpoint/database брать из versioned migration contract; требуется временный read-only credential.
- Учесть 100% строк, unknown kinds сохранить отдельно.
- Сверить counts и ordered hashes.
- Выполнить минимум три shadow comparison.
- YDB не удалять без отдельного решения владельца.

## 8. Review и publisher

- `👍/❤️` — approve exact revision;
- `👎` — reject;
- `✍` — rewrite requested;
- positive+negative — conflict;
- только allowlisted Telegram user IDs;
- любое изменение текста/URL/media/order/policy создаёт новый fingerprint.

Publisher: outbox, exact media hash, target identity readback, schedule/diversity rules, ambiguous-timeout history check. Сначала render-only и private canary; production publishing остаётся выключенным до отдельного утверждения.

## 9. Проверка

До scheduler enable выполнить:

1. repository/unit tests;
2. private dataset create/version/readback/delete canary через proven runtime;
3. fixture state/reconciler cycle;
4. отдельные E5 и BGE CPU smoke;
5. Image/Profile smoke;
6. YDB migration + shadow;
7. полный ручной pipeline;
8. продуктовый анализ: сколько кандидатов дошло до review-ready/published-ready и причины потерь;
9. исправление всех P0/P1 с regression tests.

Финальный отчёт должен содержать exact commit SHA, Actions/Kaggle run IDs, dataset/kernel versions, state SHA, queue/product metrics и оставшиеся внешние blockers. Не считать зелёные jobs продуктовым результатом без готовых кандидатов или доказанного объяснения их отсутствия.
