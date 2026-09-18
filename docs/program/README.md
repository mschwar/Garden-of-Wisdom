# Garden Corpus Program — canonical doctrine

**This directory is doctrine and history; live programme status is not here.** It lives in
`docs/program/usability-closure/CURRENT.md` (current gate, the single READY unit, the last
completed unit, the frontier). If this file and CURRENT disagree about status, CURRENT wins.

Status as of 2026-09-17: **W0 complete, Gate A accepted** (`../audit/2026-09-12/GATE_A_FRONTIER_REVIEW.md`);
**W1 complete, Gate B accepted** 2026-09-13 (`../audit/2026-09-13/GATE_B_FRONTIER_REVIEW.md`).
Doctrine, contracts and the W1 runtime all landed: the store, the candidate envelope, the
submission CLI, normalization + duplicate hints, the curation surface and the end-to-end pack
are implemented in `scripts/garden_store.py`, `garden_envelope.py`, `garden_submit.py`,
`garden_normalize.py` and `garden_review.py`, each with a `scripts/check_garden_*.py`
acceptance suite and a committed negative-control table (`scripts/run_negative_controls.py`).
**W2 is not started** — still absent are a discovery adapter and any canonical promotion path.

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
| **What is the live programme status, and what do I work on next?** | **`usability-closure/CURRENT.md`** |
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
9. `W1_DECOMPOSITION.md` — the bounded W1 work units; **historical plan, all six landed**
   (authorized in full 2026-09-12 — see `../DECISIONS.md` and `../queue.md`)
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

Current data and validators were untouched at W0's close: `quotes.csv` and `sources.csv` were
byte-identical to `main` *at that time* (see `W0_GATE_REPORT.md` §Evidence, which keeps the
point-in-time transcript). That is history, not live status — the later named data units (D3,
D4, D7, D8) did change `sources.csv` and `quotes.csv`, each with its own acceptance run and
its own dated entry in `../DECISIONS.md`.

## Verify the doctrine set

```
python3 scripts/check_program_contracts.py   # docs/fixture consistency + scenario invariants
python3 scripts/validate_quotes.py           # unchanged by W0, must still PASS
python3 scripts/check_front_door.py          # front-door docs still describe current state
```
