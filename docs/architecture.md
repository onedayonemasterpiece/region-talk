# Целевая архитектура Region Talk

## 1. Критерий архитектурного выбора

Region Talk — пакетный discovery/editorial pipeline с низкой целевой скоростью публикации и высокой стоимостью ошибки. Ему нужны:

- долговечное и воспроизводимое состояние;
- независимые CPU-стадии;
- идемпотентность;
- полная наблюдаемость;
- точное операторское согласование;
- управляемая публикация;
- минимальные регулярные расходы.

Ему не требуется постоянно доступная распределённая OLTP-БД для тысяч параллельных пользовательских запросов. Поэтому транзакционная граница переносится внутрь SQLite, а межпроцессная координация — в один сериализованный reconciler.

## 2. Data ownership

### 2.1. GitHub repository

Хранит:

- reviewed source code;
- SQLite/Supabase migrations;
- JSON Schemas;
- prompts и editorial policies;
- golden/adversarial fixtures;
- immutable external-research JSON;
- small current reports и history summaries;
- workflow definitions;
- audit receipts без секретов.

Не хранит:

- `state.sqlite`;
- сырые media bytes;
- Telegram sessions;
- provider keys;
- необрезанные run logs;
- временные Kaggle input bundles.

### 2.2. Private Kaggle state dataset

Одна версия канонического state dataset содержит:

```text
state.sqlite.zst
state.sqlite.sha256
manifest.json
queue-summary.json
product-metrics.json
candidate-export.jsonl
schema-version.txt
```

`manifest.json` обязан указывать:

- dataset version;
- previous version;
- base and result SHA-256;
- Git SHA;
- SQLite schema version;
- applied delta IDs and hashes;
- run IDs;
- invariant results;
- created timestamp;
- reconciler workflow/run identity.

### 2.3. Private Kaggle run-history dataset

Каждая version содержит один immutable run bundle и небольшой cumulative index pointer:

```text
runs/<run_id>/run-bundle.tar.zst
runs/<run_id>/run-bundle.sha256
runs/<run_id>/manifest.json
latest-run-index.json
```

Предыдущие версии адресуются по точному version number. Ссылка на версию и SHA сохраняется в `state.sqlite.runs`.

### 2.4. Supabase

Используется в двух строго ограниченных ролях:

1. существующий общий atomic Google AI limiter;
2. компактная схема `region_talk_control` для orchestration lease, stage attempt и operator projection.

Supabase не является source of truth для discovery state. При временной недоступности control-plane controller не запускает новые provider/publication действия, но история не теряется.

### 2.5. GitHub Actions reconciler

Единственный компонент, который имеет право:

- признать Kaggle output действительным;
- применить delta к SQLite;
- создать новую canonical state version;
- обновить Supabase operator projection;
- обновить `ops-current` reports;
- подтвердить publication outcome.

Kaggle workers никогда не публикуют state dataset version самостоятельно.

## 3. Worker topology

| Stage | Runtime | Local model | Telegram role | Output |
|---|---|---|---|---|
| `research_import` | GitHub CPU | none | none | SQLite delta |
| `candidate_e5` | Kaggle CPU | multilingual-e5-base | DISCOVERY1 | discovery/E5 delta |
| `bge_enrichment` | Kaggle CPU | BGE-M3 | none | BGE delta |
| `fusion` | Kaggle CPU or short GitHub CPU | none/new vectors only | none | fusion delta |
| `image_diagnostic` | Kaggle CPU | CPU image stack | DISCOVERY2 | media delta |
| `source_profile_capture` | Kaggle CPU | none | role-scoped | evidence delta |
| `finalizer_writer` | short GitHub CPU by default | remote Google model through limiter | none | exact draft delta |
| `operator_notify` | GitHub CPU | none | bot/role-scoped | delivery delta |
| `reaction_sync` | GitHub CPU | none | DISCOVERY2 or dedicated review role | review delta |
| `schedule_plan` | GitHub CPU | none | none | schedule delta |
| `publisher` | GitHub CPU | none | bot/MTProto publisher role | publication delta |

Every Kaggle `kernel-metadata.json` must set `enable_gpu=false`. A GPU-enabled run is an automatic release failure.

## 4. Delta protocol

Worker input:

```json
{
  "run_id": "rt-20260804T080000Z-candidate-e5-01",
  "stage": "candidate_e5",
  "base_state_dataset": "owner/region-talk-state",
  "base_state_version": 17,
  "base_state_sha256": "...",
  "git_sha": "...",
  "policy_versions": {},
  "work_items": [],
  "budgets": {}
}
```

Worker output:

```json
{
  "schema_version": "region-talk-stage-result-v1",
  "run_id": "...",
  "stage": "candidate_e5",
  "base_state_version": 17,
  "base_state_sha256": "...",
  "delta_id": "sha256:...",
  "delta_sha256": "...",
  "status": "complete",
  "counts": {},
  "metrics": {},
  "artifacts": {},
  "secret_scan": {"status": "pass"}
}
```

Delta operations are declarative:

- `insert_if_absent`;
- `upsert_if_revision_matches`;
- `transition_if_status_in`;
- `append_event_if_absent`;
- `delete_only_with_tombstone`.

Arbitrary SQL supplied by a worker is forbidden.

## 5. Reconciliation transaction

1. Resolve exact current state version and SHA.
2. Reject output when base version/SHA does not match.
3. Verify output file allowlist, sizes, checksums and schemas.
4. Run secret redaction scanner.
5. Decompress state into private workflow scratch.
6. Open SQLite with foreign keys enabled.
7. `BEGIN IMMEDIATE`.
8. Reserve `delta_id`; exact replay becomes no-op, hash conflict aborts.
9. Apply typed operations in deterministic order.
10. Validate status transitions, identity uniqueness, queue invariants and publication safety.
11. Write run, stage and product metric records.
12. Commit transaction.
13. Run `PRAGMA integrity_check` and `PRAGMA foreign_key_check`.
14. Create a clean copy through backup API or `VACUUM INTO`.
15. Hash and publish the next Kaggle state dataset version.
16. Read back exact files and hashes.
17. Only after readback update Supabase projections and current GitHub reports.

Failure before state-version readback leaves the previous HEAD authoritative.

## 6. Why separate E5 and BGE remains mandatory

The architecture treats the model split as a production invariant, not a tuning preference:

- Candidate stage loads only E5;
- BGE worker reads only rows with a current E5/text fingerprint and missing current BGE;
- fusion requires matching `post_id`, `text_hash`, model revision and semantic-bank version;
- stale vectors are not fused;
- BGE maintenance rows never starve fresh missing pairs;
- no notebook may load E5 and BGE concurrently in production.

A CI policy test scans kernels/config and rejects any production stage whose model list contains both model families.

## 7. Availability model

The system is asynchronous and catch-up based:

- no stage assumes exact cron delivery;
- no scheduled tick is considered state;
- every controller run reconstructs the next action from durable records;
- active kernels can outlive several controller ticks;
- a missed or delayed tick increases latency but does not lose work;
- after failure, the next tick resumes from the last committed state version;
- external calls use request fingerprints and bounded retries.

This provides near-continuous progress without a permanently running paid process.
