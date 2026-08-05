# Одноразовая миграция YDB → SQLite/Kaggle

## 1. Общий принцип

YDB используется только как read-only источник первого канонического снимка и как временный rollback. Миграция не должна включать рабочий dual-write и не должна снова запускать автономные широкие чтения.

## 2. Preconditions

- явное operator approval на миграционное окно;
- exact expected YDB database identity;
- временный read-only service account/OIDC identity;
- минимальный bounded RU throttle только на время export;
- Region Talk scheduler и watchdog остаются выключенными;
- никакой другой writer не меняет YDB в окне export;
- отдельный GitHub protected environment `region-talk-ydb-migration`;
- все export commands имеют hard query/row/byte/time budgets.

## 3. Export package

Каждая таблица экспортируется один раз с детерминированным порядком:

```text
ydb-export/
  export-manifest.json
  tables/<table>.jsonl.zst
  tables/<table>.ordered.sha256
  tables/<table>.row-count
  schema/<table>.json
  source-database-attestation.json
```

Manifest фиксирует:

- cloud/folder/database IDs;
- export timestamp window;
- table path;
- exact schema;
- row count;
- compressed/uncompressed bytes;
- ordered SHA-256;
- export tool Git SHA;
- RU/client-budget telemetry;
- service identity (non-secret ID only).

No secret or credential is included.

## 4. SQLite mapping

Legacy compact `kind/pk/payload_json` rows are decoded through versioned importers. Mapping is explicit and tested by kind:

- sources/source queue/state;
- processed posts and post links;
- candidate memory;
- E5/BGE vector evidence;
- image queue/frame decisions;
- publication candidates/drafts;
- source onboarding evidence/profile;
- external research intake/identity ledger;
- operator review/delivery/publication ledger;
- run metrics and provider request receipts.

Unknown kinds are never discarded. They enter `legacy_unmapped_rows` with exact PK, kind, payload hash, export table and migration warning.

## 5. Validation

Before publishing state version 1:

1. all YDB rows are accounted for as mapped or explicitly unmapped;
2. source table row counts match export manifest;
3. ordered export hashes match source receipts;
4. stable identity counts are reported for source/post/candidate/publication;
5. duplicate canonical URL/DOI/title-author identities are classified, not silently merged;
6. all external research request IDs and SHA attestations survive;
7. operator review fingerprints/message IDs survive;
8. publication logs and target message IDs survive;
9. E5/BGE rows retain exact model/text/policy versions;
10. `PRAGMA integrity_check` returns `ok`;
11. `PRAGMA foreign_key_check` returns no rows;
12. a deterministic SQLite logical export has a recorded SHA-256;
13. state version 1 can be downloaded, opened and queried in a clean environment.

## 6. Shadow comparison

For at least three representative cycles:

- use the same frozen input data;
- run current YDB implementation read-only/dry and new SQLite implementation;
- compare selected work, decisions, rejection reasons, vector pair coverage, image queue, final candidates and operator revisions;
- explain every mismatch;
- prohibit production publication from the new backend.

Allowed differences: storage layout and newly corrected bugs. Unexplained candidate disappearance or readiness promotion is a cutover blocker.

## 7. Cutover

1. Freeze YDB state.
2. Produce final export and SQLite state version.
3. Switch launchers to `REGION_TALK_STATE_BACKEND=kaggle_sqlite`.
4. Remove YDB credentials from normal GitHub/Kaggle environments.
5. Run full CPU pipeline.
6. Analyze results using `docs/first-full-run.md`.
7. Run private-channel publication canary.
8. Observe at least seven days or a sufficient number of complete cycles.

YDB remains at zero/disabled capacity for the rollback window. Deletion is a separate explicit owner decision after final archive/readback proof.

## 8. Credential disposal

After migration:

- revoke/delete temporary read-only identity;
- remove migration secret from GitHub environment;
- ensure Kaggle never received YDB credentials;
- record revocation and failed-auth verification;
- retain no decrypted export in Actions scratch or runner cache;
- keep only encrypted/private export archive with checksums.
