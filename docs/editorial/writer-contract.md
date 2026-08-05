# Region Talk Writer contract

## Input

Writer receives only structured, versioned evidence:

```json
{
  "candidate_id": "...",
  "candidate_revision": 3,
  "current_material": {
    "canonical_url": "...",
    "content_facts": [],
    "source_quotes": [],
    "media_manifest_fingerprint": "..."
  },
  "source_profile": {
    "status": "ready",
    "entity_type": "person|collective|thematic_channel|media_brand",
    "claims": [],
    "publisher_dimensions": {}
  },
  "history": [],
  "policy_versions": {},
  "constraints": {
    "paragraph_1_sentences": 2,
    "paragraph_2_sentences": [1, 2],
    "visible_chars": [550, 900]
  }
}
```

Every usable fact has an ID and evidence reference. Writer cannot browse or infer missing biography.

## Stages

1. `strategy` — choose one current-material angle and honest history mode.
2. `grounded_writer` — return exactly two paragraphs plus evidence mapping.
3. deterministic validation — facts, paragraphs, sentence count, language, links, clichés, length.
4. `critic` — `pass|rewrite|reject` with compact issue/evidence IDs.
5. at most one writer retry using the measured failure.
6. exact renderer adds deterministic CTA/footer and validates again.

## Output

```json
{
  "status": "ready|needs_facts|needs_source_profile|needs_grounding_review|rejected",
  "paragraph_1": "...",
  "paragraph_2": "...",
  "grounding": [
    {"span": "...", "fact_ids": ["f1"], "profile_claim_ids": []}
  ],
  "strategy": {},
  "critic": {},
  "violations": [],
  "prompt_version": "...",
  "model": "...",
  "request_fingerprint": "..."
}
```

## Hard failures

- unsupported fact/biography/prestige;
- omitted material caveat;
- source ownership ambiguity;
- body URL or CTA/metatext;
- wrong paragraph/sentence structure;
- incomplete sentence;
- unsafe irony;
- invented urgency/emotion;
- exact named deterministic cliché violations;
- missing/invalid evidence IDs;
- stale candidate/media/source fingerprint;
- visible caption beyond platform/policy limit.

## History use

At most five approved/published predecessors may be supplied. They are used to avoid repetition and select an honest bridge, not to force continuity. If no natural bridge exists, use `fresh_start`.

## Provider governance

- Every stage uses the shared atomic Google limiter.
- Stage calls have deterministic request fingerprints.
- Completed unchanged calls replay without provider send.
- No local limiter fallback in Kaggle/GitHub production.
- Prompt/model/usage/status/attempt data is logged without secret/key values.
