# Garden Corpus Program bootstrap

Status: **planning/scaffolding packet only**. No runtime implementation is authorized by this packet.

## North star

Evolve Garden of Wisdom from a rehabilitated quote collection into a **provenance-aware, human-governed wisdom corpus**.

The system should make it cheap to capture and discover candidate material, preserve where it came from, let agents do substantial normalization/research/enrichment work, and keep the operator in control of admission into the Garden. Discovery may be noisy. Canonical claims may not be.

The permanent architecture is a set of work lanes around one corpus; implementation proceeds in temporary, gated waves.

## Read order

1. `ORIGIN_AND_INTENT.md`
2. `PROGRAM_DOCTRINE.md`
3. `SYSTEM_MODEL.md`
4. `STATE_MACHINE.md`
5. `WORK_LANES.md`
6. `ROADMAP.md`
7. `EXECUTION_PROTOCOL.md`
8. `ACCEPTANCE_GATES.md`
9. `NON_GOALS.md`
10. `waves/W0_DOCTRINE.md`

An execution agent should then read `prompts/00_EXECUTE_W0.txt`.

## Program shape

Permanent lanes:

- Acquisition / expansion
- Ingestion / normalization
- Human curation
- Research / verification
- Enrichment / classification
- Platform / governance

Temporary waves:

- W0 — doctrine and contracts
- W1 — intake + human curation vertical slice
- W2 — research workbench
- W3 — canonical corpus + enrichment
- W4 — discovery automation
- W5 — agentic research at scale
- W6 — exploration / higher-order intelligence

## Critical sequencing rule

**Do not start a later wave because its design looks obvious.** Each wave exists to expose unknowns needed to design the next one safely.

This packet does **not** authorize a crawler, a database migration, Postgres, embeddings/vector search, a knowledge graph, automatic quote approval, bulk verification, or changing current canonical CSV/browser behavior.

W0 exists to convert this bootstrap into canonical repo doctrine and explicit state/provenance contracts. Only after the W0 evidence gate is accepted should W1 implementation be decomposed.

## Operator workflow

`frontier conversation -> bounded repo-native packet -> cheap/local agent execution -> evidence-bearing stop gate -> frontier review`

Within a wave:

`one contract -> one isolated branch/worktree -> implementation/research -> evidence -> foreign QA -> fixes -> discovered-work capture -> merge -> report`

## Seed vs canonical docs

Everything here is a **bootstrap seed**. W0 must reconcile it against existing repo doctrine and produce canonical living documents under `docs/` with explicit decisions and unresolved questions.
