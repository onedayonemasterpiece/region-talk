# Что действительно требуется от владельца продукта

Большинство имён и identifiers система должна вывести сама. Не нужно заводить новую инфраструктуру только ради bootstrap.

## Уже достаточно для Kaggle discovery/vector smoke

Уже установлены:

- `KAGGLE_USERNAME`;
- Google AI limiter URL/key;
- активные `GOOGLE_API_KEY*`;
- `TG_API_ID` / `TG_API_HASH`;
- `TELEGRAM_AUTH_BUNDLE_DISCOVERY1` / `DISCOVERY2`;
- reviewer IDs, timezone и publication slots.

Не хватает только одного Kaggle authentication secret:

```text
KAGGLE_KEY
```

если переиспользуется существующая legacy-аутентификация, **либо** `KAGGLE_API_TOKEN`. Оба одновременно не нужны.

## Потребуется перед review-chat canary

1. Numeric ID существующего Region Talk review chat:

```text
REGION_TALK_REVIEW_CHAT_ID
```

2. Значение уже существующего bot secret под стандартным именем:

```text
TELEGRAM_BOT_TOKEN
```

Новый бот и `REGION_TALK_TELEGRAM_BOT_TOKEN` не требуются.

Target channel numeric ID вручную не нужен: он разрешается и верифицируется по `@kalinigrad_visit` при preflight.

## Потребуется только для одноразовой миграции

В environment `region-talk-migration` на ограниченное окно:

```text
REGION_TALK_YDB_READONLY_CREDENTIAL
```

Endpoint/database уже зафиксированы в versioned migration contract. После подтверждённого export credential удаляется.

## Не требуется от владельца

- sealed-box key pair;
- Kaggle User Secret для первого запуска;
- Supabase direct PostgreSQL connection;
- отдельные names для datasets/kernels;
- model revision variables;
- target channel numeric ID;
- новый Supabase account/project;
- новый Telegram bot.

## Решения, которые останутся позднее

- выбрать exact candidate для первого private-channel и production canary;
- отдельно решить, включать ли VK;
- после первого полного прогона решить, нужен ли compact Supabase operator projection;
- включить `REGION_TALK_ORCHESTRATOR_ENABLED=1` только после ручного полного цикла и анализа метрик.

Secret values не публикуются в issue, PR, обычном чате, logs или artifacts.
