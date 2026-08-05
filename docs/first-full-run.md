# Обязательный анализ первого полного прогона

Первый полный run после SQLite/Kaggle cutover не считается завершением внедрения. Это controlled experiment, после которого обязательны анализ и при необходимости отладка.

## 1. Evidence package

Собрать:

- exact state version before/after;
- all stage attempts and Kaggle versions;
- complete run bundles;
- Git SHA, migrations, model/prompt/policy revisions;
- YDB migration receipt;
- queue and product metric snapshots;
- candidate/operator revisions;
- Supabase limiter/control usage;
- Telegram request/reaction evidence;
- no-publication or canary-publication proof.

## 2. Technical review

For every stage:

- terminal status and wall time;
- progress/heartbeat continuity;
- CPU/RSS/disk profile;
- input/output counts;
- retries and errors;
- unchanged/replayed rows;
- log completeness and redaction;
- state delta and invariant result;
- next-stage handoff correctness.

Explicitly verify E5 and BGE ran in separate CPU kernels and fused only matching current fingerprints.

## 3. Product funnel review

Report:

```text
research/manual exact links
sources checked
posts fetched
current E5
current BGE
fused strict accepts
text rejects by reason
media ready / visual review / terminal media rejects
profiles ready / missing / conflicting
final verifier accepts/rejects/errors
editorial revisions ready
operator messages sent
```

For zero or low yield, identify the narrowest real bottleneck rather than increasing discovery indiscriminately.

## 4. Candidate-level review

For every operator-ready candidate:

- original URL and source type;
- why it is external and KO-relevant;
- text/vector evidence;
- media mode and ordered manifest;
- source/publisher profile evidence;
- final verifier decision;
- exact two-paragraph copy;
- known caveats;
- comparison with policy/golden examples.

For a sample of rejected/deferred candidates, check false negatives and dead-end states.

## 5. Data-quality checks

- no duplicate canonical identities;
- no missing source/post links;
- no stale E5/BGE fusion;
- no active work absent from projection;
- no queue status contradictions;
- no approved candidate without current revision;
- no publication slot without exact approval/media;
- no unknown legacy YDB row silently dropped;
- all run/archive locators downloadable and hash-valid.

## 6. Cost/efficiency review

- Kaggle CPU time by useful outcome;
- GitHub Actions minutes/ticks;
- Supabase calls/rows/egress estimates;
- Google requests/attempts/tokens and limiter denies;
- Telegram/VK request counts;
- state/archive growth;
- projected monthly consumption under current cadence.

## 7. Decisions after run

Classify findings:

- `P0 correctness/safety` — block all further progression;
- `P1 candidate-yield` — fix before autonomous steady state;
- `P1 observability` — incomplete evidence blocks trust;
- `P2 efficiency` — optimize after correctness;
- `P2 editorial quality` — corpus/prompt/policy iteration;
- `P3 enhancement`.

Every accepted change adds a regression test or monitoring rule.

## 8. Exit criteria

The first run is accepted only when:

- all state/log archives are complete and reproducible;
- no secret leak or unexplained state mutation exists;
- separate E5/BGE path works;
- candidate funnel either produces operator candidates or gives a verified content-supply explanation;
- operator review is exact and idempotent;
- current queue/health reports are queryable;
- monthly resource projection is acceptable;
- a concrete next calibration plan exists.

Only after acceptance should private-channel publisher canary and then the first production canary be attempted.
