# External research intake

## User workflow

A new deep-research result is added as a reviewed JSON file:

```text
research/intake/region-talk-external-research-result-<request-id>.json
```

After PR review and merge to `main`, the ordinary controller imports it deterministically into SQLite and routes retained candidates through the same E5/BGE/image/source-profile/finalizer gates.

## Why import runs in GitHub Actions

Research import is CPU-light, deterministic and does not require Kaggle models. Running it in the reconciler:

- avoids an unnecessary kernel;
- validates exact trusted Git bytes;
- uses the same single-writer transaction;
- gives immediate all-or-nothing receipt;
- does not expose secrets to the research input.

## Trust boundary

Accepted path must:

- be a regular non-symlink file inside `research/intake/`;
- match the exact filename pattern;
- exist in trusted default-branch checkout;
- pass JSON Schema and semantic validation;
- have a documented SHA-256;
- contain no executable code, embedded credential or private personal data;
- use a unique `request_id`.

PR validation never writes state. Import occurs only from `main`.

## Transaction semantics

- Reserve `(request_id, input_sha256)`.
- Exact replay is a no-op with a receipt.
- Same `request_id` with different bytes is a hard conflict.
- Canonical URL, DOI and normalized title+authors identities are reserved atomically.
- Any invalid/conflicting row aborts the package; no partial subset import.
- Excluded and unresolved identities are retained for dedupe/audit.
- New candidate rows start with:
  - `review_status=unreviewed`;
  - `publication_permission=not_granted`;
  - `downstream_stage=research_intake`.

Import never creates a final publication draft, approval or public outbox row.

## Required result contract

Minimum top-level fields:

```json
{
  "schema_version": "region-talk-external-research-v2",
  "request_id": "region-talk-external-2026-08-04-001",
  "created_at": "2026-08-04T00:00:00Z",
  "research_scope": {},
  "candidates": [],
  "excluded": [],
  "unresolved": [],
  "publisher_profiles": [],
  "source_registry_snapshot": {},
  "methodology": {},
  "limitations": []
}
```

Every candidate must preserve:

- canonical URL and observed title;
- source/publisher identity;
- author/date when known;
- full-text/access status;
- locality/externality evidence;
- news/commercial/policy classification;
- exact evidence URLs/excerpts;
- downstream readiness;
- reasoned inclusion/exclusion;
- publisher dossier linkage when needed.

`manual_review_required` is not a valid terminal research output for candidate-local facts that the research agent could resolve. Truly unresolved pages must be placed in `unresolved` with a concrete missing-evidence reason.

## Pipeline priority

Fresh imported exact links receive priority over generic discovery but do not bypass quality gates:

```text
research import
→ exact content acquisition
→ current text hash
→ E5
→ BGE-M3
→ fusion and strict text policy
→ media diagnostic
→ source/publisher profile
→ final verifier and Writer
→ operator review
```

## Receipts and analysis

Each import emits:

- input path and SHA;
- schema/policy versions;
- new/replay/conflict counts and IDs;
- identity reservations;
- excluded/unresolved counts;
- downstream work opened;
- state version before/after;
- zero publication effect proof.

Product reports separately measure `research_intake_to_operator_candidate_rate` and time-to-ready.
