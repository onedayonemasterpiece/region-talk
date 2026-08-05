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
- лишние sealed-box, mandatory Supabase control-plane и manually-entered asset refs удалены из launch prerequisites;
- GitHub Secret `KAGGLE_KEY` добавлен и legacy `KAGGLE_USERNAME` + `KAGGLE_KEY` подтверждены реальным read-only Kaggle API-вызовом;
- Kaggle authentication smoke run `30990961846` прошёл: authenticated endpoint `kernels list --mine`, без создания dataset и без запуска kernel;
- sanitized receipt сохранён как artifact `8924068337`; repository validation для того же head также прошёл.

## Диагностическая запись первого smoke

Первый run `30990852958` не доказывал ошибку credential: presence preflight прошёл, а smoke упал на удалённом в `kaggle 1.8.4` Python-методе `quota_view` с `AttributeError`. Проверка заменена на поддерживаемый authenticated CLI endpoint `kaggle kernels list --mine`. Повторный run прошёл.

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

Они не блокируют state bootstrap, BGE/E5 fixture runs или local reconciler tests.

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

1. Создать и проверить deterministic private state/run-history datasets и kernel refs.
2. Реализовать state snapshot/reconciler и fixture cycle без Telegram/provider calls.
3. Выполнить отдельные Candidate/E5 и BGE CPU smoke runs.
4. Провести bounded YDB migration.
5. Выполнить полный ручной pipeline run и разобрать product metrics.
6. Только после исправления P0/P1 включить регулярный controller; publisher остаётся отдельным gate.
