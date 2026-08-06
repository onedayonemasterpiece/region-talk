# Region Talk

Автономный контур поиска, проверки, редакционной подготовки, операторского согласования и публикации внешних материалов о Калининградской области.

> **Фактический статус:** работавший YDB-backed Region Talk не был полностью перенесён из `events-bot-new`. В этом репозитории первоначально оказался новый SQLite/Kaggle bootstrap, а не production-equivalent runtime. Восстановление идёт через exact YDB parity: GitHub Actions заменяет только прежний APScheduler/Fly trigger и вызывает неизменённый рабочий commit `5bbdb681623d5e4e0bff2133e487a6663c1a838a`. Production publisher остаётся выключенным.

Подробный диагноз и порядок восстановления: [`docs/ydb-parity-recovery.md`](docs/ydb-parity-recovery.md).

## Продуктовый результат

Region Talk полезен, когда регулярно доставляет оператору **новые, качественные и действительно публикуемые внешние взгляды на Калининградскую область**, а не просто создаёт технические очереди или зелёные workflow.

Рабочий продуктовый контур должен:

1. находить внешние русскоязычные публикации о Калининградской области;
2. принимать вручную исследованные статьи;
3. обрабатывать текст отдельными CPU-контурами E5 и BGE-M3;
4. проверять источник, региональность, содержательность, рекламу, новости, визуал и редакционную пригодность;
5. готовить точную media-first ревизию публикации;
6. отправлять её в закрытый Telegram review chat;
7. связывать `👍/❤️`, `👎` и `✍` с точной ревизией текста и медиа;
8. планировать только согласованные ревизии с учётом расписания, разнообразия и идемпотентности;
9. публиковать в целевой Telegram-канал только после отдельного gate;
10. сохранять историю для воспроизведения ошибок и измерения продуктовой эффективности.

## Текущий recovery-контур

```text
GitHub Actions bounded control tick
              │
              ▼
exact checkout events-bot-new@5bbdb681...
              │
              ▼
working YDB orchestrator
   ├─ Candidate/E5 Kaggle worker
   ├─ BGE-M3 Kaggle worker
   ├─ ImageDiagnostic Kaggle worker
   ├─ finalizer / source profile
   └─ operator review queue
              │
              ▼
existing YDB product state
```

Критические правила:

- никакого нового аналога Region Talk до восстановления parity;
- exact commit и blob SHA проверяются перед каждым запуском;
- `preflight` не меняет YDB и не запускает Kaggle;
- `plan` читает YDB, но не выполняет actions;
- `canary` может запустить ровно один private Kaggle worker из allowlist;
- регулярный `scheduled` mode закрыт `REGION_TALK_ORCHESTRATOR_ENABLED`;
- Telegram/VK production publishing принудительно выключен в recovery workflow.

## Целевая архитектура после parity

Зафиксированная SQLite/Kaggle architecture остаётся возможным следующим этапом, но больше не считается предпосылкой запуска работавшего продукта:

- каноническое продуктовое состояние — SQLite snapshot в private versioned Kaggle Dataset;
- workers возвращают immutable deltas;
- GitHub Actions reconciler применяет compare-and-set и проверяет invariants;
- E5 и BGE-M3 работают в отдельных CPU kernels;
- YDB становится read-only migration/rollback source только после доказанного shadow cutover;
- publication outbox использует exact revision/media fingerprints и idempotency keys.

Этот redesign должен проходить отдельные shadow comparisons с работающим YDB-контуром. Необъяснимое исчезновение кандидатов является cutover blocker.

## Репозиторная карта

### Recovery/parity

- `config/legacy-runtime-source.yml` — exact source commit и blob SHA рабочего YDB runtime;
- `scripts/legacy_region_talk_adapter.py` — provenance/safety adapter без повторной реализации продукта;
- `.github/workflows/region-talk-control.yml` — preflight, plan, one-worker canary и bounded scheduled tick;
- `docs/ydb-parity-recovery.md` — фактический диагноз и последовательность восстановления;
- `tests/test_legacy_region_talk_adapter.py` — защита canary allowlist и sanitized receipts.

### Целевая архитектура

- `config/kaggle-runtime-source.yml` — pinned provenance общего Kaggle lifecycle;
- `docs/architecture.md` — будущие границы системы и потоки данных;
- `docs/orchestrator.md` — future state machine и recovery;
- `docs/state-history-observability.md` — SQLite, manifests, logs и retention;
- `docs/ydb-migration.md` — отдельный shadow/cutover план;
- `docs/product-metrics.md` — outcome, funnel, quality, diversity и efficiency metrics;
- `sql/sqlite/` — целевая canonical schema;
- `schemas/` — будущие run/delta/log/research contracts.

## Parity gates

До включения регулярного GitHub scheduler:

1. exact old source commit/blob verification проходит;
2. production preflight не сообщает отсутствующих runtime settings;
3. YDB read-only plan возвращает текущий продуктовый funnel и decision plan;
4. один private Candidate/E5, BGE или Image canary запускается и даёт terminal output;
5. изменения YDB после canary объяснимы и соответствуют старому контракту;
6. один bounded scheduled tick завершается без duplicate launch и без публикации;
7. product metrics показывают движение кандидатов или точную причину zero-yield;
8. dependency-closed source tree и Region Talk tests механически перенесены в этот репозиторий;
9. workflow переключён с cross-repository checkout на local code;
10. Region Talk runtime удалён из `events-bot-new` после подтверждённого parity.

## Publication gates

Production publication остаётся отдельным этапом:

1. review reactions доказаны на exact reviewer IDs и exact revision fingerprint;
2. private test-channel canary проходит media/idempotency gates;
3. queue/product metrics и причины отказов доступны оператору;
4. только затем выполняется один явно согласованный production canary.
