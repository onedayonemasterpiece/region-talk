# Продуктовые метрики Region Talk

## North-star outcome

Region Talk считается полезным, когда регулярно доставляет оператору **новые, качественные и реально публикуемые внешние взгляды на Калининградскую область**, а не просто расширяет технические очереди.

## 1. Outcome metrics

- `fresh_operator_candidates` — новые exact revisions, впервые доставленные в review chat;
- `operator_approved_candidates`;
- `published_candidates`;
- `candidate_time_to_review_ready`;
- `approved_time_to_publish`;
- `cycles_with_zero_operator_candidates_rate`;
- `compute_runs_per_operator_candidate`;
- `provider_calls_per_operator_candidate`;
- `research_intake_to_operator_candidate_rate`;
- `source_discovery_to_operator_candidate_rate`.

## 2. Funnel

```text
intake/fetched
→ current text acquired
→ E5 current
→ BGE current
→ fused strict text accepted
→ media decision ready
→ source/publisher profile ready
→ final verifier accepted
→ editorial revision ready
→ delivered to operator
→ approved / rewrite / rejected
→ scheduled
→ published
```

At every stage record:

- entry count;
- success count;
- non-terminal wait count;
- terminal reject count;
- top reason codes;
- median/p90 age;
- unique sources and canonical URLs.

Counts at different grains are never summed as one funnel total.

## 3. Quality metrics

### Discovery/content

- external-source precision in human sample;
- KO-main-subject precision;
- non-news/non-ad precision;
- duplicate/repost rate;
- useful concrete detail rate;
- source-profile evidence completeness;
- article full-text/access completeness.

### Editorial

- operator approval/rewrite/reject rate;
- unsupported-claim rate;
- fact correction rate;
- first-draft pass rate;
- length/structure validation failures;
- source onboarding quality score;
- cliché/style failure distribution;
- media replaced by operator rate.

### Diversity

- unique source share over 7/30 days;
- topic/place/source/media-mode concentration;
- adjacent similarity violations;
- article/social balance;
- repeated publisher/author interval.

### Publication

- on-time slot rate;
- retry/ambiguous outcome rate;
- duplicate publication incidents;
- media materialization fallback rate;
- views/reactions/forwards at fixed horizons when available;
- original-link click rate only when ethically and technically measurable.

Engagement does not override editorial accuracy or operator decisions.

## 4. Efficiency metrics

- Kaggle CPU minutes per stage and candidate;
- peak memory and model load failures;
- GitHub controller minutes/ticks per state advance;
- Supabase RPC/rows/bytes by function;
- Google physical attempts, RPM/TPM/RPD denies and 429 cooldowns;
- Telegram requests/flood waits;
- bytes in state/run-history versions;
- percentage of materially unchanged writes omitted.

## 5. Health versus product result

Dashboard has two independent verdicts:

### System health

- controller running;
- state head readable;
- archives complete;
- no stale active attempt;
- providers reachable/budgeted;
- review and publisher transport healthy.

### Product health

- new candidates in target window;
- queue aging;
- funnel conversion;
- approval rate;
- source/diversity health;
- zero-progress reasons;
- publication plan fill.

A green system with no candidates is not automatically a healthy product.

## 6. Daily/weekly review

### Daily compact report

- latest state and runs;
- new candidates and decisions;
- due/filled publication slots;
- top blockers;
- zero-progress cycles;
- technical errors;
- provider/transport budgets.

### Weekly product report

- funnel comparison with previous 4 weeks;
- candidate and publication yield;
- quality/rewrite/reject reasons;
- source/topic/media diversity;
- research intake effectiveness;
- expensive/low-yield stages;
- recommended policy/queue/model experiments;
- uncertainty and data-quality notes.
