# Work lanes

Lanes are permanent capabilities. Waves are temporary implementation programs. Do not confuse them.

## Acquisition / expansion lane

Purpose: find or receive potentially valuable material.

Inputs: manual captures, searches, books, public corpora, webpages, transcripts, future source adapters.

Outputs: raw captures and candidate envelopes only.

Success metric: useful recall with preserved provenance, not truth.

## Ingestion / normalization lane

Purpose: turn heterogeneous captures into consistent candidate records without erasing originals.

Responsibilities: parse, normalize, preserve raw values, identify obvious structure, generate duplicate hints, validate required intake fields.

Success metric: every accepted input becomes a durable, reviewable candidate with traceable origin.

## Human curation lane

Purpose: expose candidates to the operator for accept / reject / hold / duplicate decisions.

This lane encodes personal taste and project scope. It must be fast and pleasant enough that a large noisy intake queue is useful rather than burdensome.

Success metric: operator can make decisions with enough context and without confusing machine guesses for evidence.

## Research / verification lane

Purpose: determine what factual claims about an accepted item can actually be supported.

Responsibilities: wording comparison, author/speaker attribution, work/edition/translation identification, locators, primary/secondary witnesses, competing evidence, known misattributions, outcome and confidence/evidence notes.

Success metric: difficult cases can end honestly as verified, disputed, unverifiable, or needing more evidence.

## Enrichment / classification lane

Purpose: make canonical material rediscoverable and connected without changing its evidentiary status.

Responsibilities may include facets, themes, concepts, languages, periods, cultures, relationships, variants, and related passages.

Success metric: useful multidimensional browsing without forced mutually exclusive categories.

## Platform / governance lane

Purpose: provide storage, migrations, validators, queues, UI, automation boundaries, exports, tests, auditability, runbooks, and decision records.

Success metric: the other lanes are reliable, inspectable, reversible where appropriate, and cheap to operate.

## Lane interaction rule

Each work unit must name its primary lane and any secondary lanes. Cross-lane behavior should be delivered as a vertical slice only when needed for a wave gate; otherwise keep contracts bounded.
