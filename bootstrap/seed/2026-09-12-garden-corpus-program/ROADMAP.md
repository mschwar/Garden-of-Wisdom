# Gated roadmap

## W0 — doctrine and contracts

Goal: convert the bootstrap into canonical repo doctrine and remove architectural ambiguity before implementation.

Deliverables: reconciled product/program doctrine, state model, provenance model, candidate envelope, verification contract, lane definitions, decision log entries, W1 decomposition, explicit unresolved questions.

Stop: no runtime implementation.

Gate: a messy uncited candidate can be walked deterministically through capture, curation, research, and possible canonical outcomes without conflating taste with truth.

## W1 — intake + human curation vertical slice

Goal: prove the central human loop.

Target flow: manual submission -> durable capture -> normalized candidate -> duplicate hints -> operator accept/reject/hold/duplicate.

Likely units: storage decision/migration, intake contract implementation, CLI/API or simplest submission surface, intake table UI, review actions, audit history, end-to-end tests.

Gate: a representative batch of messy manual candidates can be reviewed without losing original provenance or creating canonical claims prematurely.

## W2 — research workbench

Goal: prove evidence-bearing investigation and adjudication.

Target flow: accepted candidate -> research case -> claims/evidence -> outcome -> operator-visible record.

Gate: the canonical ten-case adversarial set in `STATE_MACHINE.md` can all be represented honestly.

## W3 — canonical corpus + enrichment

Goal: establish the promotion seam and useful faceted browsing.

Target flow: eligible researched material -> canonical representation -> facets/relationships -> browser/export.

Gate: multidimensional browsing works while curation state, evidence state, and enrichment remain separate.

## W4 — discovery automation

Goal: add one bounded automated discovery source through the common intake envelope.

Do not start with many adapters. Prove one source end-to-end first.

Gate: a noisy batch can enter intake without bypassing human curation or contaminating canonical data.

## W5 — agentic research at scale

Goal: let agents execute bounded research cases with evidence packages and independent QA.

Gate: repeated cases show acceptable evidence quality, reproducibility, failure handling, and cost before volume increases.

## W6 — exploration and higher-order intelligence

Potential capabilities: semantic similarity, recommendation, memorization queues, thematic pathways, cross-tradition parallels, concept graphs, synthesis over verified material, dynamic downstream exports.

Gate: these features must consume provenance-aware canonical data rather than become a parallel source of truth.

## Authorization rule

Only the current authorized wave may be implemented. Later-wave ideas discovered during execution go to a queue/spec; they do not become opportunistic implementation.
