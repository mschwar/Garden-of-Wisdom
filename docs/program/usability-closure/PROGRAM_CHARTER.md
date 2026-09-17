# Usability-Closure Programme Charter

## Objective

Close the distance between Garden's mature artifacts and dependable real-world use.

The product loop being closed is:

`encounter → capture → normalize → curate → admit → Garden-facing read model → browser → rediscover later`

The programme does **not** replace the corpus roadmap. It is a bounded bridge programme over the already-landed W1 substrate.

## Why this exists

Current Garden has two strong but disconnected systems:

1. a dependable read-only Garden browser over the legacy canonical corpus; and
2. a provenance-aware W1 candidate workbench that reaches `accepted → eligible`.

The workbench does not yet reliably bootstrap from persisted state, and an eligible candidate cannot yet reach the Garden-facing browser.

## Gates

### Gate U0 — Resumable workbench

Pass only if a fresh clone can reconstruct the persisted workbench from committed artifacts, perform a real operator mutation, preserve state across restart/reclone, and make mirror freshness mechanically visible.

Required proof:

- no local SQLite exists initially;
- bootstrap reconstructs the committed store state;
- one real operator candidate is captured and curated;
- the committed mirror contains the new state;
- deleting/recreating the SQLite store from the mirror reproduces the same state;
- a stale mirror cannot be silently reported as current;
- front-door docs point to the current programme/READY unit and no longer claim W1 runtime does not exist.

### Gate U1 — Grow the Garden

Pass only if one real newly encountered passage can be:

`captured → normalized → curated/accepted → eligible → explicitly admitted → projected into the Garden read model → found in the real browser`

and the same result can be reproduced after a fresh clone/restart.

No research state may be silently upgraded. `canonical` must not imply `verified`.

## Programme order

Strict:

`U0.1 → U0.2 → U0.3 → [Gate U0 synthesis] → U1.1 → [architecture/operator synthesis] → U1.2 → U1.3 → U1.4 → U1.5 → [Gate U1 synthesis]`

No later unit is implied by completion of the prior unit.

## Execution contract for every unit

One isolated branch/worktree → implement only the unit → run its own acceptance → open one PR → independent/foreign QA from a fresh context → resolve findings → queue discovered work → re-run acceptance → merge → update `docs/queue.md` + `CURRENT.md` + unit handoff → STOP.

## Authority

- Agents may implement deterministic machinery and prepare evidence.
- Operator-authority state transitions remain human gates.
- Any architecture decision that changes the authoritative data relationship is an operator/frontier gate.
- This programme does not authorize W2.

## Preferred architecture hypothesis for U1.1

The programme starts with this **hypothesis, not a pre-decided implementation**:

- keep `quotes.csv` / `sources.csv` as preserved legacy authoritative inputs;
- keep the corpus store authoritative for new candidate/canonical state;
- generate a **deterministic unified Garden read model** from the two;
- point the browser at the derived read model;
- never make a generated projection the write authority.

U1.1 must test this against the repo's actual browser/parser/schema/id/source assumptions and record the decision before implementation.
