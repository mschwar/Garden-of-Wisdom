# Execution Map

| Unit | Newly possible after merge | Primary seam | Stop |
|---|---|---|---|
| U0.1 | Persisted store can be safely bootstrapped/status-checked/synced | SQLite ↔ committed mirror | Stop before docs/front-door |
| U0.2 | Repo front door accurately tells operator/agent what exists and what is next | implementation ↔ project intelligence | Stop before real canary |
| U0.3 | Real operator state survives restart/reclone | tested machinery ↔ ecological use | **GATE U0 — SYNTHESIS** |
| U1.1 | Authoritative admission/read-model architecture is ruled, not guessed | eligible candidate ↔ Garden corpus contract | **ARCHITECTURE SYNTHESIS** |
| U1.2 | Accepted/eligible candidate can be explicitly admitted with minimum Garden metadata | state model ↔ canonical admission | Stop before projection |
| U1.3 | Legacy Garden + new canonical store items produce one deterministic read model | two authorities ↔ one derived view | Stop before browser switch |
| U1.4 | Browser reads the unified model and visibly preserves uncertainty | projection ↔ actual product surface | Stop before persistent gate |
| U1.5 | One real passage survives the whole loop and is rediscoverable after reclone | entire product loop | **GATE U1 — SYNTHESIS** |

## READY rule

At any moment, exactly one unit should be marked `READY` in `CURRENT.md`.

An agent must not infer the next unit from this file alone. It must read:

1. `AGENTS.md`
2. `docs/product/PRODUCT_DOCTRINE.md`
3. `docs/program/usability-closure/CURRENT.md`
4. `docs/queue.md`
5. `docs/DECISIONS.md`
6. the READY work-unit document
7. the most recent relevant handoff

## Discovery rule

Anything discovered outside current unit scope goes to `docs/queue.md` with:

- observed problem;
- why it matters;
- evidence/path;
- proposed owner/lane;
- whether it blocks the current gate.

Do not fix it in passing.
