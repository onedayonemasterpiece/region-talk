# Безопасность и секреты

## 1. Gate zero: private everywhere

Before any source/data/secret is pushed:

- GitHub repository `onedayonemasterpiece/region-talk` is private;
- Actions default token permissions are read-only, elevated per workflow only;
- fork PR workflows cannot access environments/secrets;
- all Kaggle kernels and datasets are private;
- no public notebook/dataset is used as an input if it embeds project state;
- GitHub environment approvals guard migration and production publication.

The repository is currently known to be public and empty. Privacy conversion is the first code-agent action.

## 2. Secret inventory and placement

### 2.1. GitHub repository/environment secrets

Required for orchestration/runtime:

- `KAGGLE_API_TOKEN` — current Kaggle API token; never legacy plaintext file in repo.
- `GOOGLE_AI_LIMITER_SUPABASE_URL` — dedicated canonical limiter project URL.
- `GOOGLE_AI_LIMITER_SUPABASE_SERVICE_KEY` — server-side limiter credential.
- `GOOGLE_API_KEY`, `GOOGLE_API_KEY2` ... only the exact active registered key set; do not invent or silently omit a scope.
- `TG_API_ID`, `TG_API_HASH` — Telegram application credentials.
- `TELEGRAM_AUTH_BUNDLE_DISCOVERY1` — Candidate/E5 and exact source acquisition role.
- `TELEGRAM_AUTH_BUNDLE_DISCOVERY2` — Image/reaction role.
- `REGION_TALK_TELEGRAM_BOT_TOKEN` — review notifier/command/publisher bot when Bot API is used.
- `VK_SERVICE_TOKEN`, `VK_ACCESS_TOKEN` — only if VK read/publish scope is enabled.
- `REGION_TALK_MANIFEST_HMAC_KEY` — optional but recommended integrity attestation for control manifests; distinct from encryption keys.

Migration-only protected environment `region-talk-ydb-migration`:

- temporary read-only YDB credential or OIDC/WIF inputs;
- no credential is copied to normal runtime after migration.

Migration/schema administration protected environment:

- `REGION_TALK_SUPABASE_DIRECT_CONNECTION_STRING` or approved migration credential;
- removed/limited after applying migrations if not needed at runtime.

### 2.2. GitHub variables, not secrets

- `KAGGLE_USERNAME`;
- `REGION_TALK_STATE_DATASET`;
- `REGION_TALK_RUN_HISTORY_DATASET`;
- exact Kaggle kernel refs;
- E5/BGE model dataset refs and immutable revisions;
- `REGION_TALK_REVIEW_CHAT_ID`;
- `REGION_TALK_OPERATOR_REVIEWER_IDS` (may be a secret if the owner prefers);
- `REGION_TALK_TARGET_CHANNEL_ID` and username;
- publication slots/time zone and daily caps;
- Supabase schema name;
- feature gates.

### 2.3. Kaggle User Secrets

Preferred single long-lived Kaggle secret:

- `REGION_TALK_SEALED_BOX_PRIVATE_KEY`.

GitHub stores only the matching public key as a repository variable. For each run GitHub creates a short-lived private input dataset containing an authenticated sealed ciphertext. Kernel reads its private key through Kaggle User Secrets, decrypts in memory and deletes the plaintext immediately after process configuration.

Alternative, only after an API-started smoke proves availability: store the required Telegram/limiter/Google secrets directly in Kaggle User Secrets and stop shipping them through datasets.

## 3. Reject the cipher+key-together pattern

Encrypting secrets and attaching both ciphertext and decryption key to the same kernel/dataset boundary protects mainly against accidental casual viewing, not against compromise of the run or dataset sources. The new implementation must not create a bundle containing both components accessible through the same GitHub-generated input.

If Kaggle User Secrets cannot provide the private key to API-started kernels, stages requiring sensitive Telegram credentials remain blocked until one of these is implemented:

- a proven supported Kaggle secret path;
- a separate trusted secret broker with short-lived credentials;
- moving that stage to a protected GitHub/runtime environment.

Do not weaken the boundary by returning to plaintext or co-mounted key material.

## 4. Role separation

- DISCOVERY1: candidate/source text acquisition and profile capture only.
- DISCOVERY2: image acquisition and exact reaction observation only.
- Bot publisher: target send/commands only.
- BGE: no Telegram or publication credentials.
- Reconciler: Kaggle/state/Supabase control access, no unnecessary Telegram session.
- Migration: YDB read only, temporary.

Same Telegram session cannot be active in parallel. Every attempt declares `remote_telegram_auth_scope`; unknown scope conflicts fail closed.

## 5. Logging rules

Never log:

- env vars or full config;
- secret names together with values;
- Telegram session payloads/device metadata bundle;
- Authorization headers;
- Supabase service key;
- Google/VK/Kaggle tokens;
- signed/temporary URLs with query parameters;
- encrypted secret payload bytes;
- raw exception objects that include request headers.

Log safe metadata only:

- credential role/scope ID;
- key registry ID and quota scope, never key value;
- provider/model;
- request fingerprint;
- status/reason/duration/token counts;
- canonical URL without secret query parameters;
- hashed private identifiers.

## 6. Secret scan

Before output/archive/state publish scan for:

- exact HMAC fingerprints of all injected secrets;
- known prefixes (`AIza`, `sb_secret_`, JWT-like structures, Telegram session/base64 signatures, private key headers);
- environment key/value patterns;
- URL credentials/query tokens;
- accidental `.env`, `kaggle.json`, `.session`, `.pem`, `.key` files;
- high-entropy strings in suspicious contexts.

False positives are reviewed through a quarantine artifact inaccessible to ordinary jobs. A scan failure blocks all downstream publication.

## 7. Rotation and incident response

- invalidate the affected key/session immediately;
- pause orchestrator and publisher;
- identify all run/dataset/artifact versions that may contain it;
- delete/restrict accessible copies where platform permits;
- rotate Kaggle input datasets and sessions;
- audit provider usage and Telegram active sessions;
- add exact regression fingerprint/test;
- document incident and restore only after clean canary.
