# Состояние, история и наблюдаемость

## 1. Цель

Для любого кандидата, отказа, пропущенного запуска или публикации система должна отвечать:

- какие входные данные были доступны;
- какие версии кода, модели, prompt и policy использовались;
- какие стадии реально исполнились;
- что изменилось в состоянии;
- почему кандидат прошёл, был отложен или отклонён;
- сколько времени и provider calls потребовалось;
- какой текст и какой ordered media manifest видел оператор;
- кто и какой реакцией согласовал ревизию;
- что именно было опубликовано и с каким platform ID.

## 2. SQLite history model

Operational tables хранят текущую проекцию. Append-only history tables хранят решения:

- `runs`;
- `stage_attempts`;
- `state_commits`;
- `delta_receipts`;
- `candidate_decision_events`;
- `operator_review_events`;
- `publication_attempts`;
- `provider_request_receipts`;
- `product_metric_snapshots`;
- `policy_versions`;
- `research_import_receipts`.

Изменение current row без соответствующего event запрещено trigger/application invariant.

## 3. Run bundle

Каждый worker обязан создать `/kaggle/working/region-talk-run-bundle/`:

```text
run-manifest.json
stage-result.json
stdout.log
stderr.log
events.jsonl
resource-samples.jsonl
provider-usage.jsonl
input-summary.json
output-summary.json
delta.jsonl.zst
delta.sha256
candidate-diff.jsonl
metrics.json
exception.json               # only on failure
files.sha256
secret-scan.json
```

### 3.1. `events.jsonl`

Каждая строка — структурированное событие:

```json
{
  "schema_version": "region-talk-log-event-v1",
  "ts": "2026-08-04T08:03:01.123Z",
  "run_id": "...",
  "stage": "candidate_e5",
  "level": "INFO",
  "event": "post_vectorized",
  "entity_type": "post",
  "entity_id_hash": "...",
  "duration_ms": 321,
  "counters": {"vectors": 1},
  "reason_code": "current_e5_written",
  "message": "bounded human-readable explanation"
}
```

Prohibited fields:

- environment dump;
- authorization headers;
- raw tokens/sessions;
- signed URLs and query strings;
- full API responses containing credentials;
- unbounded post archives;
- private chat participant names when numeric/hash identity is sufficient.

### 3.2. Resource sampling

Every 30–60 seconds:

- RSS and peak RSS;
- CPU percent/time;
- disk free and output size;
- stage progress counters;
- network request counters by safe provider name;
- model load/unload timestamps;
- heartbeat age.

A stack watchdog writes sanitized stack names/locations, never locals or environment values.

## 4. Capturing Kaggle logs through GitHub Actions

After kernel terminal status, reconciler:

1. downloads exact kernel output version;
2. records Kaggle kernel ref, version and terminal metadata;
3. requires the complete run bundle allowlist;
4. verifies `files.sha256`;
5. runs JSON Schema validation;
6. scans all text and binary strings for known secret fingerprints and key patterns;
7. rejects archive and state commit on any secret hit;
8. uploads the verified bundle as a private GitHub Actions artifact;
9. publishes the same bundle as a version of the private Kaggle run-history dataset;
10. stores both locator sets and SHA-256 in SQLite;
11. samples a historical version periodically to prove it remains downloadable.

GitHub Actions logs alone are insufficient because they do not include all kernel files and have bounded retention. They are a secondary diagnostic copy.

## 5. Retention tiers

| Tier | Content | Default retention |
|---|---|---|
| Hot | current SQLite state + current operator projections | indefinite/current |
| Warm | GitHub Actions run bundle artifact | 400 days after repo becomes private |
| Durable | private Kaggle run-history version + SHA | indefinite by project policy, verified monthly |
| Analytical | normalized events/metrics in SQLite | indefinite |
| Daily | compact `reports/history/YYYY/MM/DD.json` | indefinite in private repo |
| Current | `reports/current/*.json` on `ops-current` branch | latest only |

No third-party service gives an absolute “forever” guarantee. Therefore monthly archive-health performs random readback, and quarterly export creates a portable encrypted bundle for owner-controlled backup.

## 6. Current reports for ad hoc analysis

Reconciler generates compact files:

```text
reports/current/health.json
reports/current/queue.json
reports/current/product-metrics.json
reports/current/latest-runs.json
reports/current/candidates.json
reports/current/publication-plan.json
```

They contain no secrets, media bytes or raw private chat data. A dedicated `ops-current` branch is force-updated with one commit so connected GitHub tooling and ChatGPT can inspect the current state without downloading SQLite. Daily summaries are appended separately for trend analysis.

## 7. Diagnostic query packs

Repository must ship SQL queries for:

- zero-candidate cycles and reason distribution;
- stage latency p50/p90/p99;
- stuck work by age and reason;
- E5→BGE pair coverage;
- BGE→fusion conversion;
- text→image conversion;
- image→Gemini conversion;
- operator approval/rewrite/reject rates;
- candidate age and queue health;
- repeated provider request fingerprints;
- state changes per run;
- candidates lost between two policy versions;
- source/theme/media concentration;
- publication schedule and diversity violations.

Every automated analysis includes exact `state_version`, `git_sha`, time window and query version.

## 8. History compaction

Current operational rows may be compacted, but decision history is not silently deleted.

- raw working text may be removed after its audit retention if source URL/hash/evidence is preserved;
- vectors may be pruned only after model/version lineage and recomputation inputs remain available;
- media bytes are not canonical state; exact refetch locators and reviewed hashes are;
- terminal rejected rows may move to compact audit tables;
- run logs remain in archive even when normalized events are compacted;
- every compaction creates a before/after count and identity hash receipt.
