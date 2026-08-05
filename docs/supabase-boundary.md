# Supabase boundary

## Decision

Use the **existing dedicated Supabase project that already owns the shared Google AI limiter**. Do not create a new account to distribute free-tier limits and do not create a second independent limiter.

A separate account/project would create:

- a split-brain quota ledger;
- additional secrets and migrations;
- harder incident reconciliation;
- risk that parallel consumers believe they have independent quota when they share one Google Cloud scope;
- extra inactive-project lifecycle risk.

A second Supabase project is justified only by a later explicit blast-radius/security decision. It must still call the one canonical limiter rather than copy it.

## Allowed Region Talk schema

Schema: `region_talk_control`.

Allowed tables are deliberately small:

- `controller_state` — one row;
- `stage_attempts` — bounded operational attempts;
- `operator_queue` — current active/recent projection, capped;
- `operator_review_events` — compact exact review events;
- `publication_outbox` — active/recent delivery projection;
- `state_head` — current dataset version/SHA pointer;
- `control_audit` — compact operator/controller events.

Not allowed:

- full discovery/source/post state;
- vectors;
- raw logs;
- media;
- entire article/post texts;
- source archives;
- run bundles;
- prompt corpora;
- historical state snapshots.

## Write discipline

- Upsert only materially changed rows.
- RPCs return compact JSON and no unneeded columns.
- Writes use minimal/no representation responses.
- Active operator queue is capped at 200 rows.
- Completed stage attempts older than the configured hot window are compacted to SQLite/Kaggle and deleted from Supabase.
- Review/outbox rows are projected into SQLite before remote retention cleanup.
- No `select *` in runtime code.
- Each RPC records returned row/byte estimates in the controller log.
- Monthly application budget: configurable hard ceiling for calls, rows and response bytes; breach pauses non-critical work.

## Why this is compatible with a small egress allowance

Normal controller tick should require one compact RPC response. Candidate details are fetched only when the operator requests them. Full analysis reads Kaggle/SQLite, not Supabase. Google limiter records remain the dominant Supabase traffic and are already required for safe provider coordination.

Target Region Talk control-plane budget:

- ordinary idle tick response: under 10 KiB;
- active tick response: under 50 KiB;
- current queue projection: under 2 MiB total;
- no media or run logs;
- less than 100 MiB/month application-side target, with an alert at 50% and hard pause before the configured ceiling.

These are engineering budgets to verify, not provider guarantees.

## Access model

- Kaggle receives the dedicated limiter URL/key only for Google provider calls.
- Kaggle does **not** receive direct Region Talk control-table credentials.
- GitHub Actions owns control-plane RPC calls and state projection.
- Telegram operator bot/publisher runs through GitHub Actions or a separately approved small runtime and uses RPCs, not table-wide reads.
- All public/publish actions fail closed when exact current revision/state cannot be read.

## Failure behavior

| Failure | Behavior |
|---|---|
| limiter unavailable | no Google provider call |
| control schema unavailable | no new kernel/publication launch; active Kaggle run may finish and await reconciliation |
| projection update fails after state commit | state remains canonical; next tick repairs projection |
| stale controller lease | compare-and-set takeover after expiry and audit event |
| queue projection incomplete | operator commands report degraded; no publication |
