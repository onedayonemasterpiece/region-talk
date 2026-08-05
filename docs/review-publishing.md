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

The normalized payload SHA-256 is `operator_review_fingerprint`.

Any material change creates a new fingerprint, a new review revision and requires a fresh reaction. An old approval never transfers to regenerated copy or another image/order.

## 2. Review chat delivery

Notifier sends only a complete, current revision:

- article: one associated hero;
- social hero: one exact source image;
- social album: ordered 3–6 images;
- video: exact source video and manual visual review marker;
- link preview fallback: only after durable no-usable-media reason.

Delivery is idempotent by exact fingerprint. Failed media materialization blocks the revision rather than substituting another asset.

## 3. Reaction semantics

Only exact Telegram user IDs from `REGION_TALK_OPERATOR_REVIEWER_IDS` bind.

| Reaction | Meaning |
|---|---|
| `👍` or `❤️` | approve exact revision |
| `👎` | reject exact revision |
| `✍` | request rewrite; may coexist with a positive reaction but blocks publication until a new revision |
| positive + negative | conflict; manual resolution required |
| unknown reaction or non-allowlisted reactor | audit only, no decision |

Reaction sync reads the complete per-reactor list, not aggregate counters. It rereads immediately before publication.

## 4. Operator commands

The Telegram operator bot should expose:

- `/region_health` — active stage, latest state, stale/backlog warnings;
- `/region_queue [limit]` — approved/pending/rewrite/rejected counts and next slots;
- `/region_candidate <id|url>` — full decision evidence, scores, draft, media manifest and history;
- `/region_plan [days]` — publication plan with diversity explanations;
- `/region_runs [limit]` — recent runs and failures;
- `/region_pause` / `/region_resume` — controller gate, allowlisted users only;
- `/region_retry <run|candidate>` — creates audited request, never direct hidden mutation;
- `/region_publish_canary <candidate>` — protected environment/manual approval only.

Compact queue data comes from Supabase operator projection. Deep evidence links to current private GitHub report/Kaggle run archive.

## 5. Publication planning

Default preserved policy:

- up to one external article slot per day;
- up to one Telegram/VK social slot per day;
- Telegram and VK, when VK is enabled, represent the same selected content pair rather than independent duplicate slots;
- only approved, current, media-materialized revisions can occupy slots;
- future unlocked slots are recalculated after every committed discovery/review cycle.

Diversity constraints are first-class:

- no adjacent duplicate source unless explicit override;
- bounded repeated topic/place/media mode;
- article/social balance;
- minimum thematic/visual distance from recent publications;
- stale candidate expiration;
- no scheduling conflict with already published canonical URL/candidate.

Planner stores both selection and rejected alternatives with reason codes so the choice is explainable.

## 6. Publication outbox

Outbox state:

```text
planned → due → prepared → sending → published
                         ↘ retry_wait
                         ↘ failed_terminal
                         ↘ cancelled
```

Before sending:

1. load exact current revision;
2. verify approval and no rewrite/conflict;
3. exact reaction reread;
4. verify scheduled slot and diversity plan version;
5. reacquire media and verify reviewed SHA where available;
6. reserve idempotency key;
7. record `prepared` transaction.

Telegram idempotency key:

```text
region-talk:<candidate_id>:<operator_review_fingerprint>:telegram
```

After API result, record platform message ID/URL and exact rendered payload. On ambiguous timeout, inspect target history before retry. Never blindly duplicate.

## 7. Target publishing rollout

1. publisher disabled;
2. render-only and exact-media dry run;
3. private test channel canary;
4. retry/timeout/duplicate fault tests;
5. one owner-approved production candidate;
6. bounded observation;
7. enable ordinary approved-slot publishing.

VK remains disabled until its separate media upload/token canary passes. Telegram target defaults to `@kalinigrad_visit`, but exact numeric target and bot/admin rights are deployment inputs.

## 8. Querying from ChatGPT

Reconciler exports sanitized current reports to the private repository `ops-current` branch. A connected GitHub session can therefore answer:

- what is running;
- latest failures;
- current candidate queue;
- publication plan;
- conversion and product metrics;
- pointer to exact run archives.

Full private source text/media remains in the controlled state/archive and is not copied into the report unless explicitly safe.
