# W0 — doctrine and contracts

## Mission

Turn the bootstrap seed into canonical repo doctrine and explicit contracts for the next implementation wave. Resolve ambiguity in state, provenance, evidence, and human gates before choosing runtime architecture.

## Inputs

Read at minimum:

- root `README.md`
- `AGENTS.md`
- `docs/product/PRODUCT_DOCTRINE.md`
- `docs/data/DATA_CONTRACT.md`
- `docs/DECISIONS.md`
- `docs/queue.md`
- current validator/browser architecture docs
- this bootstrap packet

## Required outputs

Create or update canonical documents under `docs/` covering:

1. corpus/program doctrine reconciled with existing product doctrine
2. entity/system model
3. orthogonal state model and transition authority
4. provenance/capture contract
5. candidate-envelope contract
6. verification/evidence contract
7. permanent work-lane definitions
8. classification/facet posture, with unresolved ontology questions explicit
9. W1 implementation decomposition into bounded work units
10. decision-log entries for material choices
11. queue entries for deferred ideas/debt
12. W0 evidence-gate report

## Questions W0 must answer

- What exactly is preserved from a raw capture?
- What is a candidate versus a passage versus a canonical record?
- Which states are independent?
- Which transitions require the operator?
- What qualifies as evidence?
- What exact standard upgrades a factual claim to verified?
- How are translation variants, paraphrases, wrong attributions, and unverifiable material represented?
- How does current `quotes.csv` map conceptually into the future model without forcing an immediate migration?
- What minimum storage/access requirements does W1 actually have?
- What is the smallest complete W1 vertical slice?

## Explicit non-implementation boundary

W0 may change documentation, decisions, queue/spec files, and planning fixtures/examples. It must not migrate canonical data, introduce a production datastore, build intake UI, add automated discovery, or alter current browser behavior except for documentation links if needed.

## Gate A evidence

Produce a short `W0_GATE_REPORT.md` that demonstrates:

- one uncited candidate traced through capture -> curation -> research -> possible corpus outcomes
- one verified example
- one disputed example
- one unverifiable example
- one translation/variant example
- transition authority for every step
- unresolved questions/debt
- proposed W1 work-unit order

STOP after Gate A. Do not execute W1.
