# R0 — Product Reality & System Reconciliation

**Status: COMPLETE when this PR merges.** This is a bounded reconciliation inserted between U0.2
and U0.3 because U0.1/U0.2 made the implementation and execution front door dependable enough to
expose a product-definition mismatch before the first real persistent canary.

## Operator capability after this unit

A fresh competent operator/agent can mechanically answer:

- what Garden is actually for;
- what the durable domain object is;
- what belongs in Garden versus Initiate;
- what is product versus substrate;
- what works now and where real use breaks;
- what state/documents are authoritative;
- why U0.3/U1 are the next closures.

## Why this exists

The current 324-row religious/philosophical corpus had become an accidental product boundary.
Meanwhile the program model had already evolved toward a general Passage entity, and Initiate had
matured into the broader lifecycle for arbitrary things worth remembering.

Running U0.3 before reconciling those facts would persist the first real new candidate under a
definition we already know is too narrow.

## In scope

- broaden Product Doctrine from religious/philosophical “quotes” to personally curated passages
  across domains;
- make **Passage** the durable product term while preserving legacy CSV/browser “quote” naming;
- define the Garden ↔ Initiate boundary without integrating the repos;
- create `docs/PRODUCT_REALITY.md` as the standing system/usability dashboard;
- keep `CURRENT.md` tiny and execution-authoritative;
- correct stale System Model statements about storage and canonical/research coupling;
- demote the old W2→W6 wave sequence from forward execution roadmap to historical/planning context;
- frame future trajectory as operator capabilities;
- explicitly subordinate further front-door/meta-assurance work to walking-skeleton closure.

## Out of scope

- no runtime or schema changes;
- no `quotes.csv` / `sources.csv` edits;
- no renaming legacy files/columns;
- no candidate migration;
- no Initiate adapter or shared storage;
- no canonical-admission implementation;
- no browser redesign;
- no new ontology;
- no W2 authorization.

## Decisions

1. **Passage is the domain object.** “Quote” remains a legacy representation term.
2. The 324-row religious/philosophical/oral corpus is the **current seed inventory**, not the
   product scope.
3. Garden owns a specialized corpus/product for passages the operator wants to keep and use.
4. Initiate owns the generic lifecycle of arbitrary things worth remembering.
5. Garden keeps native capture; future Initiate integration is optional and must earn its complexity.
6. `canonical` means admitted to the Garden, not verified.
7. SQLite is the authoritative mutable runtime for new work; the deterministic committed export is
   its portable/versioned recovery mirror.
8. `PRODUCT_REALITY.md` owns standing product-state truth; `CURRENT.md` owns execution authority.
9. Future work is prioritized by operator-visible usability boundaries, not the old W2→W6 numbering.
10. Additional assurance machinery is deferred unless a concrete product/dependability failure proves
    it is the constraint.

## Acceptance proof

Cold-read the canonical surface:

`README → PRODUCT_DOCTRINE → PRODUCT_REALITY → CURRENT → AGENTS/RUNBOOK → SYSTEM_MODEL/STATE_MODEL`

A competent reader must be able to state the same product boundary, Garden/Initiate relationship,
authority map, walking skeleton, current constraint and next closure without relying on handoff
archaeology.

Run the existing front-door/program-contract checks. Runtime/data are deliberately unchanged.

## Stop condition

R0 merges, `CURRENT.md` records R0 under **Last reconciliation**, and **U0.3 remains the single
READY unit**. The existing front-door guard structurally defines “last completed unit” as a numbered
U-unit, so U0.2 remains that field until a future product need justifies generalizing the guard.
Do not begin U0.3 inside R0.
