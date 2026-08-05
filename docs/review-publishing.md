# Telegram review, queue and publication

## 1. Exact revision identity

Operator review is bound to:

```text
candidate identity
+ two editorial paragraphs
+ source-aware CTA and exact original URL
+ channel footer
+ ordered media manifest
+ layout/presentation mode
+ Writer/policy versions
```

Normalized SHA-256 is `operator_review_fingerprint`. Any material change creates a new revision and requires fresh reactions.

## 2. Review chat delivery

Notifier sends only a complete current revision:

- article: one associated hero;
- social hero: one exact source image;
- social album: ordered 3–6 images;
- video: exact source video plus manual-review marker;
- link-preview fallback: only after durable no-usable-media reason.

Delivery is idempotent by exact fingerprint. Failed media materialization blocks the revision rather than silently substituting an asset.

## 3. Reaction semantics

Only exact Telegram user IDs from `REGION_TALK_OPERATOR_REVIEWER_IDS` bind.

| Reaction | Meaning |
|---|---|
| `👍` or `❤️` | approve exact revision |
| `👎` | reject exact revision |
| `✍` | rewrite requested; blocks publication until a new revision |
| positive + negative | conflict; manual resolution required |
| unknown/non-allowlisted | audit only |

Reaction sync reads complete per-reactor evidence, not aggregate counts, and rereads immediately before publication.

## 4. Operator commands

- `/region_health` — active stage, latest state, stale/backlog warnings;
- `/region_queue [limit]` — approved/pending/rewrite/rejected counts and slots;
- `/region_candidate <id|url>` — evidence, scores, draft, media and history;
- `/region_plan [days]` — plan with diversity explanations;
- `/region_runs [limit]` — recent runs/failures;
- `/region_pause` / `/region_resume` — allowlisted controller gate;
- `/region_retry <run|candidate>` — audited request;
- `/region_publish_canary <candidate>` — exact canary request only.

Первая версия читает compact current report, сформированный из canonical SQLite/Kaggle state. Supabase operator projection не обязателен. Его можно добавить позже как cache, если latency команд окажется неприемлемой.

## 5. Publication planning

Default policy:

- до одной external article позиции в день;
- до одной social позиции в день;
- Telegram и VK, если VK включён, используют один content pair;
- только approved/current/media-materialized revisions занимают slots;
- future unlocked slots пересчитываются после committed discovery/review cycle.

Diversity constraints:

- no adjacent duplicate source без override;
- bounded repeated topic/place/media mode;
- article/social balance;
- thematic/visual distance from recent publications;
- stale candidate expiration;
- no canonical URL/candidate duplication.

Planner хранит selection и отклонённые alternatives с reason codes.

## 6. Publication outbox

```text
planned → due → prepared → sending → published
                         ↘ retry_wait
                         ↘ failed_terminal
                         ↘ cancelled
```

Перед отправкой:

1. load exact current revision;
2. verify approval and no rewrite/conflict;
3. exact reaction reread;
4. verify slot/diversity plan version;
5. reacquire media and verify reviewed hashes/order;
6. reserve idempotency key;
7. record `prepared` transaction.

```text
region-talk:<candidate_id>:<operator_review_fingerprint>:telegram
```

При ambiguous timeout сначала проверить target history; не отправлять вслепую повторно.

## 7. Target identity и rollout

Target username закреплён как `@kalinigrad_visit`. Numeric ID не вводится вручную: bot preflight разрешает username, проверяет ожидаемый title/username/admin rights и сохраняет подтверждённую identity в canonical state. Identity drift блокирует публикацию.

Rollout:

1. publisher gate `0`;
2. render-only/exact-media dry run;
3. private test-channel canary;
4. retry/timeout/duplicate fault tests;
5. один явно выбранный production candidate;
6. bounded observation;
7. ordinary approved-slot publishing.

Платный GitHub required-reviewer rule не обязателен: application gate требует exact approved revision, explicit canary request и publisher feature flag. VK остаётся выключенным до отдельного canary.

## 8. Querying from ChatGPT

Reconciler экспортирует sanitized current reports в private repository. Через connected GitHub можно запросить health, failures, queue, plan, conversion metrics и locators exact run archives. Full private source/media остаются в controlled state/archive.
