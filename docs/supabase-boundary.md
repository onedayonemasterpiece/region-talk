# Supabase boundary

## Решение для первого рабочего контура

Использовать существующий Supabase project **только как canonical Google AI limiter**. Не создавать новый аккаунт, второй limiter или обязательную `region_talk_control` schema до первого полного прогона.

Обязательные существующие credentials:

```text
GOOGLE_AI_LIMITER_SUPABASE_URL
GOOGLE_AI_LIMITER_SUPABASE_SERVICE_KEY
```

`REGION_TALK_SUPABASE_DIRECT_CONNECTION_STRING` не является prerequisite и не должен находиться в обычных repository secrets.

## Почему новый control-plane сейчас лишний

Первую версию уже сериализуют:

- GitHub Actions `concurrency` — один controller/reconciler workflow;
- current state manifest — exact base version и SHA;
- SQLite transaction — атомарное применение delta;
- Kaggle Dataset version — durable state commit;
- GitHub Actions/Kaggle attempt IDs — состояние удалённых workers;
- Telegram exact revision fingerprint — review/publication state.

Дополнительный lease и дублирующая active queue в Supabase не дают необходимой функции, но добавляют schema migration, direct database credential, egress, retention и новый источник рассинхронизации.

## Источник истины

```text
product state/history     → private versioned SQLite/Kaggle Dataset
active workflow exclusion → GitHub Actions concurrency
worker status             → Kaggle API + durable attempt rows in SQLite
LLM quotas                → existing Supabase limiter
review decisions          → Telegram evidence + append-only SQLite events
publication outbox        → SQLite state
```

## Когда compact Supabase projection можно вернуть

Только если первый полный прогон докажет конкретную проблему, например:

- Telegram commands требуют ответа существенно быстрее, чем доступен state snapshot;
- controller status reads из Kaggle оказываются слишком дорогими или медленными;
- появляется независимый always-on runtime, которому нужен компактный hot view;
- GitHub concurrency недостаточно из-за второго реально необходимого controller.

Тогда допускается отдельная schema `region_talk_control` только с компактными таблицами:

```text
controller_state
state_head
active_attempts
operator_queue
operator_review_events
publication_outbox
control_audit
```

Она остаётся projection/cache, а не source of truth. Полные source/post/vector/media/log/state данные в Supabase запрещены.

## Egress discipline при возможном будущем включении

- materially changed upserts only;
- no `select *`;
- compact RPC responses;
- active queue cap;
- no media, vectors или run bundles;
- измерение request/response bytes;
- application-side monthly budget и fail-closed pause.

До отдельного принятия этой фазы SQL-файл control schema считается optional design artifact и не требует применения.
