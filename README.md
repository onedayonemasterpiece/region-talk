# Region Talk

Автономный CPU-only контур поиска, проверки, редакционной подготовки, операторского согласования и публикации внешних материалов о Калининградской области.

> Статус этого пакета: implementation-ready bootstrap. Он предназначен для первого коммита в `onedayonemasterpiece/region-talk` после обязательного перевода репозитория в private. Производственный cutover выполняется только после миграции YDB, shadow-сравнения и полного canary.

## Продуктовый результат

Система должна непрерывно, пусть и не мгновенно:

1. находить внешние русскоязычные публикации о Калининградской области;
2. принимать вручную исследованные статьи через versioned JSON intake;
3. обрабатывать текст отдельными CPU-контурами E5 и BGE-M3;
4. проверять источник, региональность, содержательность, рекламу, новости, визуал и редакционную пригодность;
5. готовить точную media-first ревизию публикации;
6. отправлять её в закрытый Telegram review chat;
7. связывать `👍/❤️`, `👎` и `✍` с точной ревизией текста и медиа;
8. планировать только согласованные ревизии с учётом расписания, разнообразия и идемпотентности;
9. публиковать в целевой Telegram-канал;
10. сохранять достаточную историю, чтобы в любой момент объяснить результат, воспроизвести ошибку и измерить продуктовую эффективность.

## Главные архитектурные решения

- **Каноническое продуктовое состояние:** SQLite-снимок в приватном versioned Kaggle Dataset.
- **Тяжёлое исполнение:** отдельные приватные Kaggle CPU kernels.
- **E5 и BGE-M3:** разные kernels и разные стадии; одновременная загрузка моделей в один notebook запрещена production policy.
- **Единственный коммиттер:** GitHub Actions reconciler. Kaggle workers возвращают immutable deltas и никогда самостоятельно не меняют канонический HEAD.
- **Оркестрация:** короткий catch-up controller в GitHub Actions каждые 15 минут, ручной dispatch и bounded chain-dispatch после завершения стадии.
- **Supabase:** существующий единый Google AI limiter сохраняется. В отдельной схеме допускается только компактный control-plane и operator projection; полное состояние, логи, медиа и корпуса туда не переносятся.
- **История:** каждая стадия создаёт полный диагностический run bundle; GitHub Actions забирает его сразу после terminal status, проверяет redaction/checksums и сохраняет двумя копиями.
- **YDB:** только временный источник миграции и rollback. После подтверждённого cutover не участвует в рабочем цикле.
- **Публикация:** outbox + exact revision fingerprint + повторная проверка реакций + platform idempotency key.
- **Редакционная основа:** «спокойный культурный навигатор с редакционным теплом»; факты и CTA заблокированы от стилистической выдумки.

## Топология

```text
GitHub private repository
  ├─ source / schemas / migrations / policies / research JSON
  ├─ short controller + reconciler Actions
  └─ current compact reports for operator and ChatGPT inspection
                  │
                  ▼
       private Kaggle CPU workers
  Candidate/E5 ──► BGE ──► Image ──► Profile/Finalizer
                  │ immutable deltas + logs
                  ▼
        GitHub Actions reconciler
  validate base version → SQLite transaction → invariants
  → new state dataset version → operator projections
                  │
      ┌───────────┴───────────┐
      ▼                       ▼
private Kaggle state     existing Supabase project
and run-history datasets tiny control/operator tables
      │                       │
      └───────────┬───────────┘
                  ▼
       Telegram review chat
   reactions → schedule → publisher
                  ▼
       @kalinigrad_visit
```

## Репозиторная карта

- `docs/architecture.md` — границы системы и потоки данных.
- `docs/orchestrator.md` — state machine, cron, leases и восстановление.
- `docs/state-history-observability.md` — SQLite, manifests, логи и retention.
- `docs/supabase-boundary.md` — что именно допустимо хранить в Supabase.
- `docs/ydb-migration.md` — одноразовая миграция и сверка.
- `docs/research-intake.md` — добавление новых исследований через JSON.
- `docs/review-publishing.md` — review chat, реакции, очередь и publisher.
- `docs/testing-debugging.md` — методика тестирования, fault injection и расследований.
- `docs/product-metrics.md` — метрики результата, а не только технической активности.
- `docs/first-full-run.md` — обязательный анализ первого полного цикла.
- `docs/security-and-secrets.md` — секреты, роли и запрет утечек.
- `docs/CODE_AGENT_TASK.md` — точная постановка кодовому агенту.
- `docs/editorial/` — редакционная политика, Writer contract, quality framework и provenance.
- `sql/sqlite/` — каноническая operational schema.
- `sql/supabase/` — минимальный control-plane.
- `schemas/` — контракты run/delta/log/research.
- `.github/workflows/` — безопасные skeleton workflows.

## Release gates

До первого production-поста обязательны:

1. репозиторий и все Kaggle assets подтверждены private;
2. секреты не попадают в input/output datasets, stdout, artifacts и manifests;
3. YDB export и SQLite import совпадают по row counts и ordered hashes;
4. повтор одного delta даёт zero changes;
5. stale-base delta блокируется без частичной записи;
6. E5 и BGE проходят отдельные CPU smoke runs;
7. полный run bundle загружается, извлекается и анализируется;
8. review reaction sync доказан на точных reviewer IDs;
9. private test-channel publisher canary проходит exact-media и idempotency gates;
10. первый полный цикл разобран по `docs/first-full-run.md`;
11. только затем один явно согласованный production candidate публикуется canary-режимом.
