# Region Talk — только административные настройки

Репозиторий и проверяемый bootstrap уже загружены. Установку, коммиты, workflow-файлы и запуск repository validation выполняет ChatGPT. Кодовый агент не должен реализовывать pipeline или запускать установочные workflow.

## 1. Сделать репозиторий приватным

Репозиторий: <https://github.com/onedayonemasterpiece/region-talk>

Настройки visibility: <https://github.com/onedayonemasterpiece/region-talk/settings>

После изменения проверить, что unauthenticated запрос к репозиторию не раскрывает содержимое.

## 2. Настроить GitHub Actions

Actions settings: <https://github.com/onedayonemasterpiece/region-talk/settings/actions>

- Workflow permissions: **Read and write permissions**.
- Artifact/log retention: **400 days**, если тариф и интерфейс GitHub позволяют это значение.
- Не включать production scheduler или publisher.

## 3. Добавить GitHub Actions Secrets

Страница: <https://github.com/onedayonemasterpiece/region-talk/settings/secrets/actions>

Обязательные:

```text
KAGGLE_API_TOKEN
GOOGLE_AI_LIMITER_SUPABASE_URL
GOOGLE_AI_LIMITER_SUPABASE_SERVICE_KEY
GOOGLE_API_KEY
TG_API_ID
TG_API_HASH
TELEGRAM_AUTH_BUNDLE_DISCOVERY1
TELEGRAM_AUTH_BUNDLE_DISCOVERY2
REGION_TALK_TELEGRAM_BOT_TOKEN
REGION_TALK_MANIFEST_HMAC_KEY
REGION_TALK_SUPABASE_DIRECT_CONNECTION_STRING
```

Добавить также только реально используемые дополнительные ключи Google под уже принятыми именами `GOOGLE_API_KEY2...N`. Не создавать фиктивные значения.

Временные, только для environment миграции YDB:

```text
REGION_TALK_YDB_ENDPOINT
REGION_TALK_YDB_DATABASE
REGION_TALK_YDB_READONLY_CREDENTIAL
```

Не добавлять до отдельного включения VK:

```text
VK_SERVICE_TOKEN
VK_ACCESS_TOKEN
```

## 4. Добавить GitHub Actions Variables

Страница: <https://github.com/onedayonemasterpiece/region-talk/settings/variables/actions>

```text
KAGGLE_USERNAME
REGION_TALK_STATE_DATASET
REGION_TALK_RUN_HISTORY_DATASET
REGION_TALK_KAGGLE_CANDIDATE_KERNEL
REGION_TALK_KAGGLE_BGE_KERNEL
REGION_TALK_KAGGLE_IMAGE_KERNEL
REGION_TALK_KAGGLE_PROFILE_KERNEL
REGION_TALK_E5_MODEL_REVISION
REGION_TALK_BGE_MODEL_REVISION
REGION_TALK_REVIEW_CHAT_ID
REGION_TALK_OPERATOR_REVIEWER_IDS
REGION_TALK_TARGET_CHANNEL_ID
REGION_TALK_TARGET_CHANNEL_USERNAME=kalinigrad_visit
REGION_TALK_PUBLICATION_SLOTS_LOCAL
REGION_TALK_TIMEZONE=Europe/Kaliningrad
REGION_TALK_SUPABASE_SCHEMA=region_talk_control
REGION_TALK_SEALED_BOX_PUBLIC_KEY
REGION_TALK_ORCHESTRATOR_ENABLED=0
```

Не выдумывать неизвестные значения. Внести доступные и вернуть `missing-values report` по остальным.

## 5. Создать GitHub Environments

Страница: <https://github.com/onedayonemasterpiece/region-talk/settings/environments>

```text
region-talk-control
region-talk-migration
region-talk-production-publish
```

Для `region-talk-production-publish` включить required reviewer. Production publisher и scheduler оставить выключенными.

## 6. Добавить Kaggle User Secret

В аккаунте Kaggle установить:

```text
REGION_TALK_SEALED_BOX_PRIVATE_KEY
```

Значение нельзя копировать в GitHub, stdout, issues, PR, datasets или Actions artifacts.

## Что вернуть

- подтверждение `visibility=private` и проверку отсутствия публичного чтения;
- список добавленных Secret/Variable/Environment names без значений;
- подтверждение GitHub Actions permissions/retention;
- подтверждение имени Kaggle User Secret без значения;
- список реально недостающих значений.

## Запреты

- не реализовывать и не перепроектировать pipeline;
- не запускать bootstrap или validation workflow;
- не выводить значения секретов;
- не включать production scheduler/publisher;
- не удалять YDB;
- не ослаблять private/secret boundaries ради прохождения проверки.
