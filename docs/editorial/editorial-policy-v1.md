# Region Talk editorial policy v1

> Status: proposed canonical baseline for implementation and corpus calibration. It consolidates the selected “option B” direction from the cross-project editorial synthesis with the existing Region Talk Writer/source/media contracts.

## 1. Voice core

**Спокойный культурный навигатор с редакционным теплом.**

The voice:

- is clear, modern and respectful;
- explains why this external view is worth attention;
- uses concrete facts and observations;
- does not pressure, flatter or imitate intimacy;
- is interested rather than excited by default;
- may use rare situational lightness, but never requires a joke;
- treats the source as an independent author/publication, not as raw material owned by Region Talk.

## 2. Content purpose

Every post must answer:

1. who is looking at Kaliningrad Oblast and from what verified perspective;
2. what exactly the source noticed, found, compared or explained;
3. what concrete detail makes opening the original worthwhile;
4. where the exact original is.

It must not become:

- a generic destination advertisement;
- a retelling without attribution;
- an invented biography of the source;
- a news digest;
- praise made from unsupported adjectives;
- clickbait or “read because it is valuable” metatext.

## 3. Fact-lock hierarchy

```text
source evidence and current material facts
> legal/safety/attribution integrity
> clarity and source ownership
> surface/length constraints
> voice core
> stylistic variation
```

Style cannot change:

- names, dates, places, numbers, access or price;
- what the source actually says/does;
- external/local classification;
- uncertainty or evidence status;
- exact original URL;
- media identity/order;
- CTA action;
- approval/publication state.

Missing evidence produces `NEEDS_FACTS`, `NEEDS_SOURCE_PROFILE` or `NEEDS_GROUNDING_REVIEW`, never plausible filler.

## 4. Post structure

### Paragraph 1

Exactly two sentences:

1. a grounded current-content hook, normally 45–110 characters;
2. a compact source-value/onboarding sentence grounded in the reusable source/publisher profile.

The source name must not be used as padding in the hook when it does not improve meaning.

### Paragraph 2

One or two complete sentences containing one or two concrete details from the current material. It should show the material rather than advertise the act of reading it.

### Footer

```text
{paragraph 1}

{paragraph 2}

{source-aware CTA linked to exact original}

О Калининграде говорят → https://t.me/kalinigrad_visit
```

The body contains no URL or duplicated CTA. One exact source/original link and one channel footer are allowed.

Target visible caption: 550–900 characters for the ordinary media-first format. A shorter result may be allowed only by an explicit surface policy and must still contain complete orientation/details; 900 is a hard maximum for this contract.

## 5. Source-aware CTA

Choose deterministically from evidence/entity type:

- `Подробнее — у автора …`;
- `Подробнее — в блоге …`;
- `Подробнее — в канале «…»`;
- `Подробнее — в статье на …`;
- `Подробнее — в статье журнала «…»`;
- safe fallback: `Подробнее — в оригинальной публикации`.

The full phrase is one link to the canonical concrete material. Do not add a second outlet homepage.

## 6. Source profile rules

Social source profile requires bounded public evidence:

- description;
- pinned/about evidence;
- 30–80 recent rows, default 50;
- at least 20 authored posts when available;
- 8–16 diverse evidence excerpts;
- authored/repost/service/ad classification;
- exact evidence URL/date and fingerprint.

Publisher reader brief requires grounded dimensions:

- outlet identity;
- intended audience;
- distinctive editorial value.

The profile may contain a clearly worded editorial inference from repeated authored evidence. Hard biography, nationality, profession, awards, travel breadth or declared mission require direct public support.

Prefer the angle that explains this material, not prestige.

## 7. Language rules

Use:

- concrete verbs;
- specific nouns/details;
- natural contemporary Russian;
- varied but controlled sentence rhythm;
- third-person attribution of source observations;
- `мы` only for a real editorial action such as “проверили” or “выбрали”.

Avoid/reject:

- advertising clichés: `уникальный`, `незабываемый`, `погрузитесь`, `обязательно`, unsupported `известный/ведущий/крупнейший`;
- promise of the reader’s emotion;
- generic triads and smooth LLM filler;
- metatext: `материал представляет ценность`, `публикация позволяет`, `читайте подробнее` inside body;
- adversative AI cliché family `не …, а …`, including punctuation/dash/line-break variants;
- a string of adjectives without evidence;
- source praise instead of source description;
- unresolved pronouns and incomplete sentences;
- arbitrary English prose; exact source-owned Latin names/handles are allowed.

Word-list matches are signals for review where context matters; unsupported prestige and the named deterministic clichés are hard failures under the current contract.

## 8. Irony and emotional register

Default Region Talk irony cap: 1 on a 0–4 scale.

Allowed only when:

- it is a mild observation about situation/place/weather/format;
- it is not needed to understand the facts;
- it does not target the source, residents, tourists, children, age, ability, budget or experience;
- removing it leaves a complete post;
- it does not compete with attribution or caveats.

Set irony to zero for:

- tragedy, memorial, illness, vulnerability;
- conflict/complaint/correction;
- safety, legal, money or access problems;
- source criticism that could become ridicule;
- uncertain or incomplete evidence.

## 9. Media-first integrity

The exact review/publication revision includes body + URL + ordered media + layout.

Preferred modes:

1. associated article hero;
2. exact social hero;
3. ordered 3–6-frame social album;
4. exact source video with operator video review;
5. link preview only after terminal no-usable-media evidence.

Do not replace the reviewed source media with a decorative card or another source asset at send time. A changed hash/order requires a new review revision.

## 10. Review and publication gate

A draft is `READY_FOR_OPERATOR` only if:

- all required source/material facts are grounded;
- source profile is ready;
- exact body structure passes;
- visible length passes;
- deterministic style/fact/link validators pass;
- critic returns pass after at most one grounded rewrite;
- exact media manifest is materializable;
- candidate is current and not already published.

Public publishing additionally requires:

- exact current positive reaction from an allowlisted reviewer;
- no negative/conflict/rewrite request;
- current schedule/diversity plan;
- final media hash/materialization verification;
- idempotent outbox reservation.

## 11. Change process

Every policy/prompt/model change requires:

- version bump;
- candidate decision diff on golden and recent production-shaped samples;
- full editorial golden/adversarial suite;
- fact fidelity check;
- human review of changed and high-risk outputs;
- shadow delivery for materially changed copy;
- preserved previous policy for rollback.
