# Region Talk — административная настройка

Репозиторий уже содержит проверенный bootstrap и одноразовый установочный workflow. Кодовому агенту не нужно получать файлы, проектировать архитектуру или писать реализацию.

## 1. Обязательные действия

1. Перевести репозиторий в **Private**: <https://github.com/onedayonemasterpiece/region-talk/settings>.
2. Запустить **Install Region Talk bootstrap**: <https://github.com/onedayonemasterpiece/region-talk/actions/workflows/bootstrap-region-talk.yml>.
3. После установки добавить перечисленные ниже GitHub Secrets и Variables.
4. Запустить **Validate Region Talk repository**: <https://github.com/onedayonemasterpiece/region-talk/actions/workflows/validate.yml>.
5. Вернуть ссылки на оба run, подтверждение `visibility=private`, список добавленных имён без значений и missing-values report.

## 2. GitHub Actions Secrets

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

Добавить также все реально используемые дополнительные ключи Google под уже принятыми в проекте именами `GOOGLE_API_KEY2...N`; не создавать фиктивные значения.

Временные, только для environment миграции YDB:

```text
REGION_TALK_YDB_ENDPOINT
REGION_TALK_YDB_DATABASE
REGION_TALK_YDB_READONLY_CREDENTIAL
```

Опциональные, не добавлять до включения VK:

```text
VK_SERVICE_TOKEN
VK_ACCESS_TOKEN
```

## 3. GitHub Actions Variables

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
```

Не выдумывать неизвестные значения: перечислить их в missing-values report.

## 4. Environments

Страница: <https://github.com/onedayonemasterpiece/region-talk/settings/environments>

Создать:

```text
region-talk-migration
region-talk-production-publish
```

Для `region-talk-production-publish` включить required reviewer. Production publisher и scheduler не включать в этой административной задаче.

## 5. Kaggle User Secret

В аккаунте Kaggle установить:

```text
REGION_TALK_SEALED_BOX_PRIVATE_KEY
```

Значение не копировать в GitHub, stdout, issues, PR или Actions artifacts.

## Запреты

- не реализовывать и не перепроектировать pipeline;
- не выводить значения секретов;
- не включать production scheduler/publisher;
- не удалять YDB до отдельного подтверждённого cutover;
- не ослаблять private/secret boundaries ради прохождения проверки.
