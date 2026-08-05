# Переиспользование рабочего Kaggle-контура `events-bot-new`

## Решение

Region Talk **не разрабатывает собственную Kaggle-инфраструктуру с нуля**. Транспорт и жизненный цикл удалённых запусков основаны на уже работающих контурах `Telegram Monitoring` и `CherryFlash` из приватного репозитория `onedayonemasterpiece/events-bot-new`.

Точный source baseline и blob SHA закреплены в [`config/kaggle-runtime-source.yml`](../config/kaggle-runtime-source.yml).

Это решение разделяет две области:

- **доказанная общая механика Kaggle** — переносится или адаптируется с сохранением поведения;
- **специфика Region Talk** — SQLite state, deltas, отдельные E5/BGE/Image стадии, research intake, продуктовые метрики, review queue и publisher.

## Что уже доказано Telegram Monitoring

Рабочий Telegram Monitoring реализует полный удалённый lifecycle:

1. формирует точный run ID и durable operations record;
2. проверяет, что выбранная Telegram session не занята;
3. строит минимальный stage-scoped набор секретов;
4. создаёт private временные Kaggle datasets;
5. ждёт статуса dataset `ready` и проверяет обязательные файлы;
6. подготавливает локальную копию kernel, status helper и зависимости;
7. обновляет kernel и привязывает exact dataset sources;
8. вычисляет timeout по реальному объёму источников;
9. опрашивает статус с bounded backoff для SSL/network/429/5xx;
10. при сбое status API пробует доказать завершение по свежему output;
11. скачивает output с повторными попытками;
12. импортирует результат идемпотентно;
13. удаляет временные datasets либо оставляет recovery receipt;
14. сохраняет прогресс и terminal evidence.

Для Region Talk этот lifecycle должен стать стандартным worker adapter, а не примером для переписывания.

## Что уже доказано CherryFlash

CherryFlash добавляет необходимые для длительных задач свойства:

- durable session row до запуска;
- запрет fire-and-forget для локального runner;
- проверка существующей активной render session;
- подтверждение remote handoff через dataset и kernel identity;
- ожидание terminal state через устойчивое состояние, а не память процесса;
- persisted retry cap, который не обнуляется после рестарта;
- heartbeat/terminal ledger как дополнительный источник истины;
- защита отдельных resource/video lanes;
- readback dataset-source binding до признания запуска состоявшимся.

Для Region Talk это означает: GitHub tick может быть коротким, но сам запуск обязан иметь durable attempt, heartbeat и recovery path.

## Общий runtime, который переиспользуется

### `video_announce/kaggle_client.py`

Это единственный базовый Kaggle transport. Из него переносятся или адаптируются:

- authentication через официальный client;
- create dataset / create version / delete;
- dataset status и file listing;
- `await_dataset_ready`;
- push/update kernel;
- проверка exact dataset sources;
- status lookup;
- output download;
- platform error diagnostics;
- подготовка script/notebook kernel;
- CPU/GPU metadata discipline.

Новый standalone client рядом с ним запрещён.

### `kaggle/kaggle_status_client.py`

Независимый worker-side helper перенесён в `src/region_talk_control/kaggle_status_client.py` с source provenance. Он создаёт локальный `kaggle_status_events.jsonl`, нормализует прогресс, отправляет heartbeat и освобождает resource leases.

### `kaggle_status.py`

Host-side ledger адаптируется к каноническому SQLite Region Talk. Сохраняются:

- hash callback token;
- append-only run events;
- `BEGIN IMMEDIATE` для одного writer;
- heartbeat freshness;
- terminal events;
- script/notebook instrumentation;
- recovery после неоднозначного platform state.

### `kaggle_registry.py`

Семантика active job registry сохраняется, но JSON-файл заменяется таблицами canonical SQLite. Нельзя иметь два независимых реестра текущих запусков.

### `remote_telegram_session.py`

Сохраняется fail-closed auth-scope guard:

- одинаковый DISCOVERY scope не запускается параллельно;
- неизвестный scope считается конфликтом;
- terminal kernel не держит lease;
- transient unknown status допускает освобождение только после bounded stale window и audit event.

## Как это ложится на Region Talk

```text
GitHub catch-up tick
        │
        ├─ читает canonical SQLite attempt/state
        ├─ выполняет recovery/reconcile
        └─ при необходимости создаёт один durable attempt
                         │
                         ▼
       events-bot-compatible Kaggle lifecycle
       prepare private inputs → wait ready → push kernel
       → verify binding → heartbeat/status → download output
                         │
                         ▼
       Region Talk schema/redaction/invariant checks
                         │
                         ▼
       SQLite delta commit → state dataset version/readback
                         │
                         ▼
       следующий короткий GitHub tick
```

GitHub Actions заменяет только место, где живёт scheduler/controller. Он **не заменяет** доказанные функции Telegram Monitoring и CherryFlash по запуску, диагностике и восстановлению Kaggle jobs.

## Стадии

Каждая стадия использует один общий lifecycle adapter:

| Stage | Models / credentials | Auth scope |
|---|---|---|
| Candidate/E5 | E5, DISCOVERY1, назначенные Google keys/limiter | `telegram:discovery1` |
| BGE-M3 | BGE-M3; без Telegram, Google и publisher credentials | нет |
| ImageDiagnostic | DISCOVERY2; visual key только если стадия реально его использует | `telegram:discovery2` |
| Source profile | DISCOVERY1 | `telegram:discovery1` |

E5 и BGE остаются разными kernels. Общим является lifecycle, а не Python process и не модельная память.

## Секреты

На первом рабочем cut используется уже доказанный private ephemeral dataset transport:

- точный allowlist по стадии;
- private dataset;
- ciphertext/key mechanics, совместимые с действующим launcher;
- удаление после terminal output;
- TTL garbage collection;
- exact-secret/prefix/high-entropy scan output.

Это не называется отдельной криптографической границей: границей является private Kaggle ACL. Новый sealed-box bootstrap не вводится без доказанной практической проблемы.

## Логи и отладка

Region Talk расширяет существующий status contract, но не меняет его основу:

- `kaggle_status_events.jsonl` — локальные worker events;
- stdout/stderr — забираются после terminal status;
- run manifest содержит source Git SHA, kernel version, input dataset versions и base state SHA;
- output download выполняется даже для failed kernel;
- отсутствие output классифицируется отдельно от worker exception;
- raw bundle архивируется до reconciliation;
- state commit хранит exact run/archive SHA.

## Проверки против повторного изобретения

CI должен блокировать:

- прямой `KaggleApi` вне compatibility runtime и отдельного auth-smoke;
- новый класс Kaggle client в другом модуле;
- запуск без dataset readiness/readback;
- запуск без durable attempt ID;
- Telegram worker без auth scope;
- повторное использование одной session параллельно;
- признание `COMPLETE` без свежего output/run ID;
- cleanup без durable recovery receipt;
- long polling в GitHub Actions.

## Что всё ещё нужно разработать

Переиспользование runtime не отменяет продуктовую работу:

- преобразовать legacy YDB rows в SQLite schema;
- перевести Region Talk workers с прямых YDB writes на immutable deltas;
- собрать Candidate/E5, BGE, Image и Profile kernels в новом private namespace;
- адаптировать host ledger/registry к SQLite snapshot commits;
- забрать полные logs и сохранить run-history;
- выполнить fixture, shadow и полный manual run;
- только после анализа включить scheduler;
- publisher остаётся отдельным release gate.

Но Kaggle authentication, dataset lifecycle, kernel handoff, polling, heartbeat, output recovery и cleanup больше не являются открытой архитектурной задачей.
