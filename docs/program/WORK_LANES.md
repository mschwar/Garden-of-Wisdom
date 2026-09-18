# Work lanes

Lanes are **permanent capabilities**. Waves are **temporary implementation programs**.
Do not confuse them: W1 is a wave that exercises lanes 1–3 and 6; it does not create them,
and it does not finish them.

## Acquisition / expansion lane

Purpose: find or receive potentially valuable material.

Inputs: manual captures, searches, books, public corpora, webpages, transcripts, future
source adapters.

Outputs: raw captures and candidate envelopes **only**.

Success metric: useful recall with preserved provenance, not truth. A noisy batch that
preserved its provenance is a success; a curated-looking batch that dropped it is a failure.

## Ingestion / normalization lane

Purpose: turn heterogeneous captures into consistent candidate records without erasing
originals.

Responsibilities: parse, normalize, preserve raw values, identify obvious structure,
generate duplicate hints, validate required intake fields.

Success metric: every accepted input becomes a durable, reviewable candidate with traceable
origin and an explicit statement of what normalization changed.

## Human curation lane

Purpose: expose candidates to the operator for accept / reject / hold / duplicate decisions.

This lane encodes personal taste and project scope. It must be fast and pleasant enough that
a large noisy intake queue is *useful* rather than burdensome, and it must never present a
machine guess as evidence.

Success metric: the operator can decide with enough context, and can see at a glance which
values are machine-inferred versus evidence-backed.

## Research / verification lane

Purpose: determine what factual claims about an accepted item can actually be supported.

Responsibilities: wording comparison, author/speaker attribution, work/edition/translation
identification, locators, primary/secondary witnesses, competing evidence, known
misattributions, outcome and evidence notes.

Success metric: difficult cases can end honestly as verified, disputed, unverifiable, or
needing more evidence — without pressure to force a conclusion.

## Enrichment / classification lane

Purpose: make canonical material rediscoverable and connected **without changing its
evidentiary status**.

Responsibilities: facets, themes, concepts, languages, periods, cultures, relationships,
variants, related passages.

Success metric: useful multidimensional browsing without forced mutually exclusive
categories. A write in this lane can never change a research state.

## Platform / governance lane

Purpose: provide storage, migrations, validators, queues, UI, automation boundaries, exports,
tests, auditability, runbooks, and decision records.

Success metric: the other lanes are reliable, inspectable, reversible where appropriate, and
cheap to operate.

## Lane interaction rule

Each work unit names its primary lane and any secondary lanes. Cross-lane behavior is
delivered as a vertical slice only when a wave gate requires it; otherwise contracts stay
bounded. A unit that needs to write another lane's state has the wrong design.

## Historical wave ↔ lane map

The W1–W6 map below remains useful as **planning history / capability decomposition**. It is no
longer the forward execution order and conveys **no authorization**. Usability-closure work
demonstrated that canonical admission must precede a full research workbench because
`canonical` and `verified` are orthogonal.

| Historical wave | Primary lanes exercised |
|---|---|
| W1 intake + curation | Ingestion/normalization, Human curation, Platform/governance (Acquisition only manually) |
| W2 research workbench | Research/verification, Platform/governance |
| W3 canonical + enrichment | Enrichment/classification, Platform/governance |
| W4 discovery | Acquisition/expansion, Ingestion/normalization |
| W5 agentic research | Research/verification, Platform/governance |
| W6 exploration | Enrichment/classification, Platform/governance |

## Capability trajectory

Forward planning is expressed as **what the operator can newly do**, not as inherited wave numbers:

1. **U0 — Resumable workbench:** trust a real passage to survive interruption/reclone.
2. **U1 — Grow the Garden:** admit a real passage and find it again in the Garden.
3. **R1 — Investigate a passage:** research one passage with durable claims/evidence/adjudication.
4. **E1 — Explore connections:** navigate facets, variants and relationships without changing
   evidence status.
5. **M1 — Internalize:** resurface/memorize selected passages.
6. **A1 — Cheap upstream feed:** source adapters, potentially including Initiate, emit candidates
   without bypassing Garden curation.

This trajectory is strategic context only. `CURRENT.md` is execution authority.
