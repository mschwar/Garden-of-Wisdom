# Garden Corpus Program — canonical doctrine

Status as of 2026-09-12 (**W0 complete, Gate A submitted**): doctrine and contracts only.
**W1 is NOT started.** No datastore, intake surface, discovery adapter, or W1 runtime code
exists in this repo.

This directory is the canonical home for Garden *corpus-program* doctrine: doctrine, the
entity/state model, provenance and evidence contracts, lane definitions, classification
posture, and the bounded W1 decomposition.

## Relationship to the rest of the repo

| Question | Canonical doc |
|---|---|
| What is Garden of Wisdom, and what is it not? | `../product/PRODUCT_DOCTRINE.md` |
| What are the CSVs, their schema, and known data issues? | `../data/DATA_CONTRACT.md` |
| Why was a past choice made? | `../DECISIONS.md` (append-only) |
| What work is open? | `../queue.md` |
| How do I run/validate things? | `../RUNBOOK.md` |
| How does a candidate become a canonical Garden record? | **this directory** |

`../product/PRODUCT_DOCTRINE.md` remains the product-level authority. It is *not*
restated here; its non-negotiables are inherited by reference. This directory governs only
the *corpus lifecycle* (capture → curation → research → canonical → enrichment) and never
weakens a product non-negotiable. See `CORPUS_PROGRAM_DOCTRINE.md` §"Reconciliation".

## Read order

1. `CORPUS_PROGRAM_DOCTRINE.md` — reconciled doctrine, governing principles, human gates
2. `SYSTEM_MODEL.md` — entities and boundaries
3. `STATE_MODEL.md` — the four orthogonal state dimensions, transition authority, invariants
4. `PROVENANCE_AND_CAPTURE_CONTRACT.md` — what is preserved from a raw encounter
5. `CANDIDATE_ENVELOPE.md` — the source-agnostic intake contract
6. `VERIFICATION_CONTRACT.md` — what makes a factual claim `verified`
7. `WORK_LANES.md` — permanent lane definitions
8. `CLASSIFICATION_AND_FACETS.md` — faceted classification posture and open ontology questions
9. `W1_DECOMPOSITION.md` — bounded W1 work units (proposed; not started)
10. `W0_GATE_REPORT.md` — Gate A evidence, decisions, unresolved questions, exact stop point

The bootstrap seed that W0 reconciled lives in
`../../bootstrap/seed/2026-09-12-garden-corpus-program/`. It is planning input, not
authority: where it conflicts with existing repo doctrine, `CORPUS_PROGRAM_DOCTRINE.md`
§"Reconciliation" records the ruling.

## Scope boundary (what W0 did and did not do)

W0 changed documentation, decision/queue entries, and planning fixtures **only**.

**Not done in W0, deliberately:** no datastore chosen or migrated, no schema change to
`quotes.csv` / `sources.csv`, no intake UI, no crawler or discovery adapter, no embeddings
or vector search, no knowledge graph, no automatic quote approval, no bulk verification, no
browser behavior change.

Current data and validators are untouched: `quotes.csv` and `sources.csv` are byte-identical
to `main` (see `W0_GATE_REPORT.md` §Evidence).

## Verify the doctrine set

```
python3 scripts/check_program_contracts.py   # docs/fixture consistency + scenario invariants
python3 scripts/validate_quotes.py           # unchanged by W0, must still PASS
```
