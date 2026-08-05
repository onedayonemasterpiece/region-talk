# Задача кодовому агенту: автономный Region Talk на private GitHub + Kaggle/SQLite

## Цель

Развернуть в `onedayonemasterpiece/region-talk` автономный CPU-only Region Talk с отдельными E5/BGE/Image стадиями, каноническим SQLite state в private Kaggle Dataset, коротким GitHub Actions orchestrator/reconciler, полными логами, компактным Supabase control-plane, Telegram review reactions, publication planning и безопасным publisher.

## Неподлежащие ослаблению требования

- Не публиковать и не передавать секреты в issue/PR/log/artifact/dataset.
- Сначала сделать GitHub repo private, затем выполнять любые push.
- Все Kaggle kernels/datasets private и CPU-only.
- E5 и BGE-M3 не загружаются в одном production kernel.
- Только GitHub reconciler меняет canonical state dataset.
- Existing dedicated Supabase Google limiter remains the single atomic limiter; no local fallback.
- No public target publishing until all migration/shadow/private-canary gates pass.
- Exact operator reaction binds exact text+URL+ordered-media revision.
- Preserve current Region Talk product/editorial semantics unless a documented migration test proves an intentional change.

## Phase 0 — privacy and repository bootstrap

1. Change `onedayonemasterpiece/region-talk` visibility from public to private.
2. Verify via API/CLI that `visibility=private` before first source push.
3. Restrict Actions default `GITHUB_TOKEN` to read-only; grant `contents:write` only to the generated-report workflow and only for `ops-current`/history branches.
4. Disable public forks where applicable and require environment approval for:
   - `region-talk-ydb-migration`;
   - `region-talk-production-publish`.
5. Commit this bootstrap package to branch `agent/region-talk-kaggle-sqlite` and open a draft PR.
6. Do not copy source repository `.env`, artifacts, sessions or database files.

Acceptance: repository and PR are private; a public unauthenticated request cannot read them.

## Phase 1 — extract source implementation and documentation

Copy with provenance from `onedayonemasterpiece/events-bot-new` the Region Talk implementation required for behavior preservation. Prefer `git subtree/filter-repo` or scripted exact-copy with source commit receipt.

Minimum code families:

- `kaggle/RegionTalkCandidateReport/` and launcher;
- BGE-M3 worker/launcher;
- RegionTalkImageDiagnostic worker/launcher;
- `scripts/region_talk_orchestrator.py` as reference, not final state backend;
- publication finalizer/draft backfill;
- goal notifier;
- reaction sync;
- publication planner/publisher-related code;
- source profile capture/import/correction code;
- external publication importer/validator;
- shared `google_ai` client/limiter integration only as needed;
- all focused Region Talk tests and fixtures.

Minimum canonical docs to preserve under `docs/source-material/events-bot-new/` or convert with explicit provenance:

- `docs/features/region-talk-channel/README.md`;
- `orchestration-to-be.md`;
- `publication-queue.md`;
- `editorial-visual-product.md`;
- `source-onboarding-profile.md`;
- `source-profile-recovery-plan.md`;
- `telegram-vk-publishing.md`;
- `external-publications.md`;
- `external-publication-import-runbook.md`;
- `external-publication-research-results.md`;
- image-scoring audit/methodology docs referenced by Region Talk;
- Writer/onboarding prompts and consultation docs;
- relevant incident reports, especially YDB cost and stdout deadlock.

Static-site editorial materials:

- copy PR #286 files from `docs/editorial/`, including both research reports and synthesis;
- preserve source commit/PR in `docs/editorial/source-provenance.md`;
- do not silently turn unfinished research into policy; use the selected option B baseline in this package as v1 policy, with corpus gates.

Acceptance: source manifest lists every copied path, source commit SHA and destination SHA-256; no unrelated events-bot runtime is imported.

## Phase 2 — state/delta layer

1. Apply `sql/sqlite/0001_initial.sql` and add migrations rather than modifying it after first release.
2. Implement `RegionTalkStateStore` with:
   - exact state version/SHA load;
   - typed work query;
   - declarative delta apply;
   - replay/conflict guard;
   - deterministic state commit;
   - invariant and logical-export checks.
