# Методика тестирования и отладки

## 1. Testing pyramid

### 1.1. Deterministic unit tests

Mandatory coverage:

- stable IDs and canonical URL normalization;
- SQLite migrations from empty and every previous schema version;
- typed delta application;
- exact replay no-op;
- same delta ID/different hash conflict;
- stale base rejection;
- allowed and forbidden state transitions;
- work priority and due ordering;
- E5/BGE fingerprint compatibility;
- source/post/candidate dedupe;
- exact review fingerprint;
- reaction classification;
- publication plan diversity;
- outbox idempotency;
- secret redaction.

### 1.2. Property and state-machine tests

Generate randomized sequences:

- crash before/after each commit boundary;
- duplicate controller ticks;
- out-of-order stage completion;
- repeated research package;
- concurrent reaction changes;
- provider success followed by local crash;
- publication timeout with/without actual platform post;
- compaction followed by replay.

Invariant: no accepted sequence may lose a committed entity, skip a required gate, publish an unapproved revision or create two state heads.

### 1.3. Golden data tests

Maintain frozen corpora:

- source local/external/spam classification;
- KO-only versus multi-region/ambiguous locality;
- news/ad/tour/announcement hard negatives;
- E5/BGE accepted/rejected pairs;
- media albums with complete/partial/weak/unsafe outcomes;
- source-profile evidence and contradictions;
- editorial good/rewrite/reject examples;
- publication schedule/diversity cases.

Every model/prompt/policy update produces a before/after decision diff. Unexplained regressions block release.

## 2. Stage integration tests

Each worker has a clean-room CPU test:

1. download a pinned private fixture dataset;
2. verify input SHA;
3. run with network/provider stubs where possible;
4. produce the exact run bundle;
5. validate delta and manifests;
6. prove no state dataset write from worker;
7. prove `enable_gpu=false`;
8. scan output for secrets;
9. apply delta in a temporary SQLite state;
10. verify expected decision/output counts.

Separate mandatory smokes:

- E5 loads and unloads without BGE present;
- BGE loads and unloads without E5 model present;
- ImageDiagnostic uses its distinct auth scope;
- finalizer uses shared limiter and no local fallback;
- reaction sync reads exact reactor pages;
- publisher renders exact reviewed media.

## 3. End-to-end scenarios

### E2E-01 Fresh social post

source discovery → exact post → E5 → BGE → fusion → image → source profile → Writer → review message → 👍 → schedule → private-channel publish.

### E2E-02 External article from research JSON

committed JSON → all-or-nothing import → exact article → publisher profile → vectors → article hero → Writer → review → schedule.

### E2E-03 Rewrite

current revision → ✍ → terminal rewrite request → new Writer fingerprint → new review message → old approval ignored.

### E2E-04 Rejection

👎 → terminal rejection → candidate absent from all future slots → retained audit.

### E2E-05 Conflicting reactions

👍 + 👎 → conflict → no publish → operator report explains reviewer/reaction set.

### E2E-06 Media drift

reviewed media hash changes before publish → publish blocked → visual re-review revision.

### E2E-07 Missed cron

skip several controller ticks → next tick reconciles active terminal kernel and continues without duplicate launch.

### E2E-08 Stale Kaggle output

new state commits before old kernel returns → old delta rejected as stale; work is re-planned from current state.

### E2E-09 Supabase outage

active kernel may finish; no new provider/publication launch; output remains downloadable and reconciles after recovery.

### E2E-10 Kaggle outage

controller marks degraded, does not spin launches, local reaction/publication safety work continues only when it does not require unavailable evidence.

## 4. Fault injection matrix

| Fault | Expected result |
|---|---|
| truncated output | no reconciliation; diagnostic archive retained |
| missing `stage-result.json` | classified output_missing |
| checksum mismatch | hard fail, no state write |
| secret pattern in log | quarantine, no artifact/state publish |
| invalid JSONL halfway | no partial delta |
| SQLite disk/full error | previous state head remains current |
| Kaggle state upload succeeds but readback fails | candidate state not advertised; recovery probes exact version |
| Supabase projection fails after state commit | repair projection next tick; no duplicate state commit |
| duplicate controller | one lease owner, other exits cleanly |
| provider 429 | shared scope cooldown; no sibling key in same scope retry |
| Telegram flood wait | bounded retry/defer, no session parallelism |
| reaction removed during sync | reread exact message state; no stale approval |
| publish timeout | inspect target history before retry |
| schedule policy changes | locked published slot unchanged; future unlocked slots replan |

## 5. Debugging workflow

### 5.1. Symptom-first triage

1. Select time window and user-visible symptom.
2. Resolve current state version and relevant candidate/source IDs.
3. Read current health/queue reports.
4. Locate stage attempts and run archive versions.
5. Compare structured events before raw stdout.
6. Reconstruct input/delta/output hashes.
7. Determine whether failure is acquisition, vector, policy, media, Writer, review, schedule, transport or projection.
8. Reproduce against a downloaded exact state version in read-only mode.
9. Produce root cause, blast radius, repair and regression fixture.

### 5.2. Required incident evidence

- exact Git SHA and policy/model versions;
- state version before/after;
- run and stage IDs;
- input/delta/archive SHA;
- last successful heartbeat and resource sample;
- reason codes and affected entity IDs;
- provider request fingerprints without secrets;
- queue/product metric impact;
- evidence that repair did not bypass editorial/review gates.

### 5.3. No “green but useless” runs

A technically complete run is product-failed when it produces zero advancement and has no valid `zero_progress_reason`. Allowed reasons include:

- no fresh eligible content;
- all work waiting for BGE;
- all work waiting for visual evidence;
- shared provider budget exhausted;
- explicit operator pause;
- upstream platform unavailable;
- policy rejected all evaluated rows.

Every zero-progress result reports evaluated counts, dominant reasons and next recoverable action.

## 6. Shadow and canary gates

### Backend cutover

- minimum three complete shadow cycles;
- matching candidate identities/reasons or reviewed explanations;
- no missing active queue population;
- no unexplained publication readiness increase;
- state and history readback successful.

### Editorial change

- full golden/adversarial corpus;
- fact fidelity 100% on required facts;
- no new hard failures;
- blind human review of changed/representative outputs;
- limited review-chat shadow before replacement.

### Publisher

- private target only;
- exact media and caption verification;
- forced timeout/retry test;
- duplicate-history check;
- explicit owner approval for first production canary.
