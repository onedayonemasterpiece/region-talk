# Implementation status

## Завершено

- repository `onedayonemasterpiece/region-talk` переведён в private;
- unauthenticated repository/raw reads закрыты;
- bootstrap установлен в `main`;
- architecture, SQLite schema, contracts, editorial policy, testing and first-run methodology зафиксированы;
- отдельные E5/BGE CPU stages закреплены как invariant;
- repository validation workflow проходит;
- GitHub Actions включены, workflow permissions read/write, artifact/log retention 400 дней;
- environments созданы;
- scheduler/publisher feature gate сохранён `0`;
- Google AI limiter, Google keys, Telegram application credentials и DISCOVERY1/DISCOVERY2 bundles добавлены;
- лишние sealed-box, mandatory Supabase control-plane и manually-entered asset refs удалены из launch prerequisites.

## Реально отсутствует перед первым Kaggle authentication smoke

Один из двух Kaggle credentials:

```text
KAGGLE_KEY          # переиспользование действующей legacy-пары
```

или

```text
KAGGLE_API_TOKEN    # новый access token
```

Оба одновременно не нужны.

## Отдельные поздние зависимости

Перед review chat:

```text
TELEGRAM_BOT_TOKEN
REGION_TALK_REVIEW_CHAT_ID
```

Перед одноразовой YDB migration:

```text
REGION_TALK_YDB_READONLY_CREDENTIAL
```

Они не должны блокировать Kaggle auth, state bootstrap, BGE/E5 fixture runs или local reconciler tests.

## Ещё не реализовано/не выполнено

- production-ready Kaggle launcher/reconciler в новом репозитории;
- creation/readback private state и run-history datasets;
- actual Candidate/E5, BGE, Image and Profile kernels в новом owner namespace;
- one-time YDB export и SQLite reconciliation;
- review bot commands и exact reaction sync;
- publication planner/publisher runtime;
- первый полный CPU pipeline run;
- анализ первого прогона и подтверждение product funnel;
- включение регулярного scheduler.

## Ближайшая последовательность

1. Переиспользовать существующий `KAGGLE_KEY` и выполнить read-only Kaggle API smoke.
2. Создать/проверить deterministic private dataset/kernel refs.
3. Реализовать state snapshot/reconciler и fixture cycle без Telegram/provider calls.
4. Выполнить отдельные Candidate/E5 и BGE CPU smoke runs.
5. Провести bounded YDB migration.
6. Выполнить полный ручной pipeline run и разобрать product metrics.
7. Только после исправления P0/P1 включить регулярный controller; publisher остаётся отдельным gate.