3. Implement schemas in `schemas/` and strict validation.
4. Convert worker writes to immutable deltas. Remove direct YDB/state-dataset writes from workers.
5. Implement one reconciler that applies a delta under `BEGIN IMMEDIATE`, produces a clean SQLite file, uploads a new private dataset version and independently reads it back.
6. Keep all legacy row kinds accounted for during migration; unknown kinds enter `legacy_unmapped_rows`.

Acceptance: exact replay writes zero rows; stale base writes nothing; crash at every commit boundary preserves one authoritative head.

## Phase 3 — Kaggle workers and secret delivery

1. Create/verify separate private CPU kernels:
   - Candidate/E5;
   - BGE-M3;
   - ImageDiagnostic;
   - source-profile capture if retained as separate worker.
2. Set `enable_gpu=false` and pin model revisions/dataset sources.
3. Add CI policy rejecting E5+BGE co-location in one production kernel.
4. Replace current secret bundle approach with sealed-box pattern:
   - GitHub repository variable contains public key;
   - Kaggle User Secret contains private key;
   - ephemeral private dataset contains ciphertext only;
   - no co-mounted decryption key from GitHub.
5. Before implementation, run an API-started Kaggle secret availability probe that returns only boolean capability, never a secret value.
6. If unavailable, stop and report the blocker; move sensitive stages to protected GitHub/runtime rather than weakening encryption.
7. Delete ephemeral input datasets after terminal output/readback; run TTL GC for leaked inputs.

Acceptance: secret leak scanner passes synthetic canaries; no run output/input contains a decryptable secret pair.

## Phase 4 — orchestrator and logs

1. Implement `.github/workflows/region-talk-control.yml` using schedule at minute offsets, manual dispatch and concurrency.
2. Controller jobs must be short: launch/status/reconcile and exit; no long sleep/poll.
3. Apply `sql/supabase/0001_region_talk_control.sql` to the existing limiter project under separate schema.
4. Implement compact RPC-only controller access and app-side request/row/byte budgets.
5. Implement complete run bundle from `docs/state-history-observability.md`.
6. After terminal Kaggle status:
   - download output;
   - verify schemas/checksums/redaction;
   - upload GitHub artifact with private retention 400 days;
   - publish private Kaggle run-history version;
   - store locators/SHA in SQLite.
7. Create `ops-current` branch and daily history summaries without raw secrets/content.
8. Add monthly random archive readback and quarterly portable backup job.

Acceptance: a deliberately failed kernel still produces a useful, secret-clean diagnostic archive; current reports are readable through GitHub connector.

## Phase 5 — YDB migration

1. Do not reuse deleted/old-account credentials.
2. Configure temporary read-only target YDB access in protected environment.
3. Keep scheduler/watchdog disabled and use a bounded export.
4. Export every relevant table with deterministic order, row count and SHA.
5. Import into SQLite using explicit kind mapping.
6. Produce migration reconciliation report, unmapped rows and exact identity counts.
7. Run three or more shadow comparisons.
8. Remove migration credential and return YDB to disabled/zero state after final export.
9. Do not delete YDB until owner separately approves after rollback window.

Acceptance: 100% source rows accounted for; SQLite state version 1 passes integrity/readback; no unexplained candidate/readiness mismatch.

## Phase 6 — research intake

1. Add PR validation for `research/intake/region-talk-external-research-result-*.json`.
2. Import only trusted `main` bytes through reconciler, not Kaggle.
3. Preserve all-or-nothing identity guard, exact replay and request/SHA conflict behavior.
4. Start all retained candidates as unreviewed/not-granted and route through normal gates.
5. Generate import receipt and product conversion metrics.

Acceptance: exact replay no-op; one invalid/conflicting row writes nothing; import has zero immediate publication effect.

## Phase 7 — review chat and operator surface

1. Port exact reaction behavior:
   - `👍/❤️` approve;
   - `👎` reject;
   - `✍` rewrite requested;
   - positive+negative conflict;
   - exact reviewer ID allowlist only.
