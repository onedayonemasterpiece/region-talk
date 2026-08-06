# Восстановление рабочего Region Talk без переписывания продукта

## Диагноз

Вынос в `onedayonemasterpiece/region-talk` не был полным переносом работавшего Region Talk.

Рабочий YDB-контур остался в `onedayonemasterpiece/events-bot-new`:

- `scripts/region_talk_scheduled_runner.py` — старый bounded scheduler entrypoint;
- `scripts/region_talk_orchestrator.py` — production queue/product orchestrator;
- финализатор, операторская очередь, reaction sync, publication plan, source profiles и research intake;
- private Kaggle Candidate/E5, BGE-M3 и ImageDiagnostic workers;
- тестовый корпус Region Talk.

В отдельном репозитории вместо этих файлов появился новый SQLite/Kaggle control-plane bootstrap. Он не является эквивалентом старого runtime и не должен блокировать восстановление работавшего продукта.

## Правильная граница миграции

На первом этапе GitHub Actions заменяет только старый APScheduler/Fly trigger:

```text
старый scheduler/Fly invocation
        ↓ заменяется
GitHub Actions bounded tick
        ↓ вызывает без изменения
старый YDB orchestrator + старые Kaggle workers
```

YDB → SQLite/Kaggle state redesign является отдельной последующей миграцией. Она не входит в parity gate и не может использоваться как причина отсутствия работающего Region Talk.

## Точный источник

До механического переноса исходников в этот репозиторий используется immutable source checkout:

```text
repository: onedayonemasterpiece/events-bot-new
commit: 5bbdb681623d5e4e0bff2133e487a6663c1a838a
```

`config/legacy-runtime-source.yml` фиксирует blob SHA критических файлов. `scripts/legacy_region_talk_adapter.py` прекращает запуск при любом несовпадении commit или blob identity.

Это временная provenance-мера, а не новая архитектура и не постоянная runtime-зависимость от монорепозитория.

## Реализованные режимы

### `preflight`

Не меняет YDB и не запускает Kaggle. Выполняет старый production `--preflight-only` и возвращает только имена отсутствующих групп конфигурации.

### `plan`

Читает live YDB и строит старый decision plan без запуска actions. Receipt сохраняет продуктовые funnel-метрики и причины следующих действий.

### `canary`

Может выполнить ровно один action из allowlist:

```text
launch_candidate_report
launch_bge_m3
launch_image_diagnostic
```

Local notifier, finalizer, publication planner и publisher в canary не допускаются.

### `scheduled`

Вызывает прежний `region_talk_scheduled_runner.py` с bounded runtime и single-flight semantics. Регулярный режим закрыт переменной `REGION_TALK_ORCHESTRATOR_ENABLED`.

Во всех recovery-режимах принудительно:

```text
REGION_TALK_TELEGRAM_PUBLISH_ENABLED=0
REGION_TALK_VK_PUBLISH_ENABLED=0
```

## Уже полученные доказательства

### Исходный публичный репозиторий

Recovery run `31087575599`:

- exact source checkout прошёл;
- production runner найден и импортирован;
- немутирующий preflight исполнен;
- YDB не менялась;
- Kaggle не запускался;
- выявлены только группы runtime settings, которых нет в публичном репозитории.

Recovery/source-export run `31087801405`:

- exact source и критические файлы подтверждены;
- создан manifest-backed export работавшей реализации;
- повторный preflight исполнен;
- source artifact `8962131799` сохранён для dependency audit.

### Отдельный private репозиторий

Parity run `31088549523` создан на commit `aaea166fe2953d1062b78ab8d00363c3d737637c`, но GitHub не назначил runner: job завершился до первого step из-за account Billing/Spending Limit. Это не runtime failure и не повод возвращаться к переписыванию системы.

## Дальнейшая последовательность

1. Запустить `preflight` в `region-talk` после доступности private Actions runner.
2. Добавить только реально отсутствующие settings под точными старыми именами или их явными aliases.
3. Выполнить `plan` и сохранить live product funnel.
4. Выполнить один `canary` private Kaggle action.
5. Проверить terminal worker output и изменения YDB.
6. Выполнить один bounded `scheduled` tick с выключенной публикацией.
7. Механически перенести dependency-closed source tree и tests в `region-talk` с hash manifest.
8. Переключить workflow с immutable cross-repository checkout на local source.
9. Удалить Region Talk runtime из `events-bot-new`, оставив только migration provenance при необходимости.
10. Рассматривать SQLite redesign отдельным shadow/cutover проектом после подтверждённого parity.

Кодовый агент не требуется для восстановления parity: задача состоит в переносе существующего кода, проверке runtime settings и запуске известного entrypoint, а не в проектировании новой системы.
