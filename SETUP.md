# Region Talk — только действительно внешние настройки

Репозиторий уже private, bootstrap установлен, repository validation пройден. Большая часть прежнего missing-values списка не является обязательной: имена Kaggle assets выводятся из `KAGGLE_USERNAME`, модели закрепляются в репозитории, target channel определяется по username, а отдельный Supabase control-plane для первого рабочего контура не нужен.

## Что требуется сейчас для первого Kaggle smoke

Страница GitHub Actions Secrets:
<https://github.com/onedayonemasterpiece/region-talk/settings/secrets/actions>

Добавить **один** из двух поддерживаемых вариантов Kaggle-аутентификации:

```text
KAGGLE_API_TOKEN
```

или переиспользовать уже работавшую legacy-пару:

```text
KAGGLE_USERNAME  # уже GitHub Variable
KAGGLE_KEY       # GitHub Secret
```

Не требовать оба варианта одновременно. Для текущего проекта предпочтительно сначала переиспользовать существующий `KAGGLE_KEY`, потому что именно этот контур уже работал в `events-bot-new`.

Уже добавленные Google/Supabase-limiter и Telegram DISCOVERY credentials сохраняются без изменений.

## Что потребуется позже, но не блокирует Kaggle smoke

### Review chat и публикация

Переиспользовать существующего бота, не создавать новый токен или новое имя секрета:

```text
TELEGRAM_BOT_TOKEN
```

Потребуется одна невычисляемая переменная:

```text
REGION_TALK_REVIEW_CHAT_ID
```

`REGION_TALK_TARGET_CHANNEL_ID` вручную не требуется: controller должен разрешить и проверить numeric ID по уже заданному `REGION_TALK_TARGET_CHANNEL_USERNAME=kalinigrad_visit`, затем сохранить подтверждённую identity в каноническом state.

### Одноразовая миграция YDB

Endpoint и database identity уже зафиксированы в миграционном контракте и не должны повторно вводиться вручную. На время экспорта нужен только временный read-only credential в environment `region-talk-migration`:

```text
REGION_TALK_YDB_READONLY_CREDENTIAL
```

После подтверждённой миграции credential удалить.

## Что больше не требуется

Не создавать и не запрашивать:

```text
REGION_TALK_SEALED_BOX_PUBLIC_KEY
REGION_TALK_SEALED_BOX_PRIVATE_KEY
REGION_TALK_SUPABASE_DIRECT_CONNECTION_STRING
REGION_TALK_YDB_ENDPOINT
REGION_TALK_YDB_DATABASE
REGION_TALK_STATE_DATASET
REGION_TALK_RUN_HISTORY_DATASET
REGION_TALK_KAGGLE_CANDIDATE_KERNEL
REGION_TALK_KAGGLE_BGE_KERNEL
REGION_TALK_KAGGLE_IMAGE_KERNEL
REGION_TALK_KAGGLE_PROFILE_KERNEL
REGION_TALK_E5_MODEL_REVISION
REGION_TALK_BGE_MODEL_REVISION
REGION_TALK_TARGET_CHANNEL_ID
```

Правила вывода:

```text
state dataset      = <KAGGLE_USERNAME>/region-talk-state
run history        = <KAGGLE_USERNAME>/region-talk-run-history
candidate kernel   = <KAGGLE_USERNAME>/region-talk-candidate-e5
bge kernel         = <KAGGLE_USERNAME>/region-talk-bge-m3
image kernel       = <KAGGLE_USERNAME>/region-talk-image-diagnostic
profile kernel     = <KAGGLE_USERNAME>/region-talk-source-profile
```

Точные model revisions хранятся в versioned repository config, а не вводятся как runtime Variables.

## Supabase

Для первой рабочей версии используется только уже существующий canonical Google AI limiter:

```text
GOOGLE_AI_LIMITER_SUPABASE_URL
GOOGLE_AI_LIMITER_SUPABASE_SERVICE_KEY
```

Новая схема `region_talk_control` и direct PostgreSQL connection откладываются. Сериализацию обеспечивают GitHub Actions concurrency и compare-and-set канонического state manifest. Отдельный compact operator projection в Supabase добавляется только если после первого полного прогона доказана практическая необходимость.

## Transport секретов в Kaggle

Первый рабочий контур переиспользует существующий механизм `events-bot-new`:

- GitHub формирует отдельный private ephemeral input dataset на конкретный stage/run;
- передаёт только минимальный stage-scoped набор секретов;
- BGE не получает Telegram или Google secrets;
- dataset удаляется после terminal run, а TTL-GC убирает утечки после аварий;
- outputs проходят secret scan.

Fernet key и ciphertext могут оставаться в одном private dataset, как в действующем launcher. Это не отдельная криптографическая граница: реальной границей является private Kaggle ACL. Не вводить дополнительную sealed-box пару до отдельного hardening-решения.

## Состояние запуска

```text
REGION_TALK_ORCHESTRATOR_ENABLED=0
```

оставить до успешного Kaggle authentication smoke, миграционного dry-run и полного ручного pipeline run. Production publisher также остаётся выключенным.
