# Безопасность и секреты

## 1. Базовая граница

- GitHub repository `onedayonemasterpiece/region-talk` — private.
- Все Region Talk Kaggle kernels, state datasets, run-history datasets и временные input datasets — private.
- Fork/PR jobs не получают production secrets.
- BGE worker не получает Telegram, bot или Google credentials.
- Scheduler и publisher остаются выключенными до canary.

## 2. Kaggle-аутентификация из GitHub

Поддерживаются оба официальных способа:

1. современный GitHub Secret `KAGGLE_API_TOKEN`;
2. уже работавшая legacy-пара `KAGGLE_USERNAME` + GitHub Secret `KAGGLE_KEY`.

Первый smoke не должен блокироваться только потому, что не создан новый token, если существующий legacy key продолжает проходить authenticated Kaggle API probe. Не хранить `kaggle.json`, access token или key в репозитории и artifacts.

## 3. Transport runtime-секретов в Kaggle

Для первого рабочего контура используется уже доказанный механизм `events-bot-new`, а не новая sealed-box инфраструктура:

1. GitHub Actions собирает минимальный allowlist секретов для конкретного stage.
2. Для run создаётся уникальный private ephemeral Kaggle Dataset.
3. Secret payload шифруется Fernet; ciphertext и key находятся в одной private dataset version, чтобы Kaggle не смонтировал рассинхронизированные версии.
4. Kernel читает payload только в памяти и не копирует его в output.
5. После terminal run dataset удаляется; bounded TTL-GC удаляет забытые временные datasets после падения controller.
6. Output/archive перед commit проходит exact-secret/HMAC/prefix/high-entropy scan.

Важно: Fernet key рядом с ciphertext **не является самостоятельной криптографической границей**. Он уменьшает риск случайного отображения payload, но реальная граница — private Kaggle account/dataset ACL. Не описывать этот механизм как защиту от компрометации Kaggle account.

Дополнительная sealed-box public/private key pair и обязательный Kaggle User Secret в MVP удалены: они создавали новый ручной bootstrap и не были нужны для уже работавшего способа запуска. Kaggle User Secrets можно позже принять как hardening после отдельного API-started smoke, но их отсутствие не блокирует pipeline.

## 4. Stage-scoped allowlists

### Candidate/E5 и source profile — DISCOVERY1

```text
TG_API_ID
TG_API_HASH
TELEGRAM_AUTH_BUNDLE_DISCOVERY1
GOOGLE_AI_LIMITER_SUPABASE_URL
GOOGLE_AI_LIMITER_SUPABASE_SERVICE_KEY
только назначенные stage Google keys
```

### ImageDiagnostic / reaction read — DISCOVERY2

```text
TG_API_ID
TG_API_HASH
TELEGRAM_AUTH_BUNDLE_DISCOVERY2
```

Google key добавляется только для реально включённого visual-LLM stage.

### BGE

Не получает ни одного Telegram, bot, publisher, Supabase service или Google secret.

### Review notifier / publisher

Переиспользует существующий GitHub Secret:

```text
TELEGRAM_BOT_TOKEN
```

Не создавать отдельный bot и отдельное имя `REGION_TALK_TELEGRAM_BOT_TOKEN`, если используется тот же бот.

### Migration

Только временный environment secret:

```text
REGION_TALK_YDB_READONLY_CREDENTIAL
```

YDB endpoint/database являются versioned expected identity в миграционном коде. Credential удаляется после export/readback.

## 5. Supabase

В первой рабочей версии Kaggle получает только доступ к уже существующему canonical Google AI limiter. Новая `region_talk_control` schema и direct PostgreSQL credential не являются launch prerequisites.

## 6. Role separation

- DISCOVERY1: candidate/source text acquisition и source profile capture.
- DISCOVERY2: image acquisition и exact reaction observation.
- Bot: review notification, commands и approved publication.
- BGE: vector enrichment без внешних продуктовых credentials.
- Reconciler: Kaggle/state orchestration; не получает Telegram user session без необходимости.
- Migration: YDB read-only и временно.

Один Telegram auth bundle нельзя использовать в двух одновременных kernels. Каждая attempt декларирует `auth_scope`; конфликт блокирует launch.

## 7. Что нельзя логировать

- env/config dumps;
- secret values, Authorization headers и signed URLs;
- Telegram session bundles/device metadata;
- Supabase service key, Google/VK/Kaggle tokens;
- encrypted payload или Fernet key;
- `.env`, `kaggle.json`, `.session`, `.pem`, `.key` files;
- исключения вместе с request headers/body, если они могут содержать credentials.

Допустимы только role/scope ID, provider/model, request fingerprint, duration, usage, redacted status/reason и canonical URL без credentials.

## 8. Secret scan и incident response

Перед публикацией output/state/archive проверять:

- exact fingerprints всех injected secrets;
- известные prefixes и JWT/session/private-key patterns;
- URL query credentials;
- suspicious high-entropy strings;
- запрещённые filenames.

При обнаружении:

1. остановить orchestrator/publisher;
2. удалить/закрыть affected temporary datasets и artifacts;
3. rotate key/session;
4. проверить provider usage и Telegram active sessions;
5. добавить regression fixture;
6. возобновить работу только после clean canary.