2. Bind decision to exact revision fingerprint.
3. Add `/region_health`, `/region_queue`, `/region_candidate`, `/region_plan`, `/region_runs` commands.
4. Store only compact active projections in Supabase; full evidence stays in state/archive.
5. Regenerated copy/media creates a new review revision and fresh reactions.

Acceptance: stale approval and aggregate reaction count cannot authorize publication.

## Phase 8 — planner and publisher

1. Preserve default daily plan: one article + one social slot, diversity-aware.
2. Implement explainable alternatives/reason codes.
3. Implement outbox with exact idempotency key and ambiguous-timeout history check.
4. Verify exact media manifest/hash before send.
5. Run render-only, then private test-channel canary.
6. Keep production publisher disabled until owner approves one exact canary revision through protected environment.
7. VK remains disabled until separate token/media canary.

Acceptance: duplicate retry creates one target post; media drift blocks publish; rewrite/conflict blocks publish.

## Phase 9 — testing and first full run

1. Implement all categories in `docs/testing-debugging.md`.
2. Run full clean CPU pipeline from migrated state.
3. Collect every artifact in `docs/first-full-run.md`.
4. Produce a complete technical/product/efficiency analysis.
5. Fix P0/P1 issues and add regressions.
6. Repeat until acceptance criteria pass.
7. Report branch, PR, commits, workflow runs, Kaggle refs/versions, state versions and remaining blockers.

## Secrets and variables to configure

### GitHub secrets — required

- `KAGGLE_API_TOKEN`
- `GOOGLE_AI_LIMITER_SUPABASE_URL`
- `GOOGLE_AI_LIMITER_SUPABASE_SERVICE_KEY`
- exact active `GOOGLE_API_KEY*` set matching limiter registry
- `TG_API_ID`
- `TG_API_HASH`
- `TELEGRAM_AUTH_BUNDLE_DISCOVERY1`
- `TELEGRAM_AUTH_BUNDLE_DISCOVERY2`
- `REGION_TALK_TELEGRAM_BOT_TOKEN`
- `REGION_TALK_MANIFEST_HMAC_KEY` (generate once)
- `REGION_TALK_SUPABASE_DIRECT_CONNECTION_STRING` in migration environment only
- temporary YDB read credential/OIDC inputs in migration environment only
- VK tokens only if VK scope is explicitly enabled

### GitHub variables — required

- `KAGGLE_USERNAME`
- `REGION_TALK_STATE_DATASET`
- `REGION_TALK_RUN_HISTORY_DATASET`
- exact Candidate/E5, BGE, Image and profile kernel refs
- E5/BGE model refs and immutable revisions
- `REGION_TALK_REVIEW_CHAT_ID`
- `REGION_TALK_OPERATOR_REVIEWER_IDS`
- `REGION_TALK_TARGET_CHANNEL_ID`
- `REGION_TALK_TARGET_CHANNEL_USERNAME=kalinigrad_visit`
- `REGION_TALK_PUBLICATION_SLOTS_LOCAL`
- daily article/social slot counts
- `REGION_TALK_TIMEZONE=Europe/Kaliningrad`
- `REGION_TALK_SUPABASE_SCHEMA=region_talk_control`

### Kaggle User Secret — required before sensitive API-started runs

- `REGION_TALK_SEALED_BOX_PRIVATE_KEY`

GitHub variable:

- `REGION_TALK_SEALED_BOX_PUBLIC_KEY`

## Values the agent must not guess

- Kaggle username and ownership of private datasets/kernels;
- exact Google key → quota-scope registry;
- review chat numeric ID;
- allowlisted reviewer Telegram user IDs;
- target channel numeric ID and actual bot/admin permissions;
- publication local times if owner wants values different from defaults;
- whether VK is in first rollout;
- temporary YDB migration identity and approved RU window.

## Final deliverable

- private repository URL;
- draft PR URL and exact head SHA;
- privacy/settings evidence;
- secret/variable presence report with values redacted;
- migrated state version and hashes;
- workflow/Kaggle run IDs;
- full first-run analysis;
- current queue/health report paths;
- canary evidence;
- explicit list of remaining owner decisions.
