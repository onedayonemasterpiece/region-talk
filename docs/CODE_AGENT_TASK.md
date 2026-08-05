# Задача кодовому агенту: довести Region Talk до первого полного CPU-прогона

Репозиторий: `onedayonemasterpiece/region-talk`.

## Цель

Не перепроектировать Region Talk, а перенести доказанную реализацию из `events-bot-new` на новый backend:

```text
private Kaggle CPU workers
→ immutable deltas/logs
→ GitHub Actions reconciler
→ versioned SQLite state in private Kaggle Dataset
→ Telegram review queue
```

## Обязательные инварианты

- Candidate/E5 и BGE-M3 — отдельные CPU kernels.
- Workers не меняют canonical state напрямую.
- Один GitHub reconciler применяет delta к exact base version.
- Existing Supabase Google AI limiter остаётся единственным limiter; local fallback запрещён.
- Scheduler и publisher выключены до полного ручного run и анализа.
- Review bind — exact text + source URL + ordered media fingerprint.
- Все Kaggle assets private; output проходит secret scan.

## 1. Переиспользовать текущую реализацию

Перенести с provenance только необходимые Region Talk code/tests/docs из `events-bot-new`:

- CandidateReport/E5 launcher и worker;
- отдельный BGE-M3 worker;
- ImageDiagnostic;
- source-profile capture;
- finalizer/Writer;
- notifier/reaction sync/planner/publisher;
- research importer;
- focused Region Talk tests/fixtures;
- нужный `google_ai` limiter client.

Не переносить `.env`, sessions, DB files, artifacts или unrelated bot runtime.

## 2. Kaggle authentication и runtime secrets

Поддержать один из вариантов:

```text
KAGGLE_API_TOKEN
```

или существующий:

```text
KAGGLE_USERNAME + KAGGLE_KEY
```

Не требовать новый token, если legacy API smoke проходит.

Переиспользовать действующий private ephemeral dataset transport из `events-bot-new`:

- unique dataset per stage/run;
- минимальный stage-scoped secret allowlist;
- Fernet payload/key в одной private version;
- delete after terminal run + TTL GC;
- BGE получает zero external secrets;
- output secret scan.

Не вводить sealed-box key pair или обязательный Kaggle User Secret.

Dataset/kernel refs выводить из `KAGGLE_USERNAME`; exact model revisions закрепить в repository config.

## 3. SQLite state и reconciler

Реализовать:

- load exact state version/SHA;
- immutable worker delta schemas;
- `BEGIN IMMEDIATE` apply;
- exact replay = zero writes;
- stale base = zero writes;
- invariants + `integrity_check` + `foreign_key_check`;
- clean SQLite snapshot;
- private Kaggle Dataset version upload/readback;
- complete run bundle archive и locators в state.

GitHub Actions concurrency обеспечивает одного controller/reconciler. Новая Supabase control schema в первой версии не нужна.

## 4. Research intake

После merge файла:

```text
research/intake/region-talk-external-research-result-*.json
```

GitHub reconciler должен:

- проверить schema/semantics/exact SHA;
- применить all-or-nothing identity import в SQLite;
- exact replay сделать no-op;
- conflict записать как blocked без частичного импорта;
- отправить retained candidates в обычный E5 → BGE → image/profile → finalizer funnel;
- не выдавать publication permission.

## 5. Одноразовая YDB migration

- endpoint/database взять из versioned migration contract;
- использовать один temporary read-only credential в `region-talk-migration`;
- bounded ordered export;
- row counts и hashes;
- explicit kind mapping в SQLite;
- unmapped rows сохранить;
- три shadow comparison;
- credential удалить после export;
- YDB не удалять без отдельного решения владельца.

## 6. Review и публикация

Переиспользовать существующий `TELEGRAM_BOT_TOKEN`, reviewer IDs и `@kalinigrad_visit`.

Не требовать вручную target numeric ID: разрешить его по username, проверить identity и сохранить в state.

Сохранить реакции:

```text
👍/❤️ approve
👎 reject
✍ rewrite
positive + negative = conflict
```

Publisher: outbox, exact current approval, schedule/diversity, exact media hashes, ambiguous-timeout readback и idempotency key. Сначала private-channel canary; production gate остаётся `0`.

## 7. Первый полный прогон

Последовательность:

1. authenticated Kaggle read-only smoke;
2. state/reconciler fixture cycle;
3. отдельные Candidate/E5 и BGE CPU smoke runs;
4. Image/Profile smoke;
5. YDB migration dry/apply/readback;
6. полный ручной funnel до review candidate;
7. скачать и проанализировать все run bundles;
8. посчитать product funnel из `docs/product-metrics.md`;
9. исправить P0/P1 и добавить regressions;
10. только после этого предложить включение регулярного controller.

## Внешние значения, которые нельзя выдумывать

Сейчас:

```text
KAGGLE_KEY или KAGGLE_API_TOKEN
```

Позже для review:

```text
TELEGRAM_BOT_TOKEN
REGION_TALK_REVIEW_CHAT_ID
```

Только для migration:

```text
REGION_TALK_YDB_READONLY_CREDENTIAL
```

Все остальные asset names/IDs/revisions должны быть выведены или закреплены в коде.

## Результат

Вернуть branch/PR, commits, tests, workflow/Kaggle run IDs, state versions/hashes, migration reconciliation, первый product-funnel report и точный список оставшихся блокеров. Не включать scheduler/publisher автоматически.
