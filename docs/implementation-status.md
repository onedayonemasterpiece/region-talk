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
- sanitized receipt сохранён как artifact `8924068337`; repository validation для того же head также прошёл;
- проведён аудит реально работающих Kaggle-контуров `Telegram Monitoring` и `CherryFlash` в `events-bot-new`;
- принято обязательное решение: Region Talk переиспользует их общий lifecycle, а не создаёт второй Kaggle transport;
- exact source repository, commit и blob SHA закреплены в `config/kaggle-runtime-source.yml`;
- worker-side `kaggle_status_client.py` перенесён с provenance в `src/region_talk_control/kaggle_status_client.py`;
- добавлен regression test, запрещающий прямой Kaggle API client вне одного compatibility runtime;
- полный reuse-контракт зафиксирован в `docs/kaggle-runtime-reuse.md`.

## Диагностическая запись первого smoke

Первый run `30990852958` не доказывал ошибку credential: presence preflight прошёл, а smoke упал на удалённом в `kaggle 1.8.4` Python-методе `quota_view` с `AttributeError`. Проверка заменена на поддерживаемый authenticated CLI endpoint `kaggle kernels list --mine`. Повторный run прошёл.

Этот инцидент дополнительно подтвердил правило: Kaggle API, polling и recovery нельзя разрабатывать по предположениям. Они должны переноситься из уже работающего `events-bot-new` и меняться только под regression tests.

## Доказанная Kaggle-база, которая больше не является открытым вопросом

Из `events-bot-new` переиспользуются:

- официальный Kaggle client/authentication;
- private dataset create/version/delete;
- ожидание dataset ready и file readback;
- kernel packaging/push и exact dataset-source binding;
- heartbeat, progress events и terminal ledger;
- durable active-job registry;
- Telegram auth-scope conflict guard;
- bounded status polling и transient SSL/network/429/5xx handling;
- completion recovery через fresh output, если status endpoint неоднозначен;
- output download retries;
- cleanup и recovery receipts;
- durable handoff/session/retry patterns CherryFlash.

GitHub Actions остаётся местом короткого Region Talk scheduler/controller, но не заменяет эту механику собственной реализацией.

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

- compatibility adapter общего `events-bot-new` Kaggle client без доменных Video/Event imports;
- адаптация host status ledger и active-job registry к canonical Region Talk SQLite;
- creation/readback private state и run-history datasets;
- actual Candidate/E5, BGE, Image and Profile kernels в новом owner namespace;
- перевод Region Talk workers с YDB writes на immutable SQLite deltas;
- one-time YDB export и SQLite reconciliation;
- review bot commands и exact reaction sync;
- publication planner/publisher runtime;
- первый полный CPU pipeline run;
- анализ первого прогона и подтверждение product funnel;
- включение регулярного scheduler.

## Ближайшая последовательность

1. Перенести/adapt generic `KaggleClient`, host status ledger, registry и auth-scope guard строго от pinned source blobs.
2. Создать и проверить deterministic private state/run-history datasets и kernel refs через тот же proven lifecycle.
3. Реализовать state snapshot/reconciler и fixture cycle без Telegram/provider calls.
4. Выполнить отдельные Candidate/E5 и BGE CPU smoke runs.
5. Провести bounded YDB migration.
6. Выполнить полный ручной pipeline run и разобрать product metrics.
7. Только после исправления P0/P1 включить регулярный controller; publisher остаётся отдельным gate.
