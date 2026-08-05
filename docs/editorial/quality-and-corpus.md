# Editorial quality and corpus

## 1. Quality decision

```text
schema/fact validation
→ deterministic lint
→ Writer
→ grounding validation
→ independent critic
→ one bounded rewrite
→ renderer validation
→ operator review
```

Outcome: `PASS`, `REWRITE`, `REJECT` or a named non-terminal evidence state.

## 2. Scored rubric 0–4

- factual fidelity;
- source ownership and attribution;
- clarity;
- natural Russian;
- literary/editorial quality;
- concrete material value;
- source onboarding quality;
- surface fit;
- respect/ethics;
- concision/structure;
- media-text coherence;
- brand coherence;
- irony safety when present.

Release hypothesis: no mandatory criterion below 3 and no hard failure. Thresholds must be calibrated against human labels, not treated as intrinsic truth.

## 3. Golden corpus classes

- strong external travel/photo account;
- external architecture/history publication;
- academic material with public-interest kernel;
- first-person route/visit impression;
- mixed but constructive criticism;
- generic destination card (reject);
- local news/reporting (reject);
- advertising/tour/announcement (reject);
- multi-region roundup (reject/defer);
- unsupported source biography;
- article teaser without full access;
- attractive but unrelated image;
- incomplete album;
- video operator-review path;
- source-profile contradiction;
- good/repetitive/clichéd/overwritten Russian copy;
- old approval after material revision;
- schedule diversity conflict.

Each fixture includes input facts/evidence, expected state, allowed variation and disallowed claims.

## 4. Adversarial corpus

Include realistic near-misses:

- one invented adjective that implies prestige;
- one unsupported travel breadth claim;
- source sentence based only on current article;
- exact fact hidden behind metaphor;
- `не …, а …` punctuation variants;
- URL or CTA inside body;
- source name padding the hook;
- 901-character caption;
- one-sentence first paragraph;
- confident copy over `needs_review` evidence;
- approval attached to old media order;
- positive reaction from non-allowlisted account;
- duplicated provider request under another run ID.

## 5. Human review

Sample:

- every new policy/prompt class;
- all sensitive/mixed criticism cases;
- all first examples for a source entity type;
- changed outputs after model upgrade;
- random ordinary candidates;
- false-positive and false-negative samples.

Questions:

- Is every claim supported?
- Is it immediately clear who says what?
- Is there one concrete reason to open the original?
- Does the source sentence orient rather than praise?
- Does the Russian sound natural and non-generated?
- Would this voice remain acceptable every day?
- Does media belong to the exact material and match the text?

## 6. Metrics

Do not optimize editorial policy by CTR alone. Track:

- fact correction and unsupported claim rate;
- operator approval/rewrite/reject;
- first-draft pass;
- reviewer disagreement;
- repeated construction rate;
- source/profile correction;
- media replacement;
- complaints/deletions;
- original-link usage when safely measurable;
- editing time and reason.
