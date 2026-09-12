# State model

Do not force all workflow meaning into one status field. W0 should formalize at least these independent dimensions.

## 1. Curation state

Suggested starting vocabulary:

- `new` — captured, not reviewed
- `accepted` — operator wants the item pursued/retained if represented honestly
- `hold` — defer decision
- `rejected` — not wanted in the Garden
- `duplicate` — represented by another candidate/passage

Only the operator, or an explicitly delegated human gate, should move a candidate into `accepted`, `rejected`, or `duplicate` as a final curation decision.

## 2. Research state

Suggested starting vocabulary:

- `not_started`
- `in_research`
- `verified`
- `disputed`
- `unverifiable`
- `needs_more_evidence`

`verified` must be tied to a written verification contract, not agent confidence.

## 3. Corpus state

Suggested starting vocabulary:

- `candidate_only`
- `eligible`
- `canonical`
- `retired`

W0 must define exact promotion requirements. A likely rule is that curation acceptance is necessary for eligibility; the research outcome determines how the record may be represented. `canonical` must not imply `verified` if disputed/unverifiable records are intentionally retained with visible uncertainty.

## 4. Work state

Execution state belongs to work units/research cases, not passage truth:

- `queued`
- `active`
- `qa`
- `blocked`
- `done`

## Transition invariants

1. Discovery cannot directly create `canonical` records.
2. Curation acceptance cannot set research outcome to `verified`.
3. Research findings cannot silently overwrite the original capture.
4. Reclassification/enrichment cannot upgrade evidence state.
5. Rejected material remains auditable unless a separate retention policy says otherwise.
6. Every machine-inferred field that matters to provenance must remain distinguishable from human/evidence-backed assertion until adjudicated.
7. Wave implementation must include deterministic transition tests before the transition is relied upon operationally.

## Canonical test scenario

The model is not ready until it can represent all of these without false certainty:

- exact genuine quote
- paraphrase
- wrong author
- wrong work/citation
- quote of a quote
- translation variant
- fabricated or spurious internet attribution
- oral attribution
- ambiguous source
- genuinely unverifiable item
